# Payment Integration with Chapa API & Celery Email Notifications

## Objective
This project integrates the **Chapa API** into a Django application to handle secure online payments for bookings.  
It also uses **Celery** to send asynchronous email notifications after successful payments.

---

## 🛠️ Technologies
- **Python 3** – Programming language  
- **Django** – Web framework for backend development  
- **Django REST Framework (DRF)** – For building RESTful APIs  
- **Chapa API** – Payment gateway integration  
- **Celery** – Task queue for handling background jobs (e.g., sending confirmation emails)  
- **RabbitMQ / Redis** – Message broker for Celery  
- **MySQL** – Database  
- **Requests (Python library)** – For making HTTP requests to Chapa API  
- **Environment Variables (.env)** – For secure storage of credentials  

**Optional (for testing and development):**  
- **pytest / unittest** – Testing framework  
- **Chapa Sandbox Environment** – For payment testing  

---

## Project Setup

### 1. Duplicate Project
Duplicate the base project:

```bash
cp -r alx_travel_app_0x02 alx_travel_app_0x03
````

---

### 2. Set Up Environment Variables

Create a `.env` file with your credentials:

```env
SECRET_KEY="your_django_secret_key"
CHAPA_SECRET_KEY="your_chapa_secret_key"
BASE_URL="http://127.0.0.1:8000"
EMAIL_HOST="smtp.example.com"
EMAIL_PORT=587
EMAIL_HOST_USER="your_email@example.com"
EMAIL_HOST_PASSWORD="your_password"
EMAIL_USE_TLS=True
```

---

### 3. Configure Celery

1. Install Celery and RabbitMQ client:

```bash
pip install celery django-celery-results
```

2. Create `alx_travel_app/celery.py`:

```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_travel_app.settings")

app = Celery("alx_travel_app")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

3. Update `alx_travel_app/__init__.py`:

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

---

### 4. Payment Model

Add a `Payment` model in `listings/models.py`:

```python
from django.db import models
from django.contrib.auth.models import User

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking_reference = models.CharField(max_length=255)
    transaction_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### 5. Celery Email Task

Add `listings/tasks.py`:

```python
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_confirmation_email(self, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        user = booking.user
        subject = "Payment Confirmation - ALX Travel App"
        message = f"Hello {user.first_name},\n\nYour payment for booking {booking.id} amounting to {booking.total_price} ETB has been successfully completed.\n\nThank you for booking with us!\n\nALX Travel Team"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        return f"Payment confirmation email sent to {user.email}"
    except Exception as e:
        raise self.retry(exc=e)
```

---

### 6. Payment Views

1. **Initiate Payment** (`POST /bookings/<booking_id>/pay/`)
2. **Verify Payment** (`GET /payments/verify/<booking_id>/`) – triggers Celery task after successful payment.

---

### 7. Running the Project

1. Start RabbitMQ (or Redis):

```bash
sudo systemctl start rabbitmq-server
```

2. Start Celery worker:

```bash
celery -A alx_travel_app worker -l info
```

3. Run Django server:

```bash
python manage.py runserver
```

4. Test booking payment and email workflow using Chapa Sandbox.

---

## Repo Structure

```
alx_travel_app_0x03/
│── alx_travel_app/
│   ├── listings/
│   │   ├── models.py   # Booking + Payment model
│   │   ├── views.py    # Initiate + verify payment
│   │   ├── tasks.py    # Celery async email task
│   │   ├── urls.py     # Payment endpoints
│   │   └── utils/      # Chapa API helpers
│   ├── settings.py     # Load .env, Celery, email config
│   ├── celery.py       # Celery app
│   └── __init__.py
│── manage.py
│── README.md
│── requirements.txt
```

---

### Notes

* Always use environment variables for sensitive credentials.
* Celery handles asynchronous email sending after payment verification.
* Test all endpoints with Chapa Sandbox before going live.
* Logs can be used to monitor payment initiation and verification status.

---

### Repository

* **GitHub Repo**: `alx_travel_app_0x03`
* **Directory**: `alx_travel_app`

---

### Quick Start (Optional `curl` Examples)

**Initiate Payment:**

```bash
curl -X POST http://127.0.0.1:8000/bookings/1/pay/ -H "Authorization: Token <your_token>"
```

**Verify Payment:**

```bash
curl -X GET http://127.0.0.1:8000/payments/verify/1/ -H "Authorization: Token <your_token>"
```

```

---

