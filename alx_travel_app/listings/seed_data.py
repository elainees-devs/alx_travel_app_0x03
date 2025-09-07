from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from alx_travel_app.listings.models import Listing, Booking, Review, Payment
from datetime import date, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = "Seed the database with sample listings, bookings, reviews, and payments."

    def handle(self, *args, **kwargs):
        # Ensure at least 1 user exists
        user, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True}
        )

        # Seed Listings
        listings = []
        for i in range(5):
            listing, _ = Listing.objects.get_or_create(
                title=f"Sample Property {i+1}",
                defaults={
                    "description": f"Description for property {i+1}",
                    "location": f"City {i+1}",
                    "price_per_night": random.randint(50, 200),
                }
            )
            listings.append(listing)

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(listings)} listings."))

        # Seed Bookings
        for i in range(10):
            property = random.choice(listings)
            check_in = date.today() + timedelta(days=i * 2)
            check_out = check_in + timedelta(days=3)

            Booking.objects.create(
                user=user,
                property=property,
                check_in=check_in,
                check_out=check_out,
            )

        self.stdout.write(self.style.SUCCESS("✅ Created 10 bookings."))

        # Seed Reviews
        for listing in listings:
            Review.objects.create(
                user=user,
                property=listing,
                rating=random.randint(3, 5),
                comment="Great place!"
            )

        self.stdout.write(self.style.SUCCESS("✅ Created reviews for listings."))

        # Seed Payments
        for booking in Booking.objects.all()[:5]:
            Payment.objects.create(
                user=user,
                booking_reference=f"BOOK-{booking.id}",
                amount=booking.property.price_per_night * 3,
                payment_status=random.choice(["Pending", "Completed", "Failed"]),
            )

        self.stdout.write(self.style.SUCCESS("✅ Created sample payments."))
        self.stdout.write(self.style.SUCCESS("🎉 Database seeding complete!"))
