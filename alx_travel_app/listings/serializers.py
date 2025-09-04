from rest_framework import serializers
from .models import Listing, Booking, Review, Payment

# ------------------------
# Listing Serializer
# ------------------------

class ListingSerializer(serializers.ModelSerializer):
    price_display = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = ['id', 'title', 'description', 'location', 'price_per_night', 'price_display']

    def get_price_display(self, obj):
        # Return a formatted price string (e.g., "$150.00 per night")
        return f"${obj.price_per_night:.2f} per night"


# ------------------------
# Booking Serializer
# ------------------------

class BookingSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    property_title = serializers.CharField(source='property.title', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'user', 'user_email', 'property', 'property_title', 'check_in', 'check_out']

    def validate(self, data):
        # Ensure check_out is after check_in
        if data['check_out'] <= data['check_in']:
            raise serializers.ValidationError("Check-out date must be after check-in date.")
        return data


# ------------------------
# Review Serializer
# ------------------------

class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    property_title = serializers.CharField(source='property.title', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'user', 'user_email', 'property', 'property_title', 'rating', 'comment']

    def validate_rating(self, value):
        # Ensure rating is between 1 and 5
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    # ------------------------
# Payment Serializer
# ------------------------
# Returns payment details including user email to client
class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'user', 'user_email', 'booking_reference', 'amount', 'transaction_id', 'payment_status', 'created_at']
        
# Input serializer for initiating payment
class PaymentInputSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    currency = serializers.CharField(max_length=3, default="ETB", required=False)