from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalogues.models import Genre, Hall, Movie, MovieGenre, Seat, Showtime, UserRating
from users.models import User, UserGenrePreference


GENRES = [
    "Action",
    "Adventure",
    "Animation",
    "Comedy",
    "Drama",
    "Family",
    "Fantasy",
    "History",
    "Horror",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Thriller",
]

MOVIES = [
    {
        "title": "Aurora Protocol",
        "description": "A rescue pilot and a reluctant systems engineer race to stop a failing orbital shield before a solar storm blacks out Earth.",
        "duration_minutes": 124,
        "release_date": date(2026, 3, 6),
        "language": "English",
        "age_rating": "PG-13",
        "poster": "aurora-protocol.png",
        "avg_rating": Decimal("8.40"),
        "rating_count": 245,
        "genres": ["Action", "Adventure", "Sci-Fi", "Thriller"],
        "metadata": {
            "seed_key": "aurora-protocol",
            "cast": ["Mara Venn", "Theo Calder", "Jun Park"],
            "director": "Elena Cross",
            "tags": ["space", "rescue mission", "high stakes"],
        },
    },
    {
        "title": "Midnight at Marigold Station",
        "description": "When the last train disappears from a mountain station, a night clerk follows a trail of impossible clues through the snow.",
        "duration_minutes": 109,
        "release_date": date(2025, 11, 14),
        "language": "English",
        "age_rating": "PG-13",
        "poster": "midnight-at-marigold-station.png",
        "avg_rating": Decimal("8.10"),
        "rating_count": 188,
        "genres": ["Mystery", "Thriller", "Drama"],
        "metadata": {
            "seed_key": "midnight-at-marigold-station",
            "cast": ["Iris Bell", "Nolan Crest", "Asha Rao"],
            "director": "Samira Holt",
            "tags": ["winter", "missing train", "slow burn"],
        },
    },
    {
        "title": "The Laughing Comet",
        "description": "A washed-up children's magician accidentally becomes the spokesperson for a comet cult and has one week to fix the mess.",
        "duration_minutes": 96,
        "release_date": date(2026, 1, 23),
        "language": "English",
        "age_rating": "PG",
        "poster": "the-laughing-comet.png",
        "avg_rating": Decimal("7.60"),
        "rating_count": 132,
        "genres": ["Comedy", "Sci-Fi"],
        "metadata": {
            "seed_key": "the-laughing-comet",
            "cast": ["Miles Finch", "Talia Moon", "Ben Orlo"],
            "director": "Priya Desai",
            "tags": ["absurd", "comet", "redemption"],
        },
    },
    {
        "title": "Harbor of Paper Boats",
        "description": "Three siblings return to their coastal hometown and uncover the letters their mother never mailed.",
        "duration_minutes": 118,
        "release_date": date(2025, 9, 19),
        "language": "English",
        "age_rating": "PG",
        "poster": "harbor-of-paper-boats.png",
        "avg_rating": Decimal("8.70"),
        "rating_count": 301,
        "genres": ["Drama", "Romance"],
        "metadata": {
            "seed_key": "harbor-of-paper-boats",
            "cast": ["Noah Lorne", "Eva Marin", "Celia Fox"],
            "director": "Jonas Vale",
            "tags": ["family", "coastal town", "letters"],
        },
    },
    {
        "title": "Clockwork Orchard",
        "description": "In a valley where mechanical trees grow real fruit, a young inventor must choose between saving the harvest and revealing a family secret.",
        "duration_minutes": 103,
        "release_date": date(2026, 2, 7),
        "language": "English",
        "age_rating": "PG",
        "poster": "clockwork-orchard.png",
        "avg_rating": Decimal("8.00"),
        "rating_count": 164,
        "genres": ["Animation", "Adventure", "Family", "Fantasy"],
        "metadata": {
            "seed_key": "clockwork-orchard",
            "cast": ["Lina Shore", "Marco Teal", "Bea Quinn"],
            "director": "Anika Zhou",
            "tags": ["inventor", "family adventure", "fantasy"],
        },
    },
    {
        "title": "Red Lantern Road",
        "description": "A retired getaway driver takes one final job to protect a neighborhood from a syndicate buying up the city block by block.",
        "duration_minutes": 131,
        "release_date": date(2026, 4, 3),
        "language": "English",
        "age_rating": "R",
        "poster": "red-lantern-road.png",
        "avg_rating": Decimal("8.20"),
        "rating_count": 216,
        "genres": ["Action", "Thriller", "Drama"],
        "metadata": {
            "seed_key": "red-lantern-road",
            "cast": ["Victor Ren", "Mina Cole", "Dante Reyes"],
            "director": "Hugo Sato",
            "tags": ["neo-noir", "car chase", "city"],
        },
    },
    {
        "title": "Letters from the Moon",
        "description": "A linguist on a lunar archive mission discovers love letters that appear to predict her own future.",
        "duration_minutes": 112,
        "release_date": date(2025, 12, 5),
        "language": "English",
        "age_rating": "PG-13",
        "poster": "letters-from-the-moon.png",
        "avg_rating": Decimal("7.90"),
        "rating_count": 175,
        "genres": ["Romance", "Sci-Fi", "Drama"],
        "metadata": {
            "seed_key": "letters-from-the-moon",
            "cast": ["Mae Sterling", "Owen Pike", "Leah Sun"],
            "director": "Nadia Rivers",
            "tags": ["lunar base", "romance", "archive"],
        },
    },
    {
        "title": "The Hollow Carnival",
        "description": "A teen film club documents a travelling carnival that arrives every thirteen years and leaves no footprints behind.",
        "duration_minutes": 101,
        "release_date": date(2025, 10, 24),
        "language": "English",
        "age_rating": "PG-13",
        "poster": "the-hollow-carnival.png",
        "avg_rating": Decimal("7.70"),
        "rating_count": 149,
        "genres": ["Horror", "Mystery", "Fantasy"],
        "metadata": {
            "seed_key": "the-hollow-carnival",
            "cast": ["Rhea Moss", "Finn Lake", "Kit Moreno"],
            "director": "Cass Wilder",
            "tags": ["found footage", "carnival", "supernatural"],
        },
    },
]

