# routing.py in myapp directory

from django.urls import path
from . import consumers

# Define WebSocket URL patterns
websocket_urlpatterns = [
    path("ws/some_path/", consumers.MyConsumer.as_asgi()),
]
