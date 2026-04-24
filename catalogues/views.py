from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin, IsOwnerOrAdmin
from users.models import User
from common.exceptions import CineLuxError
from .serializers import HallWriteSerializer, MovieWriteSerializer, SeatMapSerializer, ShowtimeWriteSerializer
from .services import CatalogueService, RecommendationService


class MoviesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(CatalogueService.browse(request.query_params))


class TrendingMoviesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(CatalogueService.trending(int(request.query_params.get("limit", 10))))


class MovieDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, movie_id):
        return Response(CatalogueService.get_movie(movie_id))


class MovieShowtimesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, movie_id):
        return Response(CatalogueService.get_showtimes(movie_id, request.query_params))


class RecommendationsView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def get(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise CineLuxError("GEN-404", "User not found.")
        return Response(RecommendationService.recommend(user, request.query_params.get("limit", 10), request.query_params.get("genre")))


class AdminMoviesView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = MovieWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(CatalogueService.create_movie(serializer.validated_data, request.user), status=201)


class AdminMovieDetailView(APIView):
    permission_classes = [IsAdmin]

    def put(self, request, movie_id):
        serializer = MovieWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(CatalogueService.update_movie(movie_id, serializer.validated_data, request.user))

    def delete(self, request, movie_id):
        return Response(CatalogueService.delete_movie(movie_id, request.user))


class AdminShowtimesView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = ShowtimeWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(CatalogueService.create_showtime(serializer.validated_data, request.user), status=201)


class AdminShowtimeDetailView(APIView):
    permission_classes = [IsAdmin]

    def put(self, request, showtime_id):
        serializer = ShowtimeWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(CatalogueService.update_showtime(showtime_id, serializer.validated_data, request.user))

    def delete(self, request, showtime_id):
        return Response(CatalogueService.delete_showtime(showtime_id, request.user))


class AdminHallsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(CatalogueService.list_halls())

    def post(self, request):
        serializer = HallWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(CatalogueService.create_hall(serializer.validated_data, request.user), status=201)


class AdminHallDetailView(APIView):
    permission_classes = [IsAdmin]

    def put(self, request, hall_id):
        serializer = HallWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(CatalogueService.update_hall(hall_id, serializer.validated_data, request.user))


class AdminHallSeatsView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, hall_id):
        serializer = SeatMapSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(CatalogueService.create_seat_map(hall_id, serializer.validated_data["rows"], request.user), status=201)
