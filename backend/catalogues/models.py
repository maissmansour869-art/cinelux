import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Genre(models.Model):
    genre_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        db_table = "genres"

    def __str__(self):
        return self.name


class Movie(models.Model):
    movie_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField()
    release_date = models.DateField(null=True, blank=True)
    language = models.CharField(max_length=40, blank=True)
    age_rating = models.CharField(max_length=10, blank=True)
    poster_url = models.URLField(max_length=500, blank=True)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    genres = models.ManyToManyField(Genre, through="MovieGenre", blank=True)

    class Meta:
        db_table = "movies"
        indexes = [models.Index(fields=["is_active"])]

    def __str__(self):
        return self.title


class MovieGenre(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    class Meta:
        db_table = "movie_genres"
        constraints = [models.UniqueConstraint(fields=["movie", "genre"], name="uniq_movie_genre")]


class Hall(models.Model):
    hall_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=60, unique=True)
    total_seats = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "halls"

    def __str__(self):
        return self.name


class Seat(models.Model):
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"
    ACCESSIBLE = "ACCESSIBLE"

    seat_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name="seats")
    row_label = models.CharField(max_length=3)
    seat_number = models.PositiveIntegerField()
    seat_type = models.CharField(max_length=20, choices=[(STANDARD, STANDARD), (PREMIUM, PREMIUM), (ACCESSIBLE, ACCESSIBLE)], default=STANDARD)

    class Meta:
        db_table = "seats"
        constraints = [models.UniqueConstraint(fields=["hall", "row_label", "seat_number"], name="uniq_hall_seat")]
        indexes = [models.Index(fields=["hall"])]

    @property
    def label(self):
        return f"{self.row_label}{self.seat_number}"


class Showtime(models.Model):
    showtime_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movie = models.ForeignKey(Movie, on_delete=models.RESTRICT, related_name="showtimes")
    hall = models.ForeignKey(Hall, on_delete=models.RESTRICT, related_name="showtimes")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "showtimes"
        indexes = [models.Index(fields=["movie", "start_time"]), models.Index(fields=["hall", "start_time"])]
        constraints = [models.CheckConstraint(condition=Q(end_time__gt=models.F("start_time")), name="showtime_end_after_start")]


class UserRating(models.Model):
    rating_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="ratings")
    score = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_ratings"
        constraints = [
            models.UniqueConstraint(fields=["user", "movie"], name="uniq_user_movie_rating"),
            models.CheckConstraint(condition=Q(score__gte=1, score__lte=10), name="rating_score_1_10"),
        ]


class RecommendationHistory(models.Model):
    rec_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    algorithm = models.CharField(max_length=20)
    relevance_score = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendation_history"


class AdminAction(models.Model):
    action_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=40)
    target_type = models.CharField(max_length=40, blank=True)
    target_id = models.UUIDField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "admin_actions"
