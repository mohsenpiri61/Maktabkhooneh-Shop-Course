from django.http import HttpResponse
from django.views.generic import (
    TemplateView,
    FormView,
    View
)
from django.contrib.auth.mixins import LoginRequiredMixin
from order.permissions import HasCustomerAccessPermission
from order.forms import CheckOutForm
from cart.models import CartModel, CartItemModel
from order.models import OrderModel, OrderItemModel, CouponModel, UserAddressModel
from django.urls import reverse_lazy
from cart.cart import CartSession
from decimal import Decimal
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import redirect
from payment.zarinpal_client import ZarinPalSandbox
from payment.models import PaymentModel


class OrderCheckOutView(LoginRequiredMixin, HasCustomerAccessPermission, FormView):
    template_name = "order/checkout.html"
    form_class = CheckOutForm
    success_url = reverse_lazy('order:completed')

    def get_form_kwargs(self):
        kwargs = super(OrderCheckOutView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        cleaned_data = form.cleaned_data
        address = cleaned_data['address_id']
        # coupon = cleaned_data['coupon']
        print(address)
        cart = CartModel.objects.get(user=user)
        order = self.create_order(address)

        self.create_order_items(order, cart)
        self.clear_cart(cart)

        total_price = order.calculate_total_price()
        #self.apply_coupon(coupon, order, user, total_price)
        order.save()
        return redirect(self.create_payment_url(order))

    def create_payment_url(self, order):
        zarinpal = ZarinPalSandbox()
        response = zarinpal.payment_request(order.get_price())
        payment_obj = PaymentModel.objects.create(
            authority_id=response.get("Authority"),
            amount=order.get_price(),
        )
        order.payment = payment_obj
        order.save()
        return zarinpal.generate_payment_url(response.get("Authority"))

    def create_order(self, address):
        return OrderModel.objects.create(
            user=self.request.user,
            address=address
        )

    def create_order_items(self, order, cart):
        for item in cart.cart_items.all():
            OrderItemModel.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.get_price(),
            )

    def clear_cart(self, cart):
        cart.cart_items.all().delete()
        CartSession(self.request.session).clear()

    
    # def apply_coupon(self, coupon, order, user, total_price):
    #     if coupon:
    #         order.coupon = coupon
    #         coupon.used_by.add(user)
    #         coupon.save()
    #     order.total_price = total_price


    def form_invalid(self, form):
        return super().form_invalid(form)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = CartModel.objects.get(user=self.request.user)
        context["addresses"] = UserAddressModel.objects.filter(
            user=self.request.user)
        total_price = cart.calculate_total_price()
        context["total_price"] = total_price
        context["total_tax"] = round((total_price * 9)/100)
        return context


class OrderCompletedView(LoginRequiredMixin, HasCustomerAccessPermission, TemplateView):
    template_name = "order/completed.html"
    
class OrderFailedView(LoginRequiredMixin, HasCustomerAccessPermission, TemplateView):
    template_name = "order/failed.html"


class ValidateCouponView(LoginRequiredMixin, HasCustomerAccessPermission, View):

    def post(self, request, *args, **kwargs):
        code = request.POST.get("code")
        user = request.user

        try:
            
            coupon = OrderModel.objects.get(code=code)

            # بررسی اعتبار کد تخفیف
            if coupon.expiration_date and coupon.expiration_date < timezone.now():
                return JsonResponse({"message": "کد تخفیف منقضی شده است"}, status=400)

            if coupon.used_by.count() >= coupon.max_limit_usage:
                return JsonResponse({"message": "محدودیت استفاده از کد تخفیف به پایان رسیده است"}, status=400)

            if user in coupon.used_by.all():
                return JsonResponse({"message": "شما قبلاً از این کد تخفیف استفاده کرده‌اید"}, status=400)

            # اعمال کد تخفیف
            cart = CartModel.objects.get(user=self.request.user)

            # محاسبه قیمت جدید
            total_price = cart.calculate_total_price()
            discount_price = total_price * (coupon.discount_percent / 100)
            final_price = total_price - discount_price
            print('fdfdff', total_price, discount_price, final_price)
            return JsonResponse({
                "message": "کد تخفیف اعمال شد",
                "total_price": round(final_price),
                "discount": round(discount_price)
            }, status=200)

        except CouponModel.DoesNotExist:
            return JsonResponse({"message": "کد تخفیف معتبر نیست"}, status=400)



class CancelCouponView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            cart = CartModel.objects.get(user=request.user)
            #cart.coupon = None
            cart.save()

            total_price = cart.calculate_total_price()

            return JsonResponse({
                "message": "کد تخفیف لغو شد",
                "total_price": round(total_price)
            }, status=200)

        except CartModel.DoesNotExist:
            return JsonResponse({"message": "سبد خرید شما خالی است"}, status=400)
