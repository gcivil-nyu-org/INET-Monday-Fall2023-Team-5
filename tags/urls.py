from django.urls import path
from .views import tag_view

urlpatterns = [
    path('', tag_view, name='tag_view'),
]