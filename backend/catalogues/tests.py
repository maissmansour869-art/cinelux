from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking
from users.models import User
from .models import Hall, Movie, Seat, Showtime
from .services import CatalogueService


@override_settings(ALLOWED_HOSTS=["testserver"])
class ShowtimeCoverageTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="SecurePass2026",
            first_name="Admin",
            last_name="User",
            role=User.ROLE_ADMIN,
            is_staff=True,
        )
        self.customer = User.objects.create_user(
            email="customer@example.com",
            password="SecurePass2026",
            first_name="Test",
            last_name="Customer",
        )
        self.movie = Movie.objects.create(title="Traceability", duration_minutes=100)
        self.hall = Hall.objects.create(name="Hall A", total_seats=3)
        self.other_hall = Hall.objects.create(name="Hall B", total_seats=2)
        self.seat_a = Seat.objects.create(hall=self.hall, row_label="A", seat_number=1)
        Seat.objects.create(hall=self.hall, row_label="A", seat_number=2)
        Seat.objects.create(hall=self.hall, row_label="A", seat_number=3)
        Seat.objects.create(hall=self.other_hall, row_label="A", seat_number=1)
        Seat.objects.create(hall=self.other_hall, row_label="A", seat_number=2)
        self.start = timezone.now() + timedelta(days=2)
        self.showtime = Showtime.objects.create(
            movie=self.movie,
            hall=self.hall,
            start_time=self.start,
            end_time=self.start + timedelta(minutes=130),
            price=Decimal("12.00"),
        )

    def test_movie_showtimes_include_availability_and_filters(self):
        Booking.objects.create(
            user=self.customer,
            showtime=self.showtime,
            seat=self.seat_a,
            status=Booking.CONFIRMED,
            price_paid=self.showtime.price,
        )

        payload = CatalogueService.get_showtimes(
            self.movie.movie_id,
            {"date": self.start.date().isoformat(), "hall": str(self.hall.hall_id)},
        )

        self.assertEqual(len(payload["showtimes"]), 1)
        showtime = payload["showtimes"][0]
        self.assertEqual(showtime["totalSeats"], 3)
        self.assertEqual(showtime["availableSeats"], 2)

    def test_admin_can_update_and_delete_showtime_and_update_hall(self):
        client = APIClient()
        client.force_authenticate(user=self.admin)
        new_start = self.start + timedelta(hours=4)

        showtime_response = client.put(
            reverse("admin-showtime-detail", kwargs={"showtime_id": self.showtime.showtime_id}),
            {
                "hallId": str(self.other_hall.hall_id),
                "startTime": new_start.isoformat(),
                "price": "14.50",
            },
            format="json",
        )
        self.assertEqual(showtime_response.status_code, 200)
        self.showtime.refresh_from_db()
        self.assertEqual(self.showtime.hall_id, self.other_hall.hall_id)
        self.assertEqual(self.showtime.price, Decimal("14.50"))

        hall_response = client.put(
            reverse("admin-hall-detail", kwargs={"hall_id": self.other_hall.hall_id}),
            {"name": "Hall Prime"},
            format="json",
        )
        self.assertEqual(hall_response.status_code, 200)
        self.other_hall.refresh_from_db()
        self.assertEqual(self.other_hall.name, "Hall Prime")

        delete_response = client.delete(reverse("admin-showtime-detail", kwargs={"showtime_id": self.showtime.showtime_id}))
        self.assertEqual(delete_response.status_code, 200)
        self.showtime.refresh_from_db()
        self.assertFalse(self.showtime.is_active)
