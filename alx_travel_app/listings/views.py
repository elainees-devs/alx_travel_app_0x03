import time
import json
import logging
import requests

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer
from .tasks import send_payment_confirmation_email
from listings.utils.chapa import initialize_payment, verify_payment

logger = logging.getLogger(__name__)


# -------------------------
# Sample API
# -------------------------
class SampleView(APIView):
    def get(self, request):
        return Response({"message": "Hello from listings API!"})


# -------------------------
# Test Chapa Payment API
# -------------------------
class TestChapaPaymentView(APIView):
    @swagger_auto_schema(operation_description="Test Chapa payment endpoint")
    def get(self, request):
        payload = {
            "amount": "10",
            "currency": "ETB",
            "email": "customer@test.com",
            "first_name": "John",
            "last_name": "Doe",
            "tx_ref": f"test_{int(time.time())}",
            "callback_url": "https://webhook.site/example"
        }

        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                "https://api.chapa.co/v1/transaction/initialize",
                json=payload,
                headers=headers,
                timeout=10
            )
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            logger.error(f"Chapa test payment failed: {str(e)}")
            return Response({"error": str(e)}, status=500)


# -------------------------
# Listing ViewSet
# -------------------------
class ListingViewSet(ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer


# -------------------------
# Booking ViewSet
# -------------------------
class BookingViewSet(ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


# -------------------------
# Initiate Payment
# -------------------------
class InitiatePaymentView(APIView):
    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        if Payment.objects.filter(booking_reference=str(booking.id), user=request.user).exists():
            return Response({"error": "Payment already exists"}, status=status.HTTP_400_BAD_REQUEST)

        booking_ref = f"booking_{booking.id}_{int(time.time())}"
        payload = {
            "amount": str(booking.total_price),
            "currency": "ETB",
            "email": request.user.email,
            "tx_ref": booking_ref,
            "callback_url": f"{settings.BASE_URL}/api/payments/verify/{booking.id}/",
        }

        headers = {
            "Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                "https://api.chapa.co/v1/transaction/initialize",
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            response_data = response.json()
            logger.info(f"Chapa init response: {response_data}")

            if response.status_code == 200 and response_data.get("status") == "success":
                payment = Payment.objects.create(
                    user=request.user,
                    booking_reference=booking_ref,
                    amount=booking.total_price,
                    transaction_id=response_data["data"]["tx_ref"],
                    payment_status="Pending"
                )
                return Response({
                    "payment": PaymentSerializer(payment).data,
                    "payment_url": response_data["data"]["checkout_url"]
                }, status=status.HTTP_201_CREATED)

            logger.error(f"Payment initiation failed: {response_data}")
            return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            logger.error(f"Payment initiation request error: {str(e)}")
            return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)


# -------------------------
# Verify Payment
# -------------------------
class VerifyPaymentView(APIView):
    def get(self, request, booking_id):
        payment = Payment.objects.filter(
            user=request.user,
            booking_reference__contains=f"_{booking_id}_"
        ).first()

        if not payment:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            response = requests.get(
                f"https://api.chapa.co/v1/transaction/verify/{payment.transaction_id}",
                headers={"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"},
                timeout=10
            )
            response_data = response.json()
            logger.info(f"Chapa verify response: {response_data}")

            if response.status_code == 200 and response_data.get("status") == "success":
                payment.payment_status = "Completed"
                payment.save()

                # Trigger async email
                try:
                    send_payment_confirmation_email.delay(booking_id)
                    logger.info(f"Payment confirmation email task queued for booking {booking_id}")
                except Exception as e:
                    logger.error(f"Failed to enqueue email task: {str(e)}")

                return Response({"status": "completed", "payment": PaymentSerializer(payment).data})

            payment.payment_status = "Failed"
            payment.save()
            return Response({"status": "failed", "payment": PaymentSerializer(payment).data}, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            logger.error(f"Chapa verify request error: {str(e)}")
            return Response({"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            return Response({"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)
