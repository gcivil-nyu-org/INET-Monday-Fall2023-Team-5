# routing.py in myapp directory

from django.urls import path
from . import consumers

# Define WebSocket URL patterns
websocket_urlpatterns = [
    path("ws/game_progress/<game_id>/", consumers.GameConsumer.as_asgi()),
]