HALLS = [
    {"name": "Hall 1", "rows": [(row, 10, Seat.STANDARD) for row in "ABCDEFGHIJ"]},
    {
        "name": "Luxe Hall",
        "rows": [
            ("A", 8, Seat.PREMIUM),
            ("B", 8, Seat.PREMIUM),
            ("C", 10, Seat.STANDARD),
            ("D", 10, Seat.STANDARD),
            ("E", 10, Seat.STANDARD),
            ("F", 10, Seat.STANDARD),
            ("G", 6, Seat.ACCESSIBLE),
        ],
    },
]

SEED_USERS = [
    {
        "email": "maya@cinelux.local",
        "password": "CineLuxUser2026",
        "first_name": "Maya",
        "last_name": "Stone",
        "phone": "+1555010101",
        "genres": ["Drama", "Romance", "Mystery"],
    },
    {
        "email": "leo@cinelux.local",
        "password": "CineLuxUser2026",
        "first_name": "Leo",
        "last_name": "Patel",
        "phone": "+1555010102",
        "genres": ["Action", "Sci-Fi", "Thriller"],
    },
    {
        "email": "staff@cinelux.local",
        "password": "CineLuxStaff2026",
        "first_name": "CineLux",
        "last_name": "Staff",
        "phone": "+1555010199",
        "role": User.ROLE_STAFF,
        "genres": [],
    },
]


