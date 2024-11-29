import requests
from django.shortcuts import redirect
from decimal import Decimal
from django.conf import settings



class SepalPaymentGateway:
    API_KEY = "test"  # در حالت تست
    REQUEST_URL = "https://sepal.ir/api/sandbox/request.json"
    PAYMENT_URL = "https://sepal.ir/sandbox/payment/"
    VERIFY_URL = "https://sepal.ir/api/sandbox/verify.json"
    CALLBACK_URL = "http://127.0.0.1:8000/order/verify/"
    
    @staticmethod
    def create_payment(order):
        """ایجاد درخواست پرداخت در سپال"""
        
        params = {
            "apiKey": SepalPaymentGateway.API_KEY,
            "amount": str(order.get_price()),  # مبلغ پرداخت به ریال
            "callbackUrl": CALLBACK_URL,
            "invoiceNumber": "123",  # شماره فاکتور
            # "payerName": order.user.get_full_name(),  # نام پرداخت‌کننده
            # "payerMobile": order.user.profile.mobile,  # موبایل پرداخت‌کننده
            # "payerEmail": order.user.email,  # ایمیل پرداخت‌کننده
            # "description": f"پرداخت برای سفارش شماره {order.id}",
        }

        try:
            response = requests.post(
                SepalPaymentGateway.REQUEST_URL, 
                json=params,
                headers={"Content-Type": "application/json"},
                verify=False
            )
            data = response.json()
            if data.get("status") == 1:
                # ایجاد آدرس پرداخت
                payment_url = f"{SepalPaymentGateway.PAYMENT_URL}{data.get('paymentNumber')}"
                return payment_url
            else:
                raise ValueError(data.get("message", "خطای نامشخص در ایجاد پرداخت"))
        except Exception as e:
            raise ValueError(f"خطا در ارتباط با درگاه سپال: {e}")
            print(paymentNumber)
    @staticmethod
    def verify_payment(payment_number, amount):
        """تایید وضعیت پرداخت"""
        params = {
            "apiKey": SepalPaymentGateway.API_KEY,
            "paymentNumber": payment_number,
            "invoiceNumber": str(amount),
        }

        try:
            response = requests.post(
                SepalPaymentGateway.VERIFY_URL, 
                json=params,
                headers={"Content-Type": "application/json"},
                verify=False
            )
            data = response.json()
            return data
        except Exception as e:
            raise ValueError(f"خطا در تایید پرداخت سپال: {e}")
