from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class CineLuxJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if user.status == "SUSPENDED":
            raise AuthenticationFailed("Account suspended", code="account_suspended")
        token_version = validated_token.get("token_version")
        if token_version is not None and token_version != user.token_version:
            raise AuthenticationFailed("Token is no longer valid", code="token_invalidated")
        return user
