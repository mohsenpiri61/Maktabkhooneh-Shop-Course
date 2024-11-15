from django import forms
from order.models import CouponModel


class CouponForm(forms.ModelForm):
    expiration_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}))

    class Meta:
        model = CouponModel
        fields = [
            "code",
            "discount_percent",
            "max_limit_usage",
            "expiration_date"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')  
        # print(vars(instance)) //note that print(instance) gives coupon's code because def __str__() was defined 'return self.code'

        if instance and instance.used_by.exists():  # اگر کد تخفیف توسط کاربران استفاده شده باشد ، فیلدهای کد و درصد غیرفعال می شوند.
            self.fields['code'].disabled = True
            self.fields['discount_percent'].disabled = True
        
        self.fields['code'].widget.attrs['class'] = 'form-control'
        self.fields['discount_percent'].widget.attrs['class'] = 'form-control'
        self.fields['max_limit_usage'].widget.attrs['class'] = 'form-control'
