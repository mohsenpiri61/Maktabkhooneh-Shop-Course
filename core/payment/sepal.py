import requests
from django.shortcuts import redirect
from decimal import Decimal
from django.conf import settings



class SepalPaymentGateway:
    _request_url = "https://sepal.ir/api/sandbox/request.json"
    _payment_url = "https://sepal.ir/sandbox/payment/"
    _verify_url = "https://sepal.ir/api/sandbox/verify.json"
    _callback_url = "http://127.0.0.1:8000/"
    
    def __init__(self, api_key):
        self.api_key = api_key

    def payment_request(self, amount, invoice_number="123", description="پرداخت سفارش", payer_name=None, payer_mobile=None, payer_email=None):
        """
        ارسال درخواست پرداخت به سپال.
        """
        payload = {
            "apiKey": self.api_key,
            "amount": str(amount),
            "callbackUrl": self._callback_url,
            "invoiceNumber": invoice_number,
            "payerName": payer_name,
            "payerMobile": payer_mobile,
            "payerEmail": payer_email,
            "description": description,
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(self._request_url, headers=headers, json=payload, verify=False)
        response_dict = response.json()
        
        if response_dict.get("status") == 1:
            # پرداخت موفق ایجاد شده است
            return response_dict["paymentNumber"]
        else:
            raise ValueError(f"خطا در ایجاد پرداخت: {response_dict.get('message', 'خطای ناشناخته')}")

    def payment_verify(self, payment_number, invoice_number):
        """
        بررسی وضعیت پرداخت.
        """
        payload = {
            "apiKey": self.api_key,
            "paymentNumber": payment_number,
            "invoiceNumber": str(invoice_number),
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(self._verify_url, headers=headers, json=payload, verify=False)
        return response.json()

    def generate_payment_url(self, payment_number):
        """
        تولید لینک پرداخت.
        """
        return f"{self._payment_url}{payment_number}"