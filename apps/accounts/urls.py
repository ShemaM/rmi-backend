from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("me/", views.me, name="me"),
    path("verify-email/", views.verify_email, name="verify-email"),
    path("password-reset/", views.password_reset_request, name="password-reset"),
    path("password-reset/confirm/", views.password_reset_confirm, name="password-reset-confirm"),
]
