from game.models import GameSession, Player
import logging
from django.db.models import Q
from django.urls import reverse


logger = logging.getLogger(__name__)


def game_session_processor(request):
    if request.user.is_authenticated:
        try:
            # Filter GameSessions where the user is either playerA or playerB
            game_session = GameSession.objects.filter(
                Q(playerA__user=request.user) | Q(playerB__user=request.user),
                is_active=True,
            ).latest("id")
            # Check if the player has a character
            player = Player.objects.get(user=request.user)
            print("Game session state: " + game_session.state)
            if game_session.state == game_session.CHARACTER_CREATION:
                if player.character:
                    game_session_url = game_session.get_absolute_url()
                elif game_session.state == game_session.MOON_SIGN_INTERPRETATION:
                    game_session_url = reverse(
                        "game:moon_sign_interpretation",
                        kwargs={"game_id": game_session.game_id},
                    )
                else:
                    game_session_url = reverse(
                        "game:character_creation",
                        kwargs={"game_id": game_session.game_id},
                    )
            else:
                game_session_url = game_session.get_absolute_url()

            return {"game_session_url": game_session_url}

        except (GameSession.DoesNotExist, Player.DoesNotExist):
            return {"game_session_url": None}

    return {}
