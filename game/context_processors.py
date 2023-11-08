from game.models import GameSession

""" def game_session_processor(request):
    # Logic to get the most recent game session URL for the current user
    if request.user.is_authenticated:
        try:
            # Assuming you have a method to get the latest game session for the user
            game_session = GameSession.objects.filter(
                playerA__user=request.user
            ).latest('id')
            return {'game_session_url': game_session.get_absolute_url()}
        except GameSession.DoesNotExist:
            # Handle the case where there is no game session
            return {'game_session_url': None}
    return {} """

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

