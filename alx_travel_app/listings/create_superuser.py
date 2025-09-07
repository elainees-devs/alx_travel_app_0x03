# In a temporary file, e.g., create_superuser.py in one of your apps

from django.contrib.auth.models import User
from django.http import HttpResponse

def create_admin(request):
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin2025"
        )
        return HttpResponse("Superuser created!")
    return HttpResponse("Superuser already exists!")
