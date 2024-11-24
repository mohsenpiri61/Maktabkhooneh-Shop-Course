import os
import django
import sys

# تنظیم فایل تنظیمات پروژه Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from order.models import OrderModel, OrderItemModel, CouponModel, UserAddressModel
from accounts.models import User
from decimal import Decimal

# ساخت داده‌های آزمایشی
def create_test_data():
    # ایجاد کاربر آزمایشی
    user = User.objects.create(email="test@example.com", password="testpassword")

    # ایجاد آدرس کاربر
    address = UserAddressModel.objects.create(
        user=user,
        address="خیابان آزادی، پلاک ۱",
        state="تهران",
        city="تهران",
        zip_code="12345"
    )

    # ایجاد کوپن تخفیف
    coupon = CouponModel.objects.create(
        code="DISCOUNT20",
        discount_percent=20,
        max_limit_usage=10
    )

    # ایجاد سفارش
    order = OrderModel.objects.create(
        user=user,
        address=address,
        total_price=100000,
        coupon=coupon
    )

    # ایجاد آیتم‌های سفارش
    OrderItemModel.objects.create(order=order, product_id=1, quantity=2, price=50000)

    return order


# تست عملکرد
def test_order_model():
    # ایجاد داده‌های آزمایشی
    order = create_test_data()

    # بررسی قیمت کل
    total_price = order.calculate_total_price()
    print(f"Total Price (Before Discount): {total_price}")

    # بررسی قیمت با تخفیف
    discounted_price = order.get_price()
    print(f"Total Price (After Discount): {discounted_price}")

    # بدون کوپن تخفیف
    order.coupon = None
    print(f"Total Price (Without Coupon): {order.get_price()}")


if __name__ == "__main__":
    test_order_model()
