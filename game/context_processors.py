from game.models import GameSession
import logging

logger = logging.getLogger(__name__)

def game_session_processor(request):
    if request.user.is_authenticated:
        try:
            game_session = GameSession.objects.filter(
                # Your conditions here
            ).latest('id')
            game_session_url = game_session.get_absolute_url()
            logger.info(f"Game session URL: {game_session_url}")
            return {'game_session_url': game_session_url}
        except GameSession.DoesNotExist:
            logger.info("No game session found")
            return {'game_session_url': None}
    return {}
