
import requests
import base64
from datetime import datetime
from django.conf import settings


def get_access_token():
    url = (
        f"{settings.MPESA_BASE_URL}"
        "/oauth/v1/generate?grant_type=client_credentials"
    )

    credentials = (
        f"{settings.MPESA_CONSUMER_KEY}:"
        f"{settings.MPESA_CONSUMER_SECRET}"
    )

    encoded_credentials = base64.b64encode(
        credentials.encode()
    ).decode("utf-8")

    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    return response.json()["access_token"]


def stk_push(phone_number, amount, callback_url, account_reference="UOKFEES"):
    access_token = get_access_token()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password_string = (
        f"{settings.MPESA_SHORTCODE}"
        f"{settings.MPESA_PASSKEY}"
        f"{timestamp}"
    )

    password = base64.b64encode(
        password_string.encode()
    ).decode("utf-8")

    phone_number = str(phone_number).strip()

    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]
    elif phone_number.startswith("+254"):
        phone_number = phone_number[1:]

    url = f"{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": "UOK School Fees"
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.json()
