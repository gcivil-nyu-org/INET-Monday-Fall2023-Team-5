"""
URL configuration for roleplaydate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from accounts.views import home
from django.conf import settings  # Import settings
from django.conf.urls.static import static  # Import static
from django.http import HttpResponse
from django.core.management import call_command


def reset_likes(request):
    call_command("reset_likes")
    return HttpResponse("Likes have been reset.")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("game/", include("game.urls")),
    path("", home, name="home"),
    path("api/reset-likes/", reset_likes),
    path("tags/", include("tags.urls")),
]

# Add the following line to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
