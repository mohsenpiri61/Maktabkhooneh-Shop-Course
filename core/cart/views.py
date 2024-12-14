from typing import Any
from django.shortcuts import render
from django.views.generic import View, TemplateView
from django.http import JsonResponse
from shop.models import ProductModel, ProductStatusType
from .cart import CartSession
import json


class SessionAddProductView(View):

    def post(self, request, *args, **kwargs):
        cart = CartSession(request.session)
        
        # بررسی می‌کنیم که آیا داده‌ای ارسال شده است یا خیر.
        if not request.body:
            return JsonResponse({"error": "داده‌ای ارسال نشده است."}, status=400)

        try:
            data = json.loads(request.body)  # تلاش برای تبدیل داده‌های JSON
        except json.JSONDecodeError:
            return JsonResponse({"error": "فرمت داده‌های ارسال شده نامعتبر است."}, status=400)
        
        product_id = data.get("product_id")
        quantity = int(data.get("quantity", 1))  # تعداد انتخابی، پیش‌فرض 1
        
        # دریافت محصول
        try:
            product_obj =  ProductModel.objects.get(id=product_id, status=ProductStatusType.publish.value)
        except ProductModel.DoesNotExist:
            return JsonResponse({"error": "محصول یافت نشد."}, status=404)
         # بررسی موجودی محصول
        if quantity > product_obj.stock:
            return JsonResponse({"error": f"موجودی محصول '{product_obj.title}' کافی نیست  ."}, status=400)
       
        # اضافه کردن یا بروزرسانی تعداد محصول در سبد خرید
        cart.add_or_update_product_quantity(product_id, quantity)
  

        # ادغام سبد خرید session با دیتابیس (در صورت احراز هویت کاربر)
        if request.user.is_authenticated:
            cart.merge_session_cart_in_db(request.user)
        return JsonResponse({"cart": cart.get_cart_dict(), "total_quantity": cart.get_total_quantity(), "message": "محصول به سبد خرید اضافه شد."})


class SessionRemoveProductView(View):

    def post(self, request, *args, **kwargs):
        cart = CartSession(request.session)
        product_id = request.POST.get("product_id")
        if product_id:
            cart.remove_product(product_id)
        if request.user.is_authenticated:
            cart.merge_session_cart_in_db(request.user)
        return JsonResponse({"cart": cart.get_cart_dict(), "total_quantity": cart.get_total_quantity()})


class SessionUpdateProductQuantityView(View):

    def post(self, request, *args, **kwargs):
        cart = CartSession(request.session)
        product_id = request.POST.get("product_id")
        quantity = request.POST.get("quantity")
        if product_id and quantity:
            cart.update_product_quantity(product_id, quantity)
        if request.user.is_authenticated:
            cart.merge_session_cart_in_db(request.user)
        return JsonResponse({"cart": cart.get_cart_dict(), "total_quantity": cart.get_total_quantity()})


class CartSummaryView(TemplateView):
    template_name = "cart/cart-summary.html"

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        cart = CartSession(self.request.session)
        cart_items = cart.get_cart_items()
        context["cart_items"] = cart_items
        context["total_quantity"] = cart.get_total_quantity()
        context["total_payment_price"] = cart.get_total_payment_amount()
        return context
