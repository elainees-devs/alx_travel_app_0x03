
# Payment Integration with Chapa API

## Objective
This project integrates the **Chapa API** into a Django application to handle secure online payments for bookings.  
It allows users to initiate and verify payments, updating the system with the correct payment status.

---

## 🛠️ Technologies
- **Python 3** – Programming language  
- **Django** – Web framework for backend development  
- **Django REST Framework (DRF)** – For building RESTful APIs  
- **Chapa API** – Payment gateway integration  
- **Celery** – Task queue for handling background jobs (e.g., sending confirmation emails)  
- **Redis** – Message broker for Celery  
- **MySQL** – Database
- **Requests (Python library)** – For making HTTP requests to Chapa API  
- **Environment Variables (.env)** – For secure storage of credentials  

**Optional (for testing and development):**  
- **pytest / unittest** – Testing framework  
- **Chapa Sandbox Environment** – For payment testing  

## Project Setup

### 1. Duplicate Project
Duplicate the base project:
```bash
cp -r alx_travel_app_0x01 alx_travel_app_0x02
````

---

### 2. Set Up Chapa API Credentials

1. Create an account at [Chapa Developer Portal](https://developer.chapa.co/).
2. Obtain your **API keys** from the dashboard.
3. Store the keys as environment variables for security:

   ```bash
   export CHAPA_SECRET_KEY="your_chapa_secret_key"
   export CHAPA_BASE_URL="https://api.chapa.co/v1"
   ```

---

### 3. Create Payment Model

Add a `Payment` model in `listings/models.py` to store:

* Booking reference
* Transaction ID
* Payment amount
* Payment status (`Pending`, `Completed`, `Failed`)

---

### 4. Create Payment API View

In `listings/views.py`:

* Implement an API endpoint to **initiate payment**:

  * Send a POST request to Chapa with booking details.
  * Store the returned `transaction ID`.
  * Set status to `"Pending"`.

---

### 5. Verify Payment

* Create an API endpoint to **verify payment** with Chapa.
* Update the `Payment` model with:

  * `"Completed"` if successful.
  * `"Failed"` otherwise.

---

### 6. Implement Payment Workflow

* When a user makes a booking:

  * Initiate the payment process.
  * Provide them with a link to complete the payment via Chapa.
* On successful payment:

  * Update payment status.
  * Send a confirmation email (Celery for background tasks).
* Handle errors gracefully, ensuring failed transactions are marked properly.

---

### 7. Test Payment Integration

* Use **Chapa Sandbox Environment** for testing.
* Validate the workflow:

  * Payment initiation
  * Status verification
  * Database updates in `Payment` model

---

## Repo Structure

```
alx_travel_app_0x02/
│── alx_travel_app/
│   ├── listings/
│   │   ├── models.py   # Payment model
│   │   ├── views.py    # Initiate + verify payment
│   │   ├── urls.py     # Payment endpoints
│   │   └── utils/      # Chapa API utils
│   ├── settings.py     # Load Chapa credentials
│   └── ...
│── README.md
```

---

## Example Endpoints

### Initiate Payment

```http
POST /bookings/<booking_id>/pay/
```

### Verify Payment

```http
GET /payments/verify/<booking_id>/
```

---

## Notes

* Store sensitive credentials in environment variables.
* Include screenshots/logs of successful transactions in your project documentation.

---

## Repository

* **GitHub Repo**: `alx_travel_app_0x02`
* **Directory**: `alx_travel_app`


