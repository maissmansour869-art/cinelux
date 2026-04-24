import json
from datetime import timedelta
from decimal import Decimal
from math import sqrt
from uuid import UUID

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from bookings.models import Booking
from common.exceptions import CineLuxError
from .models import AdminAction, Genre, Hall, Movie, MovieGenre, RecommendationHistory, Seat, Showtime, UserRating


def movie_summary(movie):
    return {
        "movieId": str(movie.movie_id),
        "title": movie.title,
        "description": movie.description,
        "durationMinutes": movie.duration_minutes,
        "releaseDate": movie.release_date,
        "language": movie.language,
        "ageRating": movie.age_rating,
        "posterUrl": movie.poster_url,
        "rating": float(movie.avg_rating),
        "genres": list(movie.genres.order_by("name").values_list("name", flat=True)),
    }


def showtime_payload(st):
    total_seats = getattr(st.hall, "total_seats", 0)
    active_booking_count = getattr(st, "active_booking_count", None)
    available_seats = None if active_booking_count is None else max(total_seats - active_booking_count, 0)
    return {
        "showtimeId": str(st.showtime_id),
        "movieId": str(st.movie_id),
        "hallId": str(st.hall_id),
        "hallName": st.hall.name,
        "startTime": st.start_time,
        "endTime": st.end_time,
        "totalSeats": total_seats,
        "availableSeats": available_seats,
        "price": float(st.price),
        "currency": st.currency,
    }


def audit_payload(data):
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


