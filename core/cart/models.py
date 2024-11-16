from django.db import models
from order.models import CouponModel

# Create your models here.
class CartModel(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    coupon = models.ForeignKey(CouponModel, null=True, blank=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

    def calculate_total_price(self):
        total_price = sum(item.product.get_price() * item.quantity for item in self.cart_items.all())
        if self.coupon:
            discount = total_price * (self.coupon.discount_percent / 100)
            total_price -= discount
        return total_price


class CartItemModel(models.Model):
    cart = models.ForeignKey(CartModel, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey('shop.ProductModel', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=0)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.title} - {self.cart.id}"
