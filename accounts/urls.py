# accounts/urls.py
from django.urls import path
from .views import SignUpView, edit_profile
from django.views.generic.base import TemplateView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("edit_profile/", edit_profile, name="edit_profile"),
    path("profile_updated/", TemplateView.as_view(template_name="profile_updated.html"), name="profile_updated"),
]