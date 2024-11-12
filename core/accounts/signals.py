from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
from .models import FailedLoginAttempt


@receiver(user_login_failed)
def login_failed_handler(sender, credentials, request, **kwargs):
    email = credentials.get("username", "Unknown")  
    ip_address = request.META.get("REMOTE_ADDR", "Unknown")
    FailedLoginAttempt.objects.create(email=email, ip_address=ip_address)
    print("Login Failed", email, ip_address)