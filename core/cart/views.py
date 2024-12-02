from typing import Any
from django.shortcuts import render
from django.views.generic import View, TemplateView
from django.http import JsonResponse
from shop.models import ProductModel, ProductStatusType
from .cart import CartSession


class SessionAddProductView(View):

    def post(self, request, *args, **kwargs):
        cart = CartSession(request.session)
        product_id = request.POST.get("product_id")
        product_obj =  ProductModel.objects.get(id=product_id, status=ProductStatusType.publish.value)
        
         # بررسی موجودی محصول
        if product_obj.stock <= 0:
            return JsonResponse({"error": f"محصول '{product_obj.title}' موجود نیست."}, status=400)
       
        # اضافه کردن محصول به سبد خرید 
        product_obj_added = cart.add_product(product_id, product_obj.stock)
        if not product_obj_added:
            return JsonResponse({"error": f"موجودی کافی برای محصول '{product_obj.title}' وجود ندارد."}, status=400)

        # ادغام سبد خرید session با دیتابیس (در صورت احراز هویت کاربر)
        if request.user.is_authenticated:
            cart.merge_session_cart_in_db(request.user)
        return JsonResponse({"cart": cart.get_cart_dict(), "total_quantity": cart.get_total_quantity()})


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
