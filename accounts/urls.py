from django.urls import path
from .views import *

urlpatterns = [
    path("about/", about, name="about"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("edit_profile/", edit_profile, name="edit_profile"),
    path("profile_updated/", profile_updated, name="profile_updated"),
    path("confirm/<str:uidb64>/<str:token>/", activate_account, name="activate_account"), # This is the pattern we'll use
    path("confirmation_required/", confirmation_required, name="confirmation_required"),
    path("profile/", view_profile, name="view_profile"),
    path("browse/", browse_profiles, name="browse_profiles"),
]
