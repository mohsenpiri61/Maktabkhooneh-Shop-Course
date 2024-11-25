import requests
import json
from django.conf import settings
from django.contrib.sites.models import Site

def get_domain():
    from django.contrib.sites.models import Site
    return Site.objects.get_current().domain

def get_protocol():
    # Determine the protocol based on the SECURE_SSL_REDIRECT setting
    return'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'

class ZarinPalSandbox:
    _payment_request_url = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
    _payment_verify_url = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
    _payment_page_url = "https://sandbox.zarinpal.com/pg/StartPay/"
    _callback_url = "http://redreseller.com/verify"

    def __init__(self, merchant_id=settings.MERCHANT_ID):
        self.merchant_id = merchant_id

    def payment_request(self, amount, description="پرداختی کاربر"):
        print(f"Requesting payment for amount with coupon: {amount}")
        payload = {
            "merchant_id": self.merchant_id,
            "amount": str(amount),
            "callback_url": self._callback_url,
            "description": description,
            "metadata": {
                "mobile": "09195523234",
                "email": "info.davari@gmail.com"
            }
        }
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", self._payment_request_url, headers=headers, data=json.dumps(payload))       

        response_dict = json.loads(response.text)
        if "data" in response_dict and response_dict["data"]:
            return response_dict["data"]["authority"]
        else:
            raise ValueError(f"Payment request failed: {response_dict['errors']}")

    def payment_verify(self,amount,authority):
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "authority": authority
        }
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(self._payment_verify_url, headers=headers, data=json.dumps(payload))
        return response.json()

    def generate_payment_url(self,authority):
        return f"{self._payment_page_url}{authority}"