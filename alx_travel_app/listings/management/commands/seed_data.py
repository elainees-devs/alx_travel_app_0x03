import random
from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from alx_travel_app.listings.models import Listing, Booking, Review, Payment


User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with sample listings, bookings, reviews, and payments"

    def handle(self, *args, **kwargs):
        # 1. Create a demo user
        user, created = User.objects.get_or_create(
            username="demo_user",
            defaults={"email": "demo@example.com", "password": "demo1234"}
        )

        # 2. Create 10 listings
        listings = []
        for i in range(10):
            listing, _ = Listing.objects.get_or_create(
                title=f"Sample Property {i+1}",
                defaults={
                    "description": f"This is a description for property {i+1}",
                    "location": f"City {i+1}",
                    "price_per_night": round(random.uniform(50, 300), 2),
                },
            )
            listings.append(listing)

        # 3. Create 10 bookings
        for i, listing in enumerate(listings, start=1):
            check_in = date.today() + timedelta(days=i)
            check_out = check_in + timedelta(days=random.randint(2, 7))

            booking, _ = Booking.objects.get_or_create(
                user=user,
                property=listing,
                check_in=check_in,
                check_out=check_out,
            )

            # 4. Add a review
            Review.objects.get_or_create(
                user=user,
                property=listing,
                rating=random.randint(1, 5),
                comment=f"Review for {listing.title}"
            )

            # 5. Add a payment
            Payment.objects.get_or_create(
                user=user,
                booking_reference=f"booking_{booking.id}",
                amount=listing.price_per_night * (check_out - check_in).days,
                transaction_id=f"tx_{i}{random.randint(1000,9999)}",
                payment_status=random.choice(["Pending", "Completed", "Failed"]),
            )

        self.stdout.write(self.style.SUCCESS("Seed data created successfully!"))
