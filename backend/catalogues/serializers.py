from rest_framework import serializers


class MovieWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    durationMinutes = serializers.IntegerField(min_value=1)
    releaseDate = serializers.DateField(required=False, allow_null=True)
    language = serializers.CharField(max_length=40, required=False, allow_blank=True)
    ageRating = serializers.CharField(max_length=10, required=False, allow_blank=True)
    posterUrl = serializers.URLField(required=False, allow_blank=True)
    genres = serializers.ListField(child=serializers.CharField(), required=False)
    metadata = serializers.DictField(required=False)


class ShowtimeWriteSerializer(serializers.Serializer):
    movieId = serializers.UUIDField()
    hallId = serializers.UUIDField()
    startTime = serializers.DateTimeField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    currency = serializers.CharField(max_length=3, required=False, default="USD")


class HallWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=60)


class SeatMapSerializer(serializers.Serializer):
    rows = serializers.ListField(child=serializers.DictField())