class CatalogueService:
    @staticmethod
    def _genres_or_error(names):
        names = names or []
        found = {g.name: g for g in Genre.objects.filter(name__in=names)}
        missing = sorted(set(names) - set(found))
        if missing:
            raise CineLuxError("GEN-400", f'Unknown genre: "{missing[0]}"')
        return [found[n] for n in names]

    @staticmethod
    def browse(params):
        qs = Movie.objects.filter(is_active=True).prefetch_related("genres")
        if params.get("q"):
            qs = qs.filter(title__icontains=params["q"])
        if params.get("genre"):
            qs = qs.filter(genres__name=params["genre"])
        if params.get("date"):
            qs = qs.filter(showtimes__start_time__date=params["date"], showtimes__is_active=True).distinct()
        page = max(int(params.get("page", 1)), 1)
        limit = min(max(int(params.get("limit", 20)), 1), 100)
        total = qs.count()
        movies = qs.order_by("title")[(page - 1) * limit: page * limit]
        return {"page": page, "limit": limit, "total": total, "movies": [movie_summary(m) for m in movies]}

    @staticmethod
    def get_movie(movie_id):
        try:
            return movie_summary(Movie.objects.prefetch_related("genres").get(movie_id=movie_id, is_active=True))
        except Movie.DoesNotExist:
            raise CineLuxError("MOV-404", "Movie not found or inactive.")

    @staticmethod
    def get_showtimes(movie_id, params=None):
        if not Movie.objects.filter(movie_id=movie_id, is_active=True).exists():
            raise CineLuxError("MOV-404", "Movie not found or inactive.")
        params = params or {}
        qs = Showtime.objects.filter(movie_id=movie_id, is_active=True, start_time__gt=timezone.now()).select_related("hall")
        if params.get("date"):
            qs = qs.filter(start_time__date=params["date"])
        if params.get("hall"):
            try:
                hall_id = UUID(str(params["hall"]))
            except ValueError:
                raise CineLuxError("GEN-400", "Invalid hall id.")
            qs = qs.filter(hall_id=hall_id)
        qs = qs.annotate(
            active_booking_count=Count(
                "bookings",
                filter=Q(bookings__status__in=[Booking.PENDING, Booking.CONFIRMED, Booking.USED]),
            )
        ).order_by("start_time")
        return {"movieId": str(movie_id), "showtimes": [showtime_payload(st) for st in qs]}

    @staticmethod
    def trending(limit=10):
        qs = Movie.objects.filter(is_active=True).annotate(
            booking_count=Count("showtimes__bookings", filter=Q(showtimes__bookings__status__in=[Booking.CONFIRMED, Booking.USED], showtimes__bookings__booked_at__gt=timezone.now() - timedelta(days=7)))
        ).order_by("-booking_count", "-avg_rating")[:limit]
        return {"movies": [movie_summary(m) for m in qs]}

    @staticmethod
    @transaction.atomic
    def create_movie(data, actor):
        genres = CatalogueService._genres_or_error(data.get("genres", []))
        movie = Movie.objects.create(
            title=data["title"],
            description=data.get("description", ""),
            duration_minutes=data["durationMinutes"],
            release_date=data.get("releaseDate"),
            language=data.get("language", ""),
            age_rating=data.get("ageRating", ""),
            poster_url=data.get("posterUrl", ""),
            metadata=data.get("metadata", {}),
        )
        MovieGenre.objects.bulk_create([MovieGenre(movie=movie, genre=g) for g in genres])
        AdminAction.objects.create(actor_user=actor, action_type="ADD_MOVIE", target_type="MOVIE", target_id=movie.movie_id, payload=audit_payload(data))
        return movie_summary(movie)

    @staticmethod
    @transaction.atomic
    def update_movie(movie_id, data, actor):
        try:
            movie = Movie.objects.get(movie_id=movie_id)
        except Movie.DoesNotExist:
            raise CineLuxError("MOV-404", "Movie not found.")
        mapping = {"durationMinutes": "duration_minutes", "releaseDate": "release_date", "ageRating": "age_rating", "posterUrl": "poster_url"}
        for key in ["title", "description", "language", "metadata"]:
            if key in data:
                setattr(movie, key, data[key])
        for api_key, field in mapping.items():
            if api_key in data:
                setattr(movie, field, data[api_key])
        movie.save()
        if "genres" in data:
            genres = CatalogueService._genres_or_error(data["genres"])
            MovieGenre.objects.filter(movie=movie).delete()
            MovieGenre.objects.bulk_create([MovieGenre(movie=movie, genre=g) for g in genres])
        AdminAction.objects.create(actor_user=actor, action_type="UPDATE_MOVIE", target_type="MOVIE", target_id=movie.movie_id, payload=audit_payload(data))
        return movie_summary(movie)

    @staticmethod
    @transaction.atomic
    def delete_movie(movie_id, actor):
        try:
            movie = Movie.objects.get(movie_id=movie_id)
        except Movie.DoesNotExist:
            raise CineLuxError("MOV-404", "Movie not found.")
        movie.is_active = False
        movie.save(update_fields=["is_active", "updated_at"])
        Showtime.objects.filter(movie=movie, start_time__gt=timezone.now()).update(is_active=False)
        AdminAction.objects.create(actor_user=actor, action_type="DELETE_MOVIE", target_type="MOVIE", target_id=movie.movie_id)
        return {"deleted": True}

    @staticmethod
    @transaction.atomic
    def create_showtime(data, actor):
        try:
            movie = Movie.objects.get(movie_id=data["movieId"], is_active=True)
            hall = Hall.objects.get(hall_id=data["hallId"])
        except Movie.DoesNotExist:
            raise CineLuxError("MOV-404", "Movie not found.")
        except Hall.DoesNotExist:
            raise CineLuxError("GEN-404", "Hall not found.")
        start = data["startTime"]
        end = start + timedelta(minutes=movie.duration_minutes + settings.SHOWTIME_CLEANING_BUFFER_MINUTES)
        if Showtime.objects.filter(hall=hall, is_active=True, start_time__lt=end, end_time__gt=start).exists():
            raise CineLuxError("SHOW-409", "Showtime schedule conflict.")
        st = Showtime.objects.create(movie=movie, hall=hall, start_time=start, end_time=end, price=data["price"], currency=data.get("currency", "USD"))
        AdminAction.objects.create(actor_user=actor, action_type="ADD_SHOWTIME", target_type="SHOWTIME", target_id=st.showtime_id, payload=audit_payload(data))
        return showtime_payload(st)

    @staticmethod
    @transaction.atomic
    def update_showtime(showtime_id, data, actor):
        try:
            st = Showtime.objects.select_related("movie", "hall").get(showtime_id=showtime_id)
        except Showtime.DoesNotExist:
            raise CineLuxError("SHOW-404", "Showtime not found.")
        movie = st.movie
        hall = st.hall
        if "movieId" in data:
            try:
                movie = Movie.objects.get(movie_id=data["movieId"], is_active=True)
            except Movie.DoesNotExist:
                raise CineLuxError("MOV-404", "Movie not found.")
        if "hallId" in data:
            try:
                hall = Hall.objects.get(hall_id=data["hallId"])
            except Hall.DoesNotExist:
                raise CineLuxError("GEN-404", "Hall not found.")
        start = data.get("startTime", st.start_time)
        end = start + timedelta(minutes=movie.duration_minutes + settings.SHOWTIME_CLEANING_BUFFER_MINUTES)
        if Showtime.objects.exclude(showtime_id=st.showtime_id).filter(hall=hall, is_active=True, start_time__lt=end, end_time__gt=start).exists():
            raise CineLuxError("SHOW-409", "Showtime schedule conflict.")
        st.movie = movie
        st.hall = hall
        st.start_time = start
        st.end_time = end
        if "price" in data:
            st.price = data["price"]
        if "currency" in data:
            st.currency = data["currency"]
        st.save()
        AdminAction.objects.create(actor_user=actor, action_type="UPDATE_SHOWTIME", target_type="SHOWTIME", target_id=st.showtime_id, payload=audit_payload(data))
        return showtime_payload(st)

    @staticmethod
    @transaction.atomic
    def delete_showtime(showtime_id, actor):
        try:
            st = Showtime.objects.get(showtime_id=showtime_id)
        except Showtime.DoesNotExist:
            raise CineLuxError("SHOW-404", "Showtime not found.")
        st.is_active = False
        st.save(update_fields=["is_active"])
        AdminAction.objects.create(actor_user=actor, action_type="DELETE_SHOWTIME", target_type="SHOWTIME", target_id=st.showtime_id)
        return {"deleted": True}

    @staticmethod
    @transaction.atomic
    def create_hall(data, actor):
        hall = Hall.objects.create(name=data["name"], total_seats=1)
        AdminAction.objects.create(actor_user=actor, action_type="ADD_HALL", target_type="HALL", target_id=hall.hall_id, payload=audit_payload(data))
        return {"hallId": str(hall.hall_id), "name": hall.name, "totalSeats": hall.total_seats}

    @staticmethod
    def list_halls():
        return {"halls": [{"hallId": str(h.hall_id), "name": h.name, "totalSeats": h.total_seats} for h in Hall.objects.order_by("name")]}

    @staticmethod
    @transaction.atomic
    def update_hall(hall_id, data, actor):
        try:
            hall = Hall.objects.get(hall_id=hall_id)
        except Hall.DoesNotExist:
            raise CineLuxError("GEN-404", "Hall not found.")
        if "name" in data:
            hall.name = data["name"]
        hall.save()
        AdminAction.objects.create(actor_user=actor, action_type="UPDATE_HALL", target_type="HALL", target_id=hall.hall_id, payload=audit_payload(data))
        return {"hallId": str(hall.hall_id), "name": hall.name, "totalSeats": hall.total_seats}

    @staticmethod
    @transaction.atomic
    def create_seat_map(hall_id, rows, actor):
        try:
            hall = Hall.objects.get(hall_id=hall_id)
        except Hall.DoesNotExist:
            raise CineLuxError("GEN-404", "Hall not found.")
        if hall.seats.exists():
            raise CineLuxError("ADM-409", "Seat map already exists for this hall.")
        seats = []
        for row in rows:
            label = row["label"]
            seat_type = row.get("type", Seat.STANDARD)
            for n in range(1, int(row["seatCount"]) + 1):
                seats.append(Seat(hall=hall, row_label=label, seat_number=n, seat_type=seat_type))
        Seat.objects.bulk_create(seats)
        hall.total_seats = len(seats)
        hall.save(update_fields=["total_seats"])
        AdminAction.objects.create(actor_user=actor, action_type="CREATE_SEAT_MAP", target_type="HALL", target_id=hall.hall_id, payload=audit_payload({"rows": rows}))
        return {"hallId": str(hall.hall_id), "totalSeats": hall.total_seats}


