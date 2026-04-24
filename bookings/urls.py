from django.urls import path

from .views import BookingDetailView, BookingsView, ConfirmBookingView, HoldBookingView, ShowtimeSeatsView, ValidateTicketView

urlpatterns = [
    path("showtimes/<uuid:showtime_id>/seats", ShowtimeSeatsView.as_view(), name="showtime-seats"),
    path("bookings/hold", HoldBookingView.as_view(), name="booking-hold"),
    path("bookings/confirm", ConfirmBookingView.as_view(), name="booking-confirm"),
    path("bookings", BookingsView.as_view(), name="bookings"),
    path("bookings/<uuid:booking_id>", BookingDetailView.as_view(), name="booking-detail"),
    path("validate", ValidateTicketView.as_view(), name="validate-ticket"),
]
