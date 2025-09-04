from django.contrib import admin

# Register your models here.
from .models import Booking, Listing, Payment

admin.site.register(Booking)
admin.site.register(Listing)
admin.site.register(Payment)