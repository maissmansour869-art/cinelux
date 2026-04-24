import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Booking(models.Model):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    USED = "USED"
    EXPIRED = "EXPIRED"

    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_group_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="bookings")
    showtime = models.ForeignKey("catalogues.Showtime", on_delete=models.RESTRICT, related_name="bookings")
    seat = models.ForeignKey("catalogues.Seat", on_delete=models.RESTRICT)
    status = models.CharField(max_length=20, choices=[(PENDING, PENDING), (CONFIRMED, CONFIRMED), (CANCELLED, CANCELLED), (USED, USED), (EXPIRED, EXPIRED)], default=PENDING)
    price_paid = models.DecimalField(max_digits=10, decimal_places=2)
    qr_token = models.CharField(max_length=128, unique=True, null=True, blank=True)
    payment_token = models.CharField(max_length=128, blank=True)
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    booked_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "bookings"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["booking_group_id"]),
            models.Index(fields=["qr_token"]),
            models.Index(fields=["hold_expires_at"], condition=Q(status="PENDING"), name="idx_booking_hold_expiry"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["showtime", "seat"], condition=Q(status__in=["PENDING", "CONFIRMED", "USED"]), name="uniq_active_seat_per_showtime"),
        ]

    def __str__(self):
        return f"Booking #{self.booking_id} by {self.user.email}"


class Notification(models.Model):
    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=40)
    channel = models.CharField(max_length=10, choices=[("EMAIL", "EMAIL"), ("SMS", "SMS"), ("IN_APP", "IN_APP")])
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    related_booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[("PENDING", "PENDING"), ("SENT", "SENT"), ("FAILED", "FAILED"), ("DELIVERED", "DELIVERED")], default="PENDING")
    retry_count = models.PositiveIntegerField(default=0)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        indexes = [models.Index(fields=["user", "is_read"]), models.Index(fields=["status"])]


class EntryLog(models.Model):
    entry_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_group_id = models.UUIDField(null=True, blank=True)
    validator_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT)
    showtime = models.ForeignKey("catalogues.Showtime", on_delete=models.RESTRICT, null=True, blank=True)
    result = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "entry_logs"
        indexes = [models.Index(fields=["showtime"])]


class PendingRefund(models.Model):
    refund_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_group_id = models.UUIDField(db_index=True)
    payment_token = models.CharField(max_length=128)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, default="PENDING")
    retry_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pending_refunds"
