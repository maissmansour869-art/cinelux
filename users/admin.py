from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import SavedPaymentMethod, User, UserGenrePreference


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ("email", "first_name", "last_name", "role", "status", "created_at")
    list_filter = ("role", "status", "is_staff")
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("first_name", "last_name", "phone", "role", "status", "token_version")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "last_login_at", "created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at", "last_login_at")
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "password1", "password2", "role", "status")}),)


admin.site.register(UserGenrePreference)
admin.site.register(SavedPaymentMethod)
