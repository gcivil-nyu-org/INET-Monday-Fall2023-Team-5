from django.urls import path, re_path
from game import consumers
from game.consumers import TestConsumer

# Define WebSocket URL patterns
websocket_urlpatterns = [
    re_path(
        r"^ws/game_progress/(?P<game_id>[a-fA-F0-9\-]{36})/$",
        consumers.GameConsumer.as_asgi(),
    ),
    re_path(r"^ws/test/$", TestConsumer.as_asgi()),
]
