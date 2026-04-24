from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone

from bookings.models import Notification
from bookings.services import BookingService
from externals.notification_service import NotificationService


def booking_hold_expiry():
    return BookingService.expire_holds()


def notification_retry_sweep():
    service = NotificationService()
    for notification in Notification.objects.filter(status="FAILED", retry_count__lt=3):
        result = service.send_email(notification.user.email, notification.subject, notification.body)
        notification.retry_count += 1
        if result.status == "SUCCESS":
            notification.status = "SENT"
            notification.sent_at = timezone.now()
        notification.save(update_fields=["retry_count", "status", "sent_at"])


def rec_similarity_refresh():
    return None


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(notification_retry_sweep, "interval", minutes=5, id="notification_retry_sweep", replace_existing=True)
    scheduler.add_job(booking_hold_expiry, "interval", minutes=1, id="booking_hold_expiry", replace_existing=True)
    scheduler.add_job(rec_similarity_refresh, "cron", hour=3, minute=0, id="rec_similarity_refresh", replace_existing=True)
    scheduler.start()
    return scheduler
