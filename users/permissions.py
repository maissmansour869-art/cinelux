from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user_id = view.kwargs.get("user_id") or view.kwargs.get("userId")
        return bool(request.user and request.user.is_authenticated and (request.user.role == "ADMIN" or str(request.user.user_id) == str(user_id)))


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "ADMIN")


class IsStaffOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in {"STAFF", "ADMIN"})
