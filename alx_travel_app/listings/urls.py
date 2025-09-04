from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, BookingViewSet, VerifyPaymentView

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),  # includes /bookings/{id}/pay/
    path('payments/verify/<int:booking_id>/', VerifyPaymentView.as_view(), name='verify-payment'),
]
