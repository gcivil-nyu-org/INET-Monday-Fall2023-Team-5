from django.urls import path
from . import views

urlpatterns = [
    path("game-session/<int:game_session_id>/", views.game_view, name="game_view"),
]
