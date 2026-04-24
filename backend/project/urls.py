from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from catalogues.views import (
    AdminHallDetailView,
    AdminHallSeatsView,
    AdminHallsView,
    AdminMovieDetailView,
    AdminMoviesView,
    AdminShowtimeDetailView,
    AdminShowtimesView,
)
from users.views import AdminUserDetailView, AdminUsersView

urlpatterns = [
    path("", TemplateView.as_view(template_name="frontend/index.html"), name="frontend"),
    path("admin/", admin.site.urls),
    path("api/", include("catalogues.urls")),
    path("api/users/", include("users.urls")),
    path("api/", include("bookings.urls")),
    path("api/admin/movies", AdminMoviesView.as_view(), name="admin-movies"),
    path("api/admin/movies/<uuid:movie_id>", AdminMovieDetailView.as_view(), name="admin-movie-detail"),
    path("api/admin/showtimes", AdminShowtimesView.as_view(), name="admin-showtimes"),
    path("api/admin/showtimes/<uuid:showtime_id>", AdminShowtimeDetailView.as_view(), name="admin-showtime-detail"),
    path("api/admin/halls", AdminHallsView.as_view(), name="admin-halls"),
    path("api/admin/halls/<uuid:hall_id>", AdminHallDetailView.as_view(), name="admin-hall-detail"),
    path("api/admin/halls/<uuid:hall_id>/seats", AdminHallSeatsView.as_view(), name="admin-hall-seats"),
    path("api/admin/users", AdminUsersView.as_view(), name="admin-users"),
    path("api/admin/users/<uuid:user_id>", AdminUserDetailView.as_view(), name="admin-user-detail"),
]