class RecommendationService:
    @staticmethod
    def recommend(user, limit=10, genre=None):
        limit = min(max(int(limit), 1), 50)
        pref = list(user.preferred_genres.values_list("name", flat=True))
        booked_genres = list(Genre.objects.filter(movie__showtimes__bookings__user=user, movie__showtimes__bookings__status__in=[Booking.CONFIRMED, Booking.USED]).values_list("name", flat=True))
        scores = {}
        for g in pref + booked_genres:
            scores[g] = scores.get(g, 0) + 1
        booked_movies = Booking.objects.filter(user=user).exclude(status=Booking.CANCELLED).values_list("showtime__movie_id", flat=True)
        candidates = Movie.objects.filter(is_active=True, showtimes__is_active=True, showtimes__start_time__gt=timezone.now()).exclude(movie_id__in=booked_movies).distinct().prefetch_related("genres")
        if genre:
            candidates = candidates.filter(genres__name=genre)
        cold = not booked_genres and not UserRating.objects.filter(user=user).exists()
        rows = []
        for movie in candidates:
            mg = list(movie.genres.values_list("name", flat=True))
            if scores:
                dot = sum(scores.get(g, 0) for g in mg)
                denom = sqrt(sum(v * v for v in scores.values())) * sqrt(max(len(mg), 1))
                relevance = Decimal(str(round(dot / denom if denom else 0, 3)))
            else:
                relevance = None
            rows.append((relevance or Decimal("0"), movie, mg))
        rows.sort(key=lambda item: (item[0], item[1].avg_rating), reverse=True)
        chosen = rows[:limit]
        algorithm = "CBF" if scores else "POPULARITY"
        payload = []
        for relevance, movie, mg in chosen:
            if relevance:
                RecommendationHistory.objects.create(user=user, movie=movie, algorithm=algorithm, relevance_score=relevance)
            payload.append({**movie_summary(movie), "relevanceScore": float(relevance) if relevance else None, "reason": "Based on your interest in " + ", ".join(mg[:2]) if relevance else "Popular this week"})
        return {"userId": str(user.user_id), "algorithm": algorithm, "coldStart": cold, "recommendations": payload}
