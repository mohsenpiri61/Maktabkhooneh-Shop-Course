from django.contrib.auth import views as auth_views
from accounts.forms import AuthenticationForm, SignUpForm
from django.urls import reverse_lazy
from .models import User
from django.contrib import messages
from django.shortcuts import render
from django.views.generic import CreateView
from .tasks import send_reset_password_email
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    form_class = AuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        if user.is_superuser:
            success_message = "شما با دسترسی ادمین وارد شده‌اید."
        elif user.is_staff:
            success_message = "شما با موفقیت وارد شده‌اید."
        else:
            success_message = "شما با موفقیت وارد شده‌اید."

        messages.success(self.request, success_message)
        return response

    def form_invalid(self, form):
        form.add_error(None, "ایمیل یا رمز عبور شما نادرست است.")
        return super().form_invalid(form)
    
    
    
class LogoutView(auth_views.LogoutView):
    pass


class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')

    # overriding form_valid for invalid email address and creating token and sending email
    def form_valid(self, form):
        email = form.cleaned_data.get('email')

        # Checking for existance of email in the database 
        user_email = User.objects.filter(email=email).first()
        if not user_email:
            messages.error(self.request, '.ایمیل وارد شده در سیستم موجود نیست')
            return render(self.request, self.template_name, {'form': form})


        else:
            # Generate password recovery token
            uid = urlsafe_base64_encode(force_bytes(user_email.pk))
            token = default_token_generator.make_token(user_email)

            # Create a reset link (both reset_link is usable)
            # reset_link = self.request.build_absolute_uri(reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))
            reset_link = f"{self.request.scheme}://{self.request.get_host()}/accounts/reset/{uid}/{token}/"

            from_email = 'webmasterl@localhost'
            recipient_list = [email]
            subject = 'Reset your password'
            message = f"Hi {user_email.email},\n\nTo reset your password, click the link below:\n{reset_link}\n\nIf you did not request a password reset, please ignore this email."
            send_reset_password_email.delay(subject, message, from_email, recipient_list)
            messages.success(self.request, '.لینک بازنشانی رمز عبور به ایمیل شما ارسال شد')
            return super().form_valid(form)


class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


class SignUpView(CreateView):
    model = User
    form_class = SignUpForm
    template_name = 'accounts/page-signup-simple.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        messages.success(self.request, "The new user was created successfully")
        return super().form_valid(form)
