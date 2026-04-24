import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("first_name", "CineLux")
        extra_fields.setdefault("last_name", "Admin")
        extra_fields.setdefault("role", "ADMIN")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_USER = "USER"
    ROLE_ADMIN = "ADMIN"
    ROLE_STAFF = "STAFF"
    STATUS_ACTIVE = "ACTIVE"
    STATUS_SUSPENDED = "SUSPENDED"

    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=20, choices=[(ROLE_USER, ROLE_USER), (ROLE_ADMIN, ROLE_ADMIN), (ROLE_STAFF, ROLE_STAFF)], default=ROLE_USER)
    status = models.CharField(max_length=20, choices=[(STATUS_ACTIVE, STATUS_ACTIVE), (STATUS_SUSPENDED, STATUS_SUSPENDED)], default=STATUS_ACTIVE)
    token_version = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    preferred_genres = models.ManyToManyField("catalogues.Genre", through="UserGenrePreference", blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        db_table = "users"
        indexes = [models.Index(fields=["email"]), models.Index(fields=["role"])]

    @property
    def id(self):
        return self.user_id

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.email


class UserGenrePreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    genre = models.ForeignKey("catalogues.Genre", on_delete=models.CASCADE)

    class Meta:
        db_table = "user_genre_preferences"
        constraints = [models.UniqueConstraint(fields=["user", "genre"], name="uniq_user_genre_preference")]


class SavedPaymentMethod(models.Model):
    method_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payment_methods")
    gateway_customer_id = models.CharField(max_length=128)
    gateway_token = models.CharField(max_length=128)
    brand = models.CharField(max_length=20, blank=True)
    last4 = models.CharField(max_length=4)
    exp_month = models.PositiveIntegerField(null=True, blank=True)
    exp_year = models.PositiveIntegerField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "saved_payment_methods"
        indexes = [models.Index(fields=["user"])]