class Command(BaseCommand):
    help = "Seed CineLux with reproducible demo catalogue, users, halls, seats, showtimes, and ratings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-date",
            default=getattr(settings, "CINELUX_SEED_START_DATE", "2026-04-24"),
            help="First seeded show date in YYYY-MM-DD format.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        seed_start = datetime.strptime(options["start_date"], "%Y-%m-%d").date()
        genres = self.seed_genres()
        admin = self.seed_admin()
        users = self.seed_users(genres)
        halls = self.seed_halls()
        movies = self.seed_movies(genres)
        self.seed_ratings(users, movies)
        showtime_count = self.seed_showtimes(seed_start, halls, movies)

        self.stdout.write(
            self.style.SUCCESS(
                f"CineLux seed data ready: {len(genres)} genres, {len(movies)} movies, "
                f"{len(halls)} halls, {showtime_count} showtimes, admin {admin.email}."
            )
        )

    def poster_url(self, filename):
        base_url = getattr(settings, "PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
        static_url = settings.STATIC_URL if settings.STATIC_URL.startswith("/") else f"/{settings.STATIC_URL}"
        return f"{base_url}{static_url}catalogues/posters/{filename}"

    def seed_genres(self):
        return {name: Genre.objects.get_or_create(name=name)[0] for name in GENRES}

    def seed_admin(self):
        email = getattr(settings, "CINELUX_ADMIN_EMAIL", None) or "admin@cinelux.local"
        password = getattr(settings, "CINELUX_ADMIN_PASSWORD", None) or "AdminPass2026"
        if not User.objects.filter(email=email).exists():
            return User.objects.create_superuser(email=email, password=password)
        return User.objects.get(email=email)

    def seed_users(self, genres):
        users = []
        for row in SEED_USERS:
            defaults = {
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "phone": row["phone"],
                "role": row.get("role", User.ROLE_USER),
                "is_staff": row.get("role") in {User.ROLE_ADMIN, User.ROLE_STAFF},
            }
            user, created = User.objects.get_or_create(email=row["email"], defaults=defaults)
            if created:
                user.set_password(row["password"])
                user.save(update_fields=["password"])
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(user, field) != value:
                        setattr(user, field, value)
                        changed = True
                if changed:
                    user.save()
            UserGenrePreference.objects.filter(user=user).delete()
            UserGenrePreference.objects.bulk_create(
                [UserGenrePreference(user=user, genre=genres[name]) for name in row["genres"]],
                ignore_conflicts=True,
            )
            users.append(user)
        return users

    def seed_halls(self):
        halls = {}
        for hall_spec in HALLS:
            seat_total = sum(count for _, count, _ in hall_spec["rows"])
            hall, _ = Hall.objects.update_or_create(
                name=hall_spec["name"],
                defaults={"total_seats": seat_total},
            )
            hall.seats.all().delete()
            seats = []
            for label, count, seat_type in hall_spec["rows"]:
                for number in range(1, count + 1):
                    seats.append(Seat(hall=hall, row_label=label, seat_number=number, seat_type=seat_type))
            Seat.objects.bulk_create(seats, ignore_conflicts=True)
            halls[hall.name] = hall
        return halls

    def seed_movies(self, genres):
        movies = {}
        for row in MOVIES:
            movie, _ = Movie.objects.update_or_create(
                title=row["title"],
                defaults={
                    "description": row["description"],
                    "duration_minutes": row["duration_minutes"],
                    "release_date": row["release_date"],
                    "language": row["language"],
                    "age_rating": row["age_rating"],
                    "poster_url": self.poster_url(row["poster"]),
                    "avg_rating": row["avg_rating"],
                    "rating_count": row["rating_count"],
                    "metadata": row["metadata"],
                    "is_active": True,
                },
            )
            MovieGenre.objects.filter(movie=movie).delete()
            MovieGenre.objects.bulk_create([MovieGenre(movie=movie, genre=genres[name]) for name in row["genres"]])
            movies[row["title"]] = movie
        return movies

    def seed_ratings(self, users, movies):
        rating_matrix = {
            "maya@cinelux.local": {
                "Harbor of Paper Boats": 9,
                "Midnight at Marigold Station": 8,
                "Letters from the Moon": 8,
            },
            "leo@cinelux.local": {
                "Aurora Protocol": 9,
                "Red Lantern Road": 8,
                "The Laughing Comet": 7,
            },
        }
        users_by_email = {user.email: user for user in users}
        for email, scores in rating_matrix.items():
            user = users_by_email.get(email)
            if not user:
                continue
            for title, score in scores.items():
                UserRating.objects.update_or_create(user=user, movie=movies[title], defaults={"score": score})

    def seed_showtimes(self, seed_start, halls, movies):
        seeded_movies = list(movies.values())
        Showtime.objects.filter(movie__in=seeded_movies).delete()

        schedule = [
            ("Hall 1", "Aurora Protocol", 0, time(13, 0), "14.50"),
            ("Hall 1", "Midnight at Marigold Station", 0, time(16, 0), "13.00"),
            ("Hall 1", "The Laughing Comet", 0, time(19, 0), "12.00"),
            ("Hall 1", "Red Lantern Road", 0, time(21, 30), "15.00"),
            ("Luxe Hall", "Clockwork Orchard", 0, time(12, 30), "18.00"),
            ("Luxe Hall", "Harbor of Paper Boats", 0, time(15, 15), "18.00"),
            ("Luxe Hall", "Letters from the Moon", 0, time(18, 15), "18.50"),
            ("Luxe Hall", "The Hollow Carnival", 0, time(21, 0), "19.00"),
            ("Hall 1", "Clockwork Orchard", 1, time(11, 30), "12.00"),
            ("Hall 1", "Aurora Protocol", 1, time(14, 15), "14.50"),
            ("Hall 1", "Harbor of Paper Boats", 1, time(17, 30), "13.50"),
            ("Hall 1", "The Hollow Carnival", 1, time(20, 45), "13.00"),
            ("Luxe Hall", "The Laughing Comet", 1, time(12, 0), "17.00"),
            ("Luxe Hall", "Midnight at Marigold Station", 1, time(14, 45), "18.50"),
            ("Luxe Hall", "Red Lantern Road", 1, time(17, 45), "19.50"),
            ("Luxe Hall", "Letters from the Moon", 1, time(21, 15), "18.50"),
            ("Hall 1", "Letters from the Moon", 2, time(12, 45), "12.50"),
            ("Hall 1", "Red Lantern Road", 2, time(15, 45), "14.00"),
            ("Hall 1", "Clockwork Orchard", 2, time(19, 15), "12.00"),
            ("Hall 1", "Aurora Protocol", 2, time(21, 45), "14.50"),
            ("Luxe Hall", "Harbor of Paper Boats", 2, time(13, 0), "18.00"),
            ("Luxe Hall", "The Hollow Carnival", 2, time(16, 0), "19.00"),
            ("Luxe Hall", "Midnight at Marigold Station", 2, time(18, 45), "18.50"),
            ("Luxe Hall", "The Laughing Comet", 2, time(21, 30), "17.00"),
        ]

        showtimes = []
        for hall_name, title, day_offset, show_time, price in schedule:
            movie = movies[title]
            start = timezone.make_aware(datetime.combine(seed_start + timedelta(days=day_offset), show_time))
            end = start + timedelta(minutes=movie.duration_minutes + settings.SHOWTIME_CLEANING_BUFFER_MINUTES)
            showtimes.append(
                Showtime(
                    movie=movie,
                    hall=halls[hall_name],
                    start_time=start,
                    end_time=end,
                    price=Decimal(price),
                    currency="USD",
                    is_active=True,
                )
            )
        Showtime.objects.bulk_create(showtimes)
        return len(showtimes)
