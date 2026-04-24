from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=100)
    lastName = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    preferredGenres = serializers.ListField(child=serializers.CharField(), required=False)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserUpdateSerializer(serializers.Serializer):
    firstName = serializers.CharField(max_length=100, required=False)
    lastName = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    password = serializers.CharField(min_length=8, required=False, write_only=True)
    currentPassword = serializers.CharField(required=False, write_only=True)


class PreferencesSerializer(serializers.Serializer):
    preferredGenres = serializers.ListField(child=serializers.CharField())


class PaymentMethodSerializer(serializers.Serializer):
    gatewayCustomerId = serializers.CharField(max_length=128)
    gatewayToken = serializers.CharField(max_length=128)
    brand = serializers.CharField(max_length=20, required=False, allow_blank=True)
    last4 = serializers.RegexField(r"^\d{4}$")
    expMonth = serializers.IntegerField(required=False, min_value=1, max_value=12)
    expYear = serializers.IntegerField(required=False, min_value=2020)
    isDefault = serializers.BooleanField(required=False)
