import time
import json
import logging
import requests
import random
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, action
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
from django.shortcuts import get_object_or_404

from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer, PaymentInputSerializer
from .tasks import send_payment_confirmation_email
from alx_travel_app.listings.utils.chapa import initialize_payment, verify_payment

logger = logging.getLogger(__name__)

# -------------------------
# Test Email
# -------------------------
@api_view(["POST"])
def test_send_email(request):
    booking_id = request.data.get("booking_id", 1)
    to_email = request.data.get("to_email", getattr(request.user, "email", None))

    send_payment_confirmation_email.apply_async(
        kwargs={"booking_id": booking_id, "to_email": to_email}
    )

    return Response({"status": "Email task queued for Celery worker"})


# -------------------------
# Sample API
# -------------------------
class SampleView(APIView):
    def get(self, request):
        if getattr(self, "swagger_fake_view", False):
            return Response({"message": "Swagger schema"}, status=200)
        return Response({"message": "Hello from listings API!"})


# -------------------------
# Test Chapa Payment API
# -------------------------
class TestChapaPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_description="Test Chapa payment endpoint")
    def get(self, request):
        if getattr(self, "swagger_fake_view", False):
            return Response({"message": "Swagger schema"}, status=200)

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
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            # Return first 5 bookings for Swagger display
            return Booking.objects.all()[:5]
        # Return all bookings
        return Booking.objects.all()


    @swagger_auto_schema(
        method="post",
        operation_description="Pay for a booking",
        responses={201: PaymentSerializer},
    )
    @action(detail=True, methods=["post"], url_path="pay")
    def pay(self, request, pk=None):
        if getattr(self, "swagger_fake_view", False):
            return Response({"message": "Swagger schema"}, status=200)

        booking = get_object_or_404(Booking, id=pk, user=request.user)

        if Payment.objects.filter(
            booking_reference__startswith=f"booking_{booking.id}_", user=request.user
        ).exists():
            return Response(
                {"error": "Payment already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking_ref = f"booking_{booking.id}_{int(time.time())}"
        payment = Payment.objects.create(
            user=request.user,
            booking_reference=booking_ref,
            amount=random.randint(1000, 5000),
            transaction_id=f"tx_{random.randint(1000,9999)}",
            payment_status=random.choice(["Pending", "Completed", "Failed"]),
        )

        try:
            send_payment_confirmation_email.delay(booking.id)
        except Exception as e:
            logger.error(f"Email task failed: {str(e)}")

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

# -------------------------
# Initiate Payment
# -------------------------
class InitiatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=PaymentInputSerializer,
        responses={201: PaymentSerializer}
    )
    def post(self, request, booking_id):
        if getattr(self, "swagger_fake_view", False):
            return Response({"message": "Swagger schema"}, status=200)

        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        serializer = PaymentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data.get(
            "amount",
            booking.property.price_per_night * (booking.check_out - booking.check_in).days
        )
        currency = serializer.validated_data.get("currency", "ETB")

        if Payment.objects.filter(booking_reference=f"booking_{booking.id}", user=request.user).exists():
            return Response({"error": "Payment already exists"}, status=status.HTTP_400_BAD_REQUEST)

        booking_ref = f"booking_{booking.id}_{int(time.time())}"
        payload = {
            "amount": str(amount),
            "currency": currency,
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
                    amount=amount,
                    transaction_id=response_data["data"]["tx_ref"],
                    payment_status="Pending"
                )
                return Response({
                    "payment": PaymentSerializer(payment).data,
                    "payment_url": response_data["data"]["checkout_url"]
                }, status=status.HTTP_201_CREATED)

            return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            logger.error(f"Payment initiation request error: {str(e)}")
            return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)


# -------------------------
# Verify Payment
# -------------------------
class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id):
        if getattr(self, "swagger_fake_view", False):
            return Response({"message": "Swagger schema"}, status=200)

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

                try:
                    send_payment_confirmation_email.delay(booking_id)
                except Exception as e:
                    logger.error(f"Failed to enqueue email task: {str(e)}")

                return Response({"status": "completed", "payment": PaymentSerializer(payment).data})

            payment.payment_status = "Failed"
            payment.save()
            return Response({"status": "failed", "payment": PaymentSerializer(payment).data}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            return Response({"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)


# -------------------------
# Verified Payments List
# -------------------------
class VerifiedPaymentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if getattr(self, "swagger_fake_view", False):
            return Response({"message": "Swagger schema"}, status=200)

        payments = Payment.objects.filter(payment_status="Completed")
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
