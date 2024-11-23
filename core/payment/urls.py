from django.urls import path,re_path
from . import views

app_name = "payment"

urlpatterns = [
    path('payment/callback/', views.PaymentCallbackView.as_view(), name='payment_callback'),


]