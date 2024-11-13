from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
from .models import User
from django.utils import timezone
from django.contrib import messages
from django.db.models.signals import post_save
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.utils.encoding import force_bytes


@receiver(user_login_failed)
def login_failed_handler(sender, credentials, request, **kwargs):
    email = credentials.get("username")
    ip_address = request.META.get("REMOTE_ADDR", "Unknown")

    try:
        user = User.objects.get(email=email)
        print(user)
    except User.DoesNotExist:
        return messages.warning(request, "کاربری با ایمیل وارد شده وجود ندارد.")
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
        messages.warning(request,
                         f"هشدار: تلاش‌های ورود ناموفق برای {email} از حد مجاز عبور کرده است \n {user.failed_login_attempts}تلاش ناموفق \n لطفا بعد از 20 ثانیه دیگر اقدام کنید")


@receiver(post_save, sender=User)
def send_activation_email(sender, instance, created, **kwargs):
    if created and not instance.is_active:
        uid = urlsafe_base64_encode(force_bytes(instance.pk))
        token = account_activation_token.make_token(instance)

        relative_link = reverse('accounts:activate', kwargs={'uidb64': uid, 'token': token})
        activation_link = f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}{relative_link}"

        subject = 'فعال‌سازی حساب کاربری'
        message = render_to_string('accounts/activation_email.html', {
            'activation_link': activation_link,
            'user': instance,
        })
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email])
