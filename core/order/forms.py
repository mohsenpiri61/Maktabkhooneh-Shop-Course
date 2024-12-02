from django import forms
from order.models import UserAddressModel,CouponModel
from django.utils import timezone

class CheckOutForm(forms.Form):
    address_id = forms.IntegerField(required=True)
    coupon = forms.CharField(required=False)
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
    def clean_address_id(self):
        """ تضمین می کند که  آدرس به همان کاربری تعلق دارد که درخواست را ارسال کرده است (بررسی مالکیت)"""
        address_id = self.cleaned_data.get('address_id')

        user = self.request.user  
        try:
            address = UserAddressModel.objects.get(id=address_id, user=user)
        except UserAddressModel.DoesNotExist:
            raise forms.ValidationError("این آدرس به شما تعلق ندارد.")

        return address
    
    def clean_coupon(self):
        """ تضمین می‌کند که در لحظه پردازش نهایی داده‌ها، کد تخفیف هنوز معتبر است"""
        code = self.cleaned_data.get('coupon')
        if code == "":   # or if not code :
            return None
        
        user = self.request.user  
        try:
            coupon = CouponModel.objects.get(code=code)
        except CouponModel.DoesNotExist:
            raise forms.ValidationError("کد تخفیف اشتباه است")
        if coupon:

            if coupon.used_by.count() >= coupon.max_limit_usage:
                raise forms.ValidationError("محدودیت در تعداد استفاده")

            if coupon.expiration_date and coupon.expiration_date < timezone.now():
                raise forms.ValidationError("کد تخفیف منقضی شده است")

            if user in coupon.used_by.all():
                raise forms.ValidationError("این کد تخفیف قبلا توسط شما استفاده شده است")

        return coupon
    
    # def clean_product_stock(self):
    #     """بررسی موجودی محصولات سبد خرید"""
    #     cleaned_data = super().clean()
    #     user = self.request.user

    #     cart = CartModel.objects.filter(user=user).first()
    #     if not cart or not cart_items.exists():
    #         raise forms.ValidationError("سبد خرید شما خالی است.")

    #     for item in cart_items.all():
    #         if item.product.stock < item.quantity:
    #             raise forms.ValidationError(
    #                 f"موجودی محصول {item.product.title} کافی نیست. (موجودی فعلی: {item.product.stock})"
    #             )
                
    #     print('sfdfsfsdfds')        
    #     return cleaned_data
