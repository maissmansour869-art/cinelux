from django.contrib import admin

from .models import Booking, EntryLog, Notification, PendingRefund

admin.site.register(Booking)
admin.site.register(Notification)
admin.site.register(EntryLog)
admin.site.register(PendingRefund)
