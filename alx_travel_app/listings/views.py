import time
import json
import logging
import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view,permission_classes, action
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer, PaymentInputSerializer
from .tasks import send_payment_confirmation_email
from alx_travel_app.listings.utils.chapa import initialize_payment, verify_payment
import random


logger = logging.getLogger(__name__)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_send_email(request):
    """
    Test endpoint to send a payment confirmation email via Celery.
    Accepts 'booking_id' and optional 'to_email' in request body.
    """
    booking_id = request.data.get("booking_id", 1)
    to_email = request.data.get("to_email", request.user.email)

    send_payment_confirmation_email.apply_async(
        kwargs={"booking_id": booking_id, "to_email": to_email}
    )

    return Response({"status": "Email task queued for Celery worker"})
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
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Short-circuit for Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Booking.objects.none()
        return Booking.objects.all()

    # -------------------------
    # Custom pay action
    # -------------------------
    @action(detail=True, methods=['post'], url_path='pay')
    def pay(self, request, pk=None):
        booking = get_object_or_404(Booking, id=pk, user=request.user)

        # Prevent duplicate payments
        if Payment.objects.filter(booking_reference=f"booking_{booking.id}", user=request.user).exists():
            return Response({"error": "Payment already exists"}, status=status.HTTP_400_BAD_REQUEST)

        booking_ref = f"booking_{booking.id}_{int(time.time())}"
        payment = Payment.objects.create(
            user=request.user,
            booking_reference=booking_ref,
            amount=random.randint(1000, 5000),  # replace with booking total if available
            transaction_id=f"tx_{random.randint(1000,9999)}",
            payment_status=random.choice(["Pending", "Completed", "Failed"])
        )

        # Optionally trigger async email
        try:
            send_payment_confirmation_email.delay(booking.id)
        except Exception:
            pass

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

# -------------------------
# Initiate Payment
# -------------------------
@permission_classes([IsAuthenticated])
class InitiatePaymentView(APIView):
    @swagger_auto_schema(
        request_body=PaymentInputSerializer,
        responses={201: PaymentSerializer}
    )
    def post(self, request, booking_id):
        # Ensure user is authenticated
        if request.user.is_anonymous:
            return Response({"error": "Authentication required"}, status=401)

        # Get booking for this user
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        # Validate input data from Swagger
        serializer = PaymentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Calculate amount if not provided
        amount = serializer.validated_data.get(
            "amount",
            booking.property.price_per_night * (booking.check_out - booking.check_in).days
        )
        currency = serializer.validated_data.get("currency", "ETB")

        # Check if payment already exists
        if Payment.objects.filter(booking_reference=f"booking_{booking.id}", user=request.user).exists():
            return Response({"error": "Payment already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare Chapa payload
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

            logger.error(f"Payment initiation failed: {response_data}")
            return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            logger.error(f"Payment initiation request error: {str(e)}")
            return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)


# -------------------------
# Verify Payment
# -------------------------
@permission_classes([IsAuthenticated])
class VerifyPaymentView(APIView):
    def get(self, request, booking_id):
            #Check for anonymous user first
        if request.user.is_anonymous:
            return Response({"error": "Authentication required"}, status=401)
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


@permission_classes([IsAuthenticated])    
class VerifiedPaymentsView(APIView):

    def get(self, request):
        payments = Payment.objects.filter(payment_status="Completed")
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
