# listings/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking


@shared_task
def send_payment_confirmation_email(booking_id, to_email=None):
    try:
        booking = Booking.objects.get(id=booking_id)
        subject = f"Payment Confirmation for Booking #{booking.id}"
        message = f"Dear {booking.user.username}, your booking is confirmed."
        
        # If a custom email is provided, use it. Otherwise, fallback to booking.user.email
        recipient = [to_email] if to_email else [booking.user.email]

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient,
            fail_silently=False,
        )
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found"
