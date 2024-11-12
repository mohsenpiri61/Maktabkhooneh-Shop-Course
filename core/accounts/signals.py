from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
from .models import User
from django.utils import timezone
from django.contrib import messages



@receiver(user_login_failed)    
def login_failed_handler(sender, credentials, request, **kwargs):
    email = credentials.get("username")  
    ip_address = request.META.get("REMOTE_ADDR", "Unknown")

    try:
        user = User.objects.get(email=email)
        print(user)
    except User.DoesNotExist:
        return  messages.warning(request, "کاربری با ایمیل وارد شده وجود ندارد.")
    # محاسبه بازه زمانی
    time_threshold = timezone.now() - timezone.timedelta(seconds=20)
    if user.last_failed_login and user.last_failed_login < time_threshold:
        user.failed_login_attempts = 0  # ریست تلاش‌ها پس از بازه زمانی

    # افزایش تعداد تلاش‌ها و تنظیم زمان آخرین تلاش ناموفق
    user.failed_login_attempts += 1
    user.last_failed_login = timezone.now()
    user.save()

    # هشدار دادن پس از تعداد تلاش‌های ناموفق
    if user.failed_login_attempts >= 3:
        # هشدار دادن به کاربر (مثلاً با نمایش پیام یا ایمیل هشدار)
        messages.warning(request, f"هشدار: تلاش‌های ورود ناموفق برای {email} از حد مجاز عبور کرده است \n {user.failed_login_attempts}تلاش ناموفق \n لطفا بعد از 20 ثانیه دیگر اقدام کنید")