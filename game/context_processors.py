from game.models import GameSession
import logging
from django.db.models import Q


logger = logging.getLogger(__name__)


def game_session_processor(request):
    if request.user.is_authenticated:
        try:
            # Filter GameSessions where the user is either playerA or playerB
            game_session = GameSession.objects.filter(
                Q(playerA__user=request.user) | Q(playerB__user=request.user),
                is_active=True,  # Assuming you want only active game sessions
            ).latest(
                "id"
            )  # Assuming 'id' is an auto-incrementing that reflects creation order

            game_session_url = game_session.get_absolute_url()
            logger.info(
                f"Game session URL for user {request.user.username}: {game_session_url}"
            )
            return {"game_session_url": game_session_url}

        except GameSession.DoesNotExist:
            logger.info(f"No game session found for user {request.user.username}")
            return {"game_session_url": None}

    # Return an empty dictionary if the user is not authenticated
    return {}
