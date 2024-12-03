from django.views.generic import View
from .models import PaymentModel, PaymentStatusType
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from .zarinpal_client import ZarinPalSandbox
from order.models import OrderModel, OrderStatusType


class PaymentVerifyView(View):
    
    
    def payment_failed(self, order):
        """بازگرداندن موجودی محصولات در صورت شکست پرداخت"""
        order.status = OrderStatusType.CANCELED.value
        
        for item in order.order_items.all():
            print(f"The count of product before rollingback for {item.product.title} is: {item.product.stock}")
            print(f"The count of product after rollingback for {item.product.title} must be: { item.quantity}")
            item.product.stock += item.quantity
            item.product.save()
            print(f"The count of product after rollingback for {item.product.title} is: { item.product.stock}")         
        order.save()
        
        
    def get(self, request, *args, **kwargs):
        # دریافت پارامترهای ارسال شده به مرورگر
        authority_id = request.GET.get("Authority")
        status = request.GET.get("Status")

        # بازیابی اطلاعات پرداخت
        payment_obj = get_object_or_404(PaymentModel, authority_id=authority_id)
        
        # مقداردهی به زرین پال و دریافت پاسخ از زرین پال به منظور اطمینان از موفقیت آمیز بودن پرداخت
        zarin_pal = ZarinPalSandbox() 
        response = zarin_pal.payment_verify(int(payment_obj.amount), payment_obj.authority_id)
        
        # استخراج داده‌های پاسخ
        data = response.get("data", {})
        code = data.get("code", -51)
        ref_id = data.get("ref_id")

        # ثبت اطلاعات پرداخت در مدل
        payment_obj.ref_id = ref_id
        payment_obj.response_code = code
        payment_obj.status = PaymentStatusType.success.value if code in {
            100, 101} else PaymentStatusType.failed.value
        payment_obj.response_json = response
        payment_obj.save()
     
        
        # مشاهده اطلاعات نمونه در کنسول (payment_obj)
        for field in payment_obj._meta.get_fields():
            # فیلدهایی که مستقیم نیستند (یعنی رابطه معکوس هستند) را رد کن
            if not field.concrete:
                continue
            field_name = field.name
            field_value = getattr(payment_obj, field_name, None)
            print(f"{field_name}: {field_value}")

        # بروزرسانی وضعیت سفارش مرتبط
        order = OrderModel.objects.get(payment=payment_obj)
        if payment_obj.response_code in {100, 101}:
            order.status = OrderStatusType.PAID.value
        else:
            # تنظیم وضعیت سفارش به شکست خورده
            self.payment_failed(order)

        order.save()       
        return redirect(reverse_lazy("order:completed") if code in {100, 101} else reverse_lazy("order:failed"))
