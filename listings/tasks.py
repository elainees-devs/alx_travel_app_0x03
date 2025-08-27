# bookings/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking


@shared_task
def send_payment_confirmation_email(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        user = booking.user

        subject = "Payment Confirmation - ALX Travel App"
        message = (
            f"Hello {user.first_name},\n\n"
            f"Your payment for booking reference {booking.id} "
            f"amounting to {booking.total_price} ETB has been successfully completed.\n\n"
            f"Thank you for booking with us!\n\n"
            f"ALX Travel Team"
        )

        recipient_list = [user.email]

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # make sure this is set in settings.py
            recipient_list,
            fail_silently=False,
        )

        return f"Payment confirmation email sent to {user.email}"

    except Booking.DoesNotExist:
        return f"Booking with id {booking_id} not found"
    except Exception as e:
        return f"Error sending payment confirmation: {str(e)}"
