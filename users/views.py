from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import error_response
from .models import User
from .permissions import IsAdmin, IsOwnerOrAdmin
from .serializers import LoginSerializer, PaymentMethodSerializer, PreferencesSerializer, RegisterSerializer, UserUpdateSerializer
from .services import UserService, serialize_user


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(UserService.register(serializer.validated_data), status=201)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(UserService.login(serializer.validated_data["email"], serializer.validated_data["password"]))


class UserProfileView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def get(self, request, user_id):
        return Response(UserService.get_user(user_id))

    def put(self, request, user_id):
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(UserService.update_user(user_id, serializer.validated_data))


class UpdatePreferencesView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def put(self, request, user_id):
        serializer = PreferencesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(UserService.update_preferences(user_id, serializer.validated_data["preferredGenres"]))


class PaymentMethodsView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def get(self, request, user_id):
        return Response({"paymentMethods": UserService.list_payment_methods(user_id)})

    def post(self, request, user_id):
        serializer = PaymentMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(UserService.add_payment_method(user_id, serializer.validated_data), status=201)


class PaymentMethodDetailView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def delete(self, request, user_id, method_id):
        return Response(UserService.delete_payment_method(user_id, method_id))


class AdminUsersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        qs = User.objects.all().order_by("-created_at")
        if request.query_params.get("role"):
            qs = qs.filter(role=request.query_params["role"])
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        return Response({"users": [serialize_user(u) for u in qs[:100]]})

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = request.data.get("role", "USER")
        if role not in {"USER", "ADMIN", "STAFF"}:
            return error_response("GEN-400", "Invalid role.", request=request)
        return Response(UserService.register(serializer.validated_data, role=role), status=201)


class AdminUserDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, user_id):
        return Response(UserService.get_user(user_id))

    def patch(self, request, user_id):
        return Response(UserService.admin_patch_user(user_id, request.data, request.user))
