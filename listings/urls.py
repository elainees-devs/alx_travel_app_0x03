# listings/urls.py

from django.urls import path

from .views import SampleView, InitiatePaymentView, VerifyPaymentView , TestChapaPaymentView
urlpatterns = [
    path('payment/test/', TestChapaPaymentView.as_view(), name='test-payment'),
    path('sample/', SampleView.as_view(), name='sample'),  # test endpoint
    path('bookings/<int:booking_id>/pay/', InitiatePaymentView.as_view(), name='initiate-payment'),
    path('payments/verify/<int:booking_id>/', VerifyPaymentView.as_view(), name='verify-payment'),
  
]
