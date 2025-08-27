from django.shortcuts import get_object_or_404
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework import status
from django.conf import settings
import logging
import requests
from requests.exceptions import RequestException, Timeout
from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer
from .tasks import send_payment_confirmation_email
from rest_framework.decorators import action
from listings.utils.chapa import initialize_payment, verify_payment
from drf_yasg.utils import swagger_auto_schema
import json



class SampleView(APIView):
    def get(self, request):
        return Response({"message": "Hello from listings API!"})
    

class TestChapaPaymentView(APIView):
    @swagger_auto_schema(operation_description="Test Chapa payment endpoint")
    def get(self, request):
        # Set up test payload
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

        # Chapa API endpoint
        url = "https://api.chapa.co/v1/transaction/initialize"

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            # Return Chapa response directly
            return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"error": str(e)}, status=500)

       
     



logger = logging.getLogger(__name__)


class ListingViewSet(ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer


class BookingViewSet(ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


class InitiatePaymentView(APIView):
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)

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

            response = requests.post(
                "https://api.chapa.co/v1/transaction/initialize",
                headers={"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}", "Content-Type": "application/json"},
                data=json.dumps(payload)
            )
            response_data = response.json()

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

            return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)

        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)


class VerifyPaymentView(APIView):
    def get(self, request, booking_id):
        try:
            payment = Payment.objects.filter(user=request.user, booking_reference__contains=f"_{booking_id}_").first()
            if not payment:
                return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

            response = requests.get(
                f"https://api.chapa.co/v1/transaction/verify/{payment.transaction_id}",
                headers={"Authorization": f"Bearer {settings.CHAPA_SECRET_KEY}"}
            )
            response_data = response.json()

            if response.status_code == 200 and response_data.get("status") == "success":
                payment.payment_status = "Completed"
                payment.save()
                send_payment_confirmation_email.delay(booking_id)
                return Response({"status": "completed", "payment": PaymentSerializer(payment).data})

            payment.payment_status = "Failed"
            payment.save()
            return Response({"status": "failed", "payment": PaymentSerializer(payment).data}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({"error": "Verification failed"}, status=status.HTTP_400_BAD_REQUEST)
        

        from rest_framework.views import APIView

