from django.urls import path

from .views import MovieDetailView, MovieShowtimesView, MoviesView, RecommendationsView, TrendingMoviesView

urlpatterns = [
    path("movies", MoviesView.as_view(), name="movies"),
    path("movies/trending", TrendingMoviesView.as_view(), name="trending"),
    path("movies/<uuid:movie_id>", MovieDetailView.as_view(), name="movie-detail"),
    path("movies/<uuid:movie_id>/showtimes", MovieShowtimesView.as_view(), name="movie-showtimes"),
    path("recommendations/<uuid:user_id>", RecommendationsView.as_view(), name="recommendations"),
]
