import os
import sys

from django.apps import AppConfig


class BookingsConfig(AppConfig):
    name = 'bookings'
    scheduler = None

    def ready(self):
        if os.getenv("CINELUX_ENABLE_SCHEDULER", "1") != "1":
            return
        command = sys.argv[1] if len(sys.argv) > 1 else ""
        if command in {"check", "collectstatic", "createsuperuser", "makemigrations", "migrate", "shell", "test"}:
            return
        if command == "runserver" and os.getenv("RUN_MAIN") != "true":
            return
        if BookingsConfig.scheduler:
            return
        from scheduler.jobs import start_scheduler

        BookingsConfig.scheduler = start_scheduler()
