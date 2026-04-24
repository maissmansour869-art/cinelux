from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from catalogues.models import Genre
from common.exceptions import CineLuxError
from .models import SavedPaymentMethod, User, UserGenrePreference


def serialize_user(user):
    genres = list(user.preferred_genres.order_by("name").values_list("name", flat=True))
    return {
        "userId": str(user.user_id),
        "firstName": user.first_name,
        "lastName": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "status": user.status,
        "preferredGenres": genres,
        "createdAt": user.created_at,
        "updatedAt": user.updated_at,
    }


class UserService:
    @staticmethod
    def _resolve_genres(names):
        names = names or []
        found = {g.name: g for g in Genre.objects.filter(name__in=names)}
        missing = sorted(set(names) - set(found))
        if missing:
            raise CineLuxError("GEN-400", f'Unknown genre: "{missing[0]}"')
        return [found[name] for name in names]

    @staticmethod
    @transaction.atomic
    def register(data, *, role="USER"):
        email = data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise CineLuxError("AUTH-002", "Email address already registered.")
        genres = UserService._resolve_genres(data.get("preferredGenres", []))
        user = User.objects.create_user(
            email=email,
            password=data["password"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            phone=data.get("phone", ""),
            role=role,
            is_staff=role in {"ADMIN", "STAFF"},
        )
        UserGenrePreference.objects.bulk_create([UserGenrePreference(user=user, genre=g) for g in genres])
        return serialize_user(user)

    @staticmethod
    def login(email, password):
        user = authenticate(username=email.lower(), password=password)
        if not user:
            raise CineLuxError("AUTH-001", "Invalid credentials.")
        if user.status == "SUSPENDED":
            raise CineLuxError("AUTH-003", "Account suspended.")
        user.last_login_at = timezone.now()
        user.save(update_fields=["last_login_at"])
        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        refresh["token_version"] = user.token_version
        return {"token": str(refresh.access_token), "refreshToken": str(refresh), "expiresIn": 3600, "userId": str(user.user_id)}

    @staticmethod
    def get_user(user_id):
        try:
            return serialize_user(User.objects.get(user_id=user_id))
        except User.DoesNotExist:
            raise CineLuxError("GEN-404", "User not found.")

    @staticmethod
    @transaction.atomic
    def update_user(user_id, data):
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise CineLuxError("GEN-404", "User not found.")
        if "email" in data and User.objects.exclude(user_id=user.user_id).filter(email=data["email"].lower()).exists():
            raise CineLuxError("AUTH-002", "Email address already registered.")
        for api_key, field in {"firstName": "first_name", "lastName": "last_name", "phone": "phone"}.items():
            if api_key in data:
                setattr(user, field, data[api_key])
        if "email" in data:
            user.email = data["email"].lower()
        if "password" in data:
            if not data.get("currentPassword") or not user.check_password(data["currentPassword"]):
                raise CineLuxError("AUTH-001", "Invalid credentials.")
            user.set_password(data["password"])
            user.token_version += 1
        user.save()
        return serialize_user(user)

    @staticmethod
    @transaction.atomic
    def update_preferences(user_id, genre_names):
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise CineLuxError("GEN-404", "User not found.")
        genres = UserService._resolve_genres(genre_names)
        UserGenrePreference.objects.filter(user=user).delete()
        UserGenrePreference.objects.bulk_create([UserGenrePreference(user=user, genre=g) for g in genres])
        return serialize_user(user)

    @staticmethod
    def list_payment_methods(user_id):
        return [
            {
                "methodId": str(pm.method_id),
                "brand": pm.brand,
                "last4": pm.last4,
                "expMonth": pm.exp_month,
                "expYear": pm.exp_year,
                "isDefault": pm.is_default,
            }
            for pm in SavedPaymentMethod.objects.filter(user_id=user_id).order_by("-is_default", "-created_at")
        ]

    @staticmethod
    @transaction.atomic
    def add_payment_method(user_id, data):
        if data.get("isDefault"):
            SavedPaymentMethod.objects.filter(user_id=user_id).update(is_default=False)
        pm = SavedPaymentMethod.objects.create(
            user_id=user_id,
            gateway_customer_id=data["gatewayCustomerId"],
            gateway_token=data["gatewayToken"],
            brand=data.get("brand", ""),
            last4=data["last4"],
            exp_month=data.get("expMonth"),
            exp_year=data.get("expYear"),
            is_default=data.get("isDefault", False),
        )
        return {"methodId": str(pm.method_id), "brand": pm.brand, "last4": pm.last4, "expMonth": pm.exp_month, "expYear": pm.exp_year, "isDefault": pm.is_default}

    @staticmethod
    def delete_payment_method(user_id, method_id):
        deleted, _ = SavedPaymentMethod.objects.filter(user_id=user_id, method_id=method_id).delete()
        if not deleted:
            raise CineLuxError("GEN-404", "Payment method not found.")
        return {"deleted": True}

    @staticmethod
    @transaction.atomic
    def admin_patch_user(user_id, data, actor):
        from catalogues.models import AdminAction

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise CineLuxError("GEN-404", "User not found.")
        if "role" in data:
            if user.role == "ADMIN" and data["role"] != "ADMIN" and not User.objects.exclude(user_id=user.user_id).filter(role="ADMIN", status="ACTIVE").exists():
                raise CineLuxError("ADM-409", "Cannot demote the last active admin.")
            user.role = data["role"]
            user.is_staff = user.role in {"ADMIN", "STAFF"}
            user.token_version += 1
        if "status" in data:
            user.status = data["status"]
            user.token_version += 1
        user.save()
        AdminAction.objects.create(actor_user=actor, action_type="PATCH_USER", target_type="USER", target_id=user.user_id, payload=data)
        return serialize_user(user)
