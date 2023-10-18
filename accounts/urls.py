from django.urls import path
from .views import *
from django.views.generic.base import TemplateView

urlpatterns = [
    path("about/", about, name="about"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("edit_profile/", edit_profile, name="edit_profile"),
    path("profile_updated/", profile_updated, name="profile_updated"),
]