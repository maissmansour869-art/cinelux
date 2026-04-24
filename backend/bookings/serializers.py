from rest_framework import serializers


class HoldSerializer(serializers.Serializer):
    userId = serializers.UUIDField(required=False)
    showtimeId = serializers.UUIDField()
    seatIds = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)


class ConfirmSerializer(serializers.Serializer):
    bookingGroupId = serializers.UUIDField()
    paymentMethod = serializers.DictField()


class ValidateTicketSerializer(serializers.Serializer):
    qrToken = serializers.CharField(max_length=128)
