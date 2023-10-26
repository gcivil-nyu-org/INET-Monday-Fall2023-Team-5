from django.urls import path
from .views import 
from django.contrib.auth.views import LoginView  # override the default login view
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)

urlpatterns = [
    path("about/", about, name="about"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("edit_profile/", edit_profile, name="edit_profile"),
    path("profile_updated/", profile_updated, name="profile_updated"),
    path(
        "confirm/<str:uidb64>/<str:token>/", activate_account, name="activate_account"
    ),  # This is the pattern we'll use
    path("confirmation_required/", confirmation_required, name="confirmation_required"),
    path("profile/", view_profile, name="view_profile"),
    path("browse/", browse_profiles, name="browse_profiles"),
    path("account/", account, name="account"),
    path(
        "login/",
        LoginView.as_view(template_name="accounts/registration/login.html"),
        name="login",
    ),
    path(
        "password_reset/",
        PasswordResetView.as_view(
            template_name="accounts/registration/password_reset_form.html"
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        PasswordResetDoneView.as_view(
            template_name="accounts/registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="accounts/registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        PasswordResetCompleteView.as_view(
            template_name="accounts/registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
