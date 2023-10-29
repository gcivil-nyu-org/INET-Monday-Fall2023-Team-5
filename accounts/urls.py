from django.urls import path
from .views import (
    about,
    home,
    SignUpView,
    edit_profile,
    profile_updated,
    activate_account,
    confirmation_required,
    view_profile,
    view_single_profile,
    browse_profiles,
    account,
)

from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)

urlpatterns = [
    path("", home, name="home"),
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
    path("logout/", LogoutView.as_view(next_page="home"), name="logout"),
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
    path("profile/<int:profile_id>/", view_single_profile, name="view_single_profile"),
]
