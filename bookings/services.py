import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from catalogues.models import Seat, Showtime
from common.exceptions import CineLuxError
from externals.notification_service import NotificationService
from externals.payment_gateway import PaymentGateway
from .models import Booking, EntryLog, Notification, PendingRefund


def booking_group_payload(bookings, *, status_code=200):
    first = bookings[0]
    seats = [b.seat.label for b in bookings]
    return {
        "bookingGroupId": str(first.booking_group_id),
        "userId": str(first.user_id),
        "showtimeId": str(first.showtime_id),
        "movieTitle": first.showtime.movie.title,
        "seats": seats,
        "status": first.status,
        "totalAmount": float(sum(b.price_paid for b in bookings)),
        "currency": first.showtime.currency,
        "paymentToken": first.payment_token,
        "qrCodeToken": first.qr_token,
        "qrCodeUrl": f"{settings.PUBLIC_BASE_URL}/qr/{first.qr_token}.png" if first.qr_token else None,
        "confirmedAt": first.confirmed_at,
    }


class BookingService:
    @staticmethod
    def seat_map(showtime_id):
        try:
            st = Showtime.objects.select_related("hall").get(showtime_id=showtime_id, is_active=True)
        except Showtime.DoesNotExist:
            raise CineLuxError("SHOW-404", "Showtime not found.")
        active = {
            b.seat_id: b
            for b in Booking.objects.filter(showtime=st, status__in=[Booking.PENDING, Booking.CONFIRMED, Booking.USED])
        }
        seats = []
        now = timezone.now()
        for seat in st.hall.seats.order_by("row_label", "seat_number"):
            booking = active.get(seat.seat_id)
            if not booking:
                status = "AVAILABLE"
            elif booking.status == Booking.PENDING and booking.hold_expires_at and booking.hold_expires_at > now:
                status = "HELD"
            elif booking.status in {Booking.CONFIRMED, Booking.USED}:
                status = "BOOKED"
            else:
                status = "AVAILABLE"
            seats.append({"seatId": str(seat.seat_id), "row": seat.row_label, "number": seat.seat_number, "type": seat.seat_type, "status": status})
        return {"showtimeId": str(st.showtime_id), "hallId": str(st.hall_id), "hallName": st.hall.name, "price": float(st.price), "currency": st.currency, "seats": seats}

    @staticmethod
    @transaction.atomic
    def hold_seats(user, showtime_id, seat_ids):
        try:
            st = Showtime.objects.select_for_update().select_related("hall").get(showtime_id=showtime_id, is_active=True)
        except Showtime.DoesNotExist:
            raise CineLuxError("SHOW-404", "Showtime not found.")
        if st.start_time <= timezone.now():
            raise CineLuxError("BOOK-422", "Showtime already started.")
        seats = list(Seat.objects.filter(hall=st.hall, seat_id__in=seat_ids))
        if len(seats) != len(set(seat_ids)):
            raise CineLuxError("SEAT-404", "Seat not found.")
        now = timezone.now()
        existing = list(Booking.objects.select_for_update().filter(showtime=st, seat_id__in=seat_ids, status__in=[Booking.PENDING, Booking.CONFIRMED, Booking.USED]))
        active = [b for b in existing if b.status != Booking.PENDING or (b.hold_expires_at and b.hold_expires_at > now)]
        expired = [b for b in existing if b.status == Booking.PENDING and (not b.hold_expires_at or b.hold_expires_at <= now)]
        if active:
            raise CineLuxError("SEAT-409", "Seat already booked or held.", details=[str(b.seat_id) for b in active])
        for b in expired:
            b.status = Booking.EXPIRED
            b.save(update_fields=["status"])
        group_id = uuid.uuid4()
        expires = now + timedelta(minutes=settings.BOOKING_HOLD_MINUTES)
        Booking.objects.bulk_create([Booking(booking_group_id=group_id, user=user, showtime=st, seat=seat, status=Booking.PENDING, price_paid=st.price, hold_expires_at=expires) for seat in seats])
        return {"bookingGroupId": str(group_id), "showtimeId": str(st.showtime_id), "seats": [str(s.seat_id) for s in seats], "status": "PENDING", "holdExpiresAt": expires, "totalAmount": float(st.price * len(seats)), "currency": st.currency}

    @staticmethod
    @transaction.atomic
    def confirm(user, booking_group_id, payment_method):
        bookings = list(Booking.objects.select_for_update().select_related("showtime__movie", "seat", "user").filter(booking_group_id=booking_group_id).order_by("seat__row_label", "seat__seat_number"))
        if not bookings:
            raise CineLuxError("BOOK-404", "Booking not found.")
        if bookings[0].user_id != user.user_id and user.role != "ADMIN":
            raise CineLuxError("GEN-403", "Not authorised.")
        if all(b.status == Booking.CONFIRMED for b in bookings):
            return booking_group_payload(bookings)
        now = timezone.now()
        if any(b.status != Booking.PENDING or not b.hold_expires_at or b.hold_expires_at <= now for b in bookings):
            raise CineLuxError("BOOK-410", "Seat hold expired.")
        total = sum((b.price_paid for b in bookings), Decimal("0.00"))
        token = payment_method.get("token", "")
        result = PaymentGateway().charge(token=token, amount=total, currency=bookings[0].showtime.currency, idempotency_key=str(booking_group_id))
        if result.status == "DECLINED":
            raise CineLuxError("PAY-402", "Payment declined.", details=result.decline_reason)
        if result.status != "SUCCESS":
            raise CineLuxError("PAY-503", "Payment gateway unavailable.")
        qr_token = f"QR-{booking_group_id}-{uuid.uuid4().hex[:8]}"
        for index, b in enumerate(bookings):
            b.status = Booking.CONFIRMED
            b.confirmed_at = now
            b.payment_token = result.transaction_id
            b.qr_token = qr_token if index == 0 else None
            b.save(update_fields=["status", "confirmed_at", "payment_token", "qr_token"])
        BookingService._notify(bookings[0].user, "BOOKING_CONFIRM", "Booking confirmed", f"Your CineLux booking is confirmed: {qr_token}", bookings[0])
        return booking_group_payload(bookings)

    @staticmethod
    def list_for_user(user, status=None):
        qs = Booking.objects.filter(user=user).select_related("showtime__movie", "seat").order_by("-booked_at")
        if status:
            qs = qs.filter(status=status)
        return {"bookings": [{"bookingId": str(b.booking_id), "bookingGroupId": str(b.booking_group_id), "movieTitle": b.showtime.movie.title, "startTime": b.showtime.start_time, "seat": b.seat.label, "status": b.status, "qrCodeToken": b.qr_token} for b in qs[:100]]}

    @staticmethod
    def get_booking(user, booking_id):
        try:
            b = Booking.objects.select_related("showtime__movie", "seat").get(booking_id=booking_id)
        except Booking.DoesNotExist:
            raise CineLuxError("BOOK-404", "Booking not found.")
        if b.user_id != user.user_id and user.role != "ADMIN":
            raise CineLuxError("GEN-403", "Not authorised.")
        return {"bookingId": str(b.booking_id), "bookingGroupId": str(b.booking_group_id), "movieTitle": b.showtime.movie.title, "showtimeId": str(b.showtime_id), "startTime": b.showtime.start_time, "seat": b.seat.label, "status": b.status, "qrCodeToken": b.qr_token, "createdAt": b.booked_at}

    @staticmethod
    @transaction.atomic
    def cancel(user, booking_id):
        try:
            first = Booking.objects.select_for_update().select_related("showtime").get(booking_id=booking_id)
        except Booking.DoesNotExist:
            raise CineLuxError("BOOK-404", "Booking not found.")
        if first.user_id != user.user_id and user.role != "ADMIN":
            raise CineLuxError("GEN-403", "Not authorised.")
        if first.status in {Booking.CANCELLED, Booking.USED} or timezone.now() >= first.showtime.start_time - timedelta(hours=settings.REFUND_PARTIAL_HOURS):
            raise CineLuxError("BOOK-403", "Cancellation not allowed.")
        group = list(Booking.objects.select_for_update().filter(booking_group_id=first.booking_group_id))
        amount = sum((b.price_paid for b in group), Decimal("0.00"))
        for b in group:
            b.status = Booking.CANCELLED
            b.cancelled_at = timezone.now()
            b.save(update_fields=["status", "cancelled_at"])
        if first.payment_token:
            refund = PaymentGateway().refund(first.payment_token, amount, first.showtime.currency, str(first.booking_group_id))
            if refund.status != "SUCCESS":
                PendingRefund.objects.create(booking_group_id=first.booking_group_id, payment_token=first.payment_token, amount=amount, currency=first.showtime.currency)
        BookingService._notify(first.user, "BOOKING_CANCEL", "Booking cancelled", "Your CineLux booking was cancelled.", first)
        return {"bookingGroupId": str(first.booking_group_id), "status": "CANCELLED", "cancelledAt": timezone.now()}

    @staticmethod
    @transaction.atomic
    def validate_ticket(validator, qr_token):
        ticket = Booking.objects.select_for_update().filter(qr_token=qr_token).first()
        if not ticket:
            EntryLog.objects.create(validator_user=validator, result="INVALID")
            raise CineLuxError("VAL-401", "Ticket not found.")
        bookings = list(
            Booking.objects.select_for_update()
            .select_related("showtime__movie", "showtime__hall", "seat", "user")
            .filter(booking_group_id=ticket.booking_group_id)
            .order_by("seat__row_label", "seat__seat_number")
        )
        first = bookings[0]
        now = timezone.now()
        result = None
        if first.status == Booking.USED:
            result = "ALREADY_USED"
            EntryLog.objects.create(booking_group_id=first.booking_group_id, validator_user=validator, showtime=first.showtime, result=result)
            raise CineLuxError("VAL-409", "Ticket already used.", details={"usedAt": first.used_at})
        if first.status == Booking.CANCELLED:
            result = "INVALID"
            EntryLog.objects.create(booking_group_id=first.booking_group_id, validator_user=validator, showtime=first.showtime, result=result)
            raise CineLuxError("VAL-403", "Ticket cancelled.")
        if first.status != Booking.CONFIRMED:
            EntryLog.objects.create(booking_group_id=first.booking_group_id, validator_user=validator, showtime=first.showtime, result="INVALID")
            raise CineLuxError("VAL-400", "Ticket not in confirmed state.")
        if now < first.showtime.start_time - timedelta(minutes=settings.ENTRY_OPEN_MINUTES):
            raise CineLuxError("VAL-410", "Too early.")
        if now > first.showtime.end_time:
            raise CineLuxError("VAL-411", "Show has already ended.")
        for b in bookings:
            b.status = Booking.USED
            b.used_at = now
            b.save(update_fields=["status", "used_at"])
        EntryLog.objects.create(booking_group_id=first.booking_group_id, validator_user=validator, showtime=first.showtime, result="VALID")
        return {"result": "VALID", "bookingGroupId": str(first.booking_group_id), "movieTitle": first.showtime.movie.title, "showtime": first.showtime.start_time, "hall": first.showtime.hall.name, "seats": [b.seat.label for b in bookings], "userName": first.user.full_name}

    @staticmethod
    def expire_holds():
        return Booking.objects.filter(status=Booking.PENDING, hold_expires_at__lte=timezone.now()).update(status=Booking.EXPIRED)

    @staticmethod
    def _notify(user, type_, subject, body, booking):
        notification = Notification.objects.create(user=user, type=type_, channel="EMAIL", subject=subject, body=body, related_booking=booking)
        result = NotificationService().send_email(user.email, subject, body)
        notification.status = "SENT" if result.status == "SUCCESS" else "FAILED"
        notification.sent_at = timezone.now() if result.status == "SUCCESS" else None
        notification.retry_count = 0 if result.status == "SUCCESS" else 1
        notification.save(update_fields=["status", "sent_at", "retry_count"])
