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
        from .utils import CartSession  # فرض بر این است که کلاس مدیریت سبد خرید در `utils` است
        CartSession(self.request.session).clear()

    def _create_payment_url(self, order):
        """ایجاد لینک پرداخت سپال."""
        try:
            payment_url = SepalPaymentGateway(api_key="test").payment_request(
                amount=order.calculate_total_price(),
                invoice_number=str(order.id),
                description=f"پرداخت برای سفارش شماره {order.id}",
                payer_name=order.user.get_full_name(),
                payer_mobile=order.user.profile.mobile,
                payer_email=order.user.email
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
