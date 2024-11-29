from django.views.generic import View
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CheckOutForm
from cart.models import CartModel
from .models import OrderModel, OrderItemModel, UserAddressModel
from payment.sepal import SepalPaymentGateway
from .permissions import HasCustomerAccessPermission


class OrderCheckOutView(LoginRequiredMixin, HasCustomerAccessPermission, FormView):
    template_name = "order/checkout.html"
    form_class = CheckOutForm
    success_url = reverse_lazy('order:completed')

    def get_form_kwargs(self):
        """اضافه کردن درخواست کاربر به آرگومان‌های فرم."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        """عملیات مورد نیاز در صورت معتبر بودن فرم."""
        user = self.request.user
        cleaned_data = form.cleaned_data
        address = cleaned_data['address_id']
        coupon = cleaned_data['coupon']

        # ایجاد سفارش
        cart = CartModel.objects.get(user=user)
        order = self._create_order(user, address, coupon)

        # افزودن آیتم‌های سفارش و پاک کردن سبد خرید
        self._create_order_items(order, cart)
        self._clear_cart(cart)

        # هدایت به درگاه پرداخت
        payment_url = self._create_payment_url(order)
        return redirect(payment_url)

    def _create_order(self, user, address, coupon):
        """ایجاد و ذخیره سفارش جدید."""
        order = OrderModel.objects.create(
            user=user,
            address=address,
            coupon=coupon
        )
        order.total_price = order.calculate_total_price()
        order.save()
        return order

    def _create_order_items(self, order, cart):
        """اضافه کردن آیتم‌های سفارش از سبد خرید."""
        for item in cart.cart_items.all():
            OrderItemModel.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.get_price(),
            )

    def _clear_cart(self, cart):
        """پاک کردن آیتم‌های سبد خرید و ریست کردن نشست سبد."""
        cart.cart_items.all().delete()
        from cart.cart import CartSession  # فرض بر این است که کلاس مدیریت سبد خرید در `utils` است
        CartSession(self.request.session).clear()

    def _create_payment_url(self, order):
        """ایجاد لینک پرداخت سپال."""
        try:
            payment_url = SepalPaymentGateway(api_key="test").payment_request(
                amount=order.calculate_total_price(),
                invoice_number=str(order.id),
                description=f"پرداخت برای سفارش شماره {order.id}",
                # payer_name=order.user.get_full_name(),
                # payer_mobile=order.user.profile.mobile,
                # payer_email=order.user.email
            )
            return payment_url
        except ValueError as e:
            # مدیریت خطا و هدایت به صفحه تسویه حساب
            messages.error(self.request, str(e))
            return reverse("order:checkout")

    def form_invalid(self, form):
        """مدیریت فرم نامعتبر."""
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """اضافه کردن داده‌های مورد نیاز به زمینه صفحه."""
        context = super().get_context_data(**kwargs)
        cart = CartModel.objects.get(user=self.request.user)
        total_price = cart.calculate_total_price()

        context.update({
            "addresses": UserAddressModel.objects.filter(user=self.request.user),
            "total_price": total_price,
            "total_tax": round((total_price * 9) / 100),
        })
        return context


class ValidateCouponView(LoginRequiredMixin, HasCustomerAccessPermission, View):

    def post(self, request, *args, **kwargs):
        code = request.POST.get("code")
        user = request.user

        try:
            # استفاده از CouponModel برای دریافت کد تخفیف
            coupon = CouponModel.objects.get(code=code)

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
            cart.save()

            total_price = cart.calculate_total_price()

            return JsonResponse({
                "message": "کد تخفیف لغو شد",
                "total_price": round(total_price)
            }, status=200)

        except CartModel.DoesNotExist:
            return JsonResponse({"message": "سبد خرید شما خالی است"}, status=400)
