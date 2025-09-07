from django.urls import path, include
from .create_superuser import create_admin
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, BookingViewSet, VerifyPaymentView, VerifiedPaymentsView, test_send_email

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),  # includes /bookings/{id}/pay/
    path('payments/verify/<int:booking_id>/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('payments/verified/', VerifiedPaymentsView.as_view(), name='verified-payments'),
    path('email/test-send-email/', test_send_email),
     path("create-admin/", create_admin),

]
