from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from .forms import SubmitReviewForm
from .models import ReviewModel
from django.contrib import messages
from order.models import OrderStatusType, OrderItemModel

class SubmitReviewView(LoginRequiredMixin, CreateView):
    http_method_names = ["post"]
    model = ReviewModel
    form_class = SubmitReviewForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        
        
        product = form.cleaned_data['product']
        print('sffdsf',  product)
        # بررسی اینکه کاربر محصول را خریداری کرده است یا خیر
        has_purchased = OrderItemModel.objects.filter(
            order__user=self.request.user,
            product=product, order__status=OrderStatusType.PAID.value).exists()
        
        
        if not has_purchased:
            messages.error(self.request, "شما این محصول را نخریده‌اید و نمی‌توانید دیدگاهی ثبت کنید.")
            return redirect(self.request.META.get('HTTP_REFERER'))
        form.save()
        
        messages.success(self.request, "دیدگاه شما با موفقیت ثبت شد و پس از بررسی نمایش داده خواهد شد")
        return redirect(reverse_lazy('shop:product-detail', kwargs={"slug": product.slug}))

    def form_invalid(self, form):
        # برای مشاهده خطاهایی که ممکن است در زمان ارسال فرم رخ بدهد
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return redirect(self.request.META.get('HTTP_REFERER'))

    def get_queryset(self):
       
        return ReviewModel.objects.filter(user=self.request.user)
