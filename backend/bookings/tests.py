import uuid
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from catalogues.models import Hall, Movie, Seat, Showtime
from users.models import User
from .models import Booking
from .services import BookingService


class TicketValidationTests(TestCase):
    def test_group_qr_scan_marks_every_seat_used(self):
        user = User.objects.create_user(
            email="customer@example.com",
            password="SecurePass2026",
            first_name="Test",
            last_name="Customer",
        )
        validator = User.objects.create_user(
            email="staff@example.com",
            password="SecurePass2026",
            first_name="Gate",
            last_name="Staff",
            role=User.ROLE_STAFF,
            is_staff=True,
        )
        hall = Hall.objects.create(name="Hall A", total_seats=2)
        seat_a = Seat.objects.create(hall=hall, row_label="A", seat_number=1)
        seat_b = Seat.objects.create(hall=hall, row_label="A", seat_number=2)
        movie = Movie.objects.create(title="Coverage", duration_minutes=90)
        start = timezone.now() + timedelta(minutes=10)
        showtime = Showtime.objects.create(
            movie=movie,
            hall=hall,
            start_time=start,
            end_time=start + timedelta(minutes=120),
            price=Decimal("12.00"),
        )
        booking_group_id = uuid.uuid4()
        qr_token = f"QR-{booking_group_id}-test"
        Booking.objects.create(
            booking_group_id=booking_group_id,
            user=user,
            showtime=showtime,
            seat=seat_a,
            status=Booking.CONFIRMED,
            price_paid=showtime.price,
            qr_token=qr_token,
            confirmed_at=timezone.now(),
        )
        Booking.objects.create(
            booking_group_id=booking_group_id,
            user=user,
            showtime=showtime,
            seat=seat_b,
            status=Booking.CONFIRMED,
            price_paid=showtime.price,
            confirmed_at=timezone.now(),
        )

        payload = BookingService.validate_ticket(validator, qr_token)

        self.assertEqual(payload["result"], "VALID")
        self.assertEqual(payload["seats"], ["A1", "A2"])
        self.assertEqual(
            set(Booking.objects.filter(booking_group_id=booking_group_id).values_list("status", flat=True)),
            {Booking.USED},
        )
