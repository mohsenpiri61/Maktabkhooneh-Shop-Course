import sys
import os
import django

# اضافه کردن مسیر پروژه به sys.path
sys.path.append('/app')  # مسیر پروژه داخل کانتینر

# تنظیم متغیر محیطی برای تنظیمات Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# راه‌اندازی Django
django.setup()

from django.contrib.auth import get_user_model
from order.models import OrderModel, OrderItemModel, CouponModel, UserAddressModel
from cart.models import CartModel, CartItemModel
from payment.zarinpal_client import ZarinPalSandbox
from payment.models import PaymentModel
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

def create_order_and_payment(user_email, address_id, coupon_code=None):
    try:
        # دریافت کاربر از ایمیل
        user = User.objects.get(email=user_email)

        # دریافت سبد خرید کاربر
        cart = CartModel.objects.get(user=user)

        # دریافت آدرس کاربر
        # فرض بر این است که آدرس قبلا ایجاد شده و شناسه آن در درخواست آمده است
        address = UserAddressModel.objects.get(id=address_id, user=user)

        # دریافت کوپن تخفیف در صورت موجود بودن
        coupon = None
        if coupon_code:
            coupon = CouponModel.objects.get(code=coupon_code)

        # ایجاد سفارش جدید
        order = OrderModel.objects.create(user=user, address=address, coupon=coupon)

        # اضافه کردن آیتم‌های سبد خرید به سفارش
        for cart_item in cart.cart_items.all():
            OrderItemModel.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.get_price(),
            )

        # محاسبه قیمت کل سفارش
        order.total_price = order.calculate_total_price()
        order.save()

        # ایجاد لینک پرداخت از طریق زرین‌پال
        zarinpal = ZarinPalSandbox()
        response = zarinpal.payment_request(order.get_price())

        # ثبت پرداخت در مدل Payment
        payment_obj = PaymentModel.objects.create(
            authority_id=response.get("authority"),
            amount=order.get_price(),
        )
        order.payment = payment_obj
        order.save()

        # برگشت لینک پرداخت
        payment_url = zarinpal.generate_payment_url(response.get("authority"))
        print(f"Payment URL: {payment_url}")

        return order, payment_url

    except User.DoesNotExist:
        print(f"User with email {user_email} does not exist.")
    except CartModel.DoesNotExist:
        print(f"Cart for user {user_email} does not exist.")
    except CouponModel.DoesNotExist:
        print(f"Coupon {coupon_code} does not exist.")
    except Exception as e:
        print(f"Error: {e}")
    
    return None, None

if __name__ == "__main__":
    # اطلاعات ورودی برای کاربر و آدرس
    user_email = 'sara@yahoo.com'  # ایمیل کاربر
    address_id = 2  # شناسه آدرس کاربر
    coupon_code = 'd10'  # کد تخفیف

    # فراخوانی تابع ایجاد سفارش و دریافت لینک پرداخت
    order, payment_url = create_order_and_payment(user_email, address_id, coupon_code)

    if order:
        print(f"Order created successfully. Total Price: {order.total_price}")
        print(f"Redirect to payment: {payment_url}")
    else:
        print("Failed to create order.")
