from django.urls import path
from .views import SignUpView, edit_profile, profile_updated, activate_account, confirmation_required
from django.views.generic.base import TemplateView
from django.urls import path, re_path

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("edit_profile/", edit_profile, name="edit_profile"),
    path("profile_updated/", profile_updated, name="profile_updated"),
    path("confirm/<str:uidb64>/<str:token>/", activate_account, name="activate_account"),
    path("confirmation_required/", confirmation_required, name="confirmation_required"),
    # re_path(r'^confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', 
    #     activate_account, 
    #     name='activate'),
]