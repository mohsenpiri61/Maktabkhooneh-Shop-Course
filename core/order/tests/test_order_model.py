import pytest
from decimal import Decimal
from order.models import OrderModel, OrderItemModel, CouponModel, UserAddressModel
from accounts.models import User

@pytest.fixture
def create_user(db):
    """ایجاد یک کاربر تستی."""
    return User.objects.create(email="test@example.com", password="testpassword")

@pytest.fixture
def create_address(db, create_user):
    """ایجاد آدرس تستی."""
    return UserAddressModel.objects.create(
        user=create_user,
        address="خیابان آزادی، پلاک ۱",
        state="تهران",
        city="تهران",
        zip_code="12345"
    )

@pytest.fixture
def create_coupon(db):
    """ایجاد یک کوپن تستی."""
    return CouponModel.objects.create(
        code="DISCOUNT20",
        discount_percent=20,
        max_limit_usage=10
    )

@pytest.fixture
def create_order(db, create_user, create_address, create_coupon):
    """ایجاد یک سفارش تستی."""
    return OrderModel.objects.create(
        user=create_user,
        address=create_address,
        total_price=100000,
        coupon=create_coupon
    )

@pytest.fixture
def create_order_item(db, create_order):
    """ایجاد آیتم‌های سفارش تستی."""
    return OrderItemModel.objects.create(
        order=create_order,
        product_id=1,  # فرض می‌کنیم محصولی با این ID وجود دارد
        quantity=2,
        price=50000
    )

def test_order_total_price(create_order, create_order_item):
    """تست محاسبه قیمت کل."""
    order = create_order
    assert order.calculate_total_price() == 100000, "قیمت کل باید 100000 باشد"

def test_order_discounted_price(create_order):
    """تست قیمت نهایی با تخفیف."""
    order = create_order
    discounted_price = order.get_price()
    assert discounted_price == 80000, "قیمت نهایی باید با تخفیف 80000 باشد"

def test_order_without_coupon(create_order):
    """تست قیمت نهایی بدون کوپن تخفیف."""
    order = create_order
    order.coupon = None
    assert order.get_price() == 100000, "قیمت بدون کوپن باید برابر با قیمت کل باشد"
