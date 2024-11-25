

from decimal import Decimal
import sys
sys.path.append('/app')

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")  # نام پروژه خود را جایگزین کنید

import django
django.setup()

from order.models import OrderModel, OrderItemModel, CouponModel, UserAddressModel
from accounts.models import User


def create_test_user():
    """ایجاد یک کاربر آزمایشی"""
    return User.objects.create_user(email="test@example.com", password="testpassword")


def create_test_address(user):
    """ایجاد یک آدرس آزمایشی برای کاربر"""
    return UserAddressModel.objects.create(
        user=user,
        address="خیابان آزادی، پلاک ۱",
        state="تهران",
        city="تهران",
        zip_code="12345"
    )


def create_test_coupon():
    """ایجاد یک کوپن آزمایشی"""
    return CouponModel.objects.create(
        code="DISCOUNT20",
        discount_percent=20,
        max_limit_usage=10
    )


def create_test_order(user, address, coupon):
    """ایجاد یک سفارش آزمایشی"""
    return OrderModel.objects.create(
        user=user,
        address=address,
        total_price=100000,
        coupon=coupon
    )


def create_test_order_item(order):
    """ایجاد آیتم‌های سفارش آزمایشی"""
    return OrderItemModel.objects.create(
        order=order,
        product_id=1,  # فرض بر این است که محصولی با ID مشخص وجود دارد
        quantity=2,
        price=50000
    )


def test_order_calculate_total_price(order, order_item):
    """تست محاسبه قیمت کل سفارش"""
    assert order.calculate_total_price() == 100000, "محاسبه قیمت کل سفارش نادرست است"


def test_order_get_price_with_coupon(order):
    """تست محاسبه قیمت سفارش با کوپن"""
    assert order.get_price() == 80000, "محاسبه قیمت با کوپن نادرست است"


def test_order_get_price_without_coupon(order):
    """تست محاسبه قیمت سفارش بدون کوپن"""
    order.coupon = None
    order.save()
    assert order.get_price() == 100000, "محاسبه قیمت بدون کوپن نادرست است"


def main():
    # ایجاد داده‌های تستی
    user = create_test_user()
    address = create_test_address(user)
    coupon = create_test_coupon()
    order = create_test_order(user, address, coupon)
    order_item = create_test_order_item(order)

    # اجرای تست‌ها
    try:
        test_order_calculate_total_price(order, order_item)
        print("تست محاسبه قیمت کل سفارش موفقیت‌آمیز بود")

        test_order_get_price_with_coupon(order)
        print("تست محاسبه قیمت سفارش با کوپن موفقیت‌آمیز بود")

        test_order_get_price_without_coupon(order)
        print("تست محاسبه قیمت سفارش بدون کوپن موفقیت‌آمیز بود")
    except AssertionError as e:
        print(f"خطا در تست: {e}")


if __name__ == "__main__":
    main()
