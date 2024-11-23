from django.views import View
from django.shortcuts import redirect
from django.contrib import messages

class PaymentCallbackView(View):
    """مدیریت بازگشت از درگاه پرداخت سپال"""

    def get(self, request, *args, **kwargs):
        authority = request.GET.get("authority")
        status = request.GET.get("status")

        # بررسی وضعیت پرداخت
        try:
            payment = PaymentModel.objects.get(authority_id=authority)
            if status == "success":
                verified = self.verify_payment(authority, payment.amount)
                if verified:
                    messages.success(request, "پرداخت با موفقیت انجام شد.")
                    return redirect("order:completed")
            messages.error(request, "پرداخت ناموفق بود.")
        except PaymentModel.DoesNotExist:
            messages.error(request, "پرداخت یافت نشد.")

        return redirect("order:checkout")

