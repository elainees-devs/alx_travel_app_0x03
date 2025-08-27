# listings/utils/chapa.py

import os
import requests
from django.conf import settings

CHAPA_SECRET_KEY = os.getenv("CHAPA_SECRET_KEY", getattr(settings, "CHAPA_SECRET_KEY", ""))
CHAPA_BASE_URL = os.getenv("CHAPA_BASE_URL", getattr(settings, "CHAPA_BASE_URL", "https://api.chapa.co/v1"))

HEADERS = {
    "Authorization": f"Bearer {CHAPA_SECRET_KEY}",
    "Content-Type": "application/json"
}


def initialize_payment(amount, email, tx_ref, currency="TZS", first_name="", last_name="", callback_url=None):
    """
    Initialize a Chapa payment
    """
    if callback_url is None:
        callback_url = getattr(settings, "BASE_URL", "http://localhost:8000") + "/api/payments/verify/"

    payload = {
        "amount": amount,
        "currency": currency,
        "email": email,
        "tx_ref": tx_ref,
        "first_name": first_name,
        "last_name": last_name,
        "callback_url": callback_url
    }

    try:
        response = requests.post(
            f"{CHAPA_BASE_URL}/transaction/initialize",
            headers=HEADERS,
            json=payload,
            timeout=10
        )
        return response.json()
    except requests.Timeout:
        return {"status": "error", "message": "Request timed out"}
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}


def verify_payment(tx_ref):
    """
    Verify the status of a Chapa payment
    """
    try:
        response = requests.get(
            f"{CHAPA_BASE_URL}/transaction/verify/{tx_ref}",
            headers=HEADERS,
            timeout=10
        )
        return response.json()
    except requests.Timeout:
        return {"status": "error", "message": "Request timed out"}
    except requests.RequestException as e:
        return {"status": "error", "message": str(e)}
