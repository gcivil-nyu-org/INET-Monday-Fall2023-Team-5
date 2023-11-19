from django.contrib import messages
from django.db import transaction
from .forms import AnswerForm, EmojiReactForm, NarrativeChoiceForm
from .models import (
    Player,
    GameSession,
    GameTurn,
    Word,
    Question,
)
from django.shortcuts import redirect, render
from django.views import View
import random
from collections import defaultdict
from django.contrib.auth.models import User
from accounts.models import Match
from django.db.models import Q


def initiate_game_session(request):
    if request.method == "POST":
        # Fetching the logged-in user
        user1 = request.user

        # Retrieving the selected user's username from the POST request
        selected_username = request.POST.get("selected_user")
        user2 = User.objects.get(username=selected_username)

        # Create a new game session and save it
        game_session = GameSession()
        game_session.save()

        # Create players for the game session
        player_A = Player.objects.create(user=user1, game_session=game_session)
        player_B = Player.objects.create(user=user2, game_session=game_session)

        # Assigning players to the game session
        game_session.playerA = player_A
        game_session.playerB = player_B
        game_session.save()

        # Initialize the game and redirect to the GameProgressView
        game_session.initialize_game()
        game_session.save()
        return redirect("game_progress", game_id=game_session.game_id)
    else:
        # Define a list of the usernames that can be selected
        selectable_usernames = [
            "prof_test",
            "ta_test",
            "test1",
            "test2",
            "test3",
            "test4",
            "test5",
        ]

        # Fetch the users with the specified usernames and not the logged-in user
        selectable_users = User.objects.filter(
            username__in=selectable_usernames
        ).exclude(id=request.user.id)

        # Pass the list of selectable users to the template
        return render(
            request,
            "initiate_game_session.html",
            {"selectable_users": selectable_users},
        )


class GameProgressView(View):
    template_name = "game_progress.html"

    def get(self, request, *args, **kwargs):
        game_id = kwargs["game_id"]
        try:
            game_session = GameSession.objects.get(game_id=game_id)
        except GameSession.DoesNotExist:
            messages.error(request, "Game session not found.")
            return redirect("end_game_session", game_id=game_id)

        if game_session.state == GameSession.ENDED:
            messages_by_sender = retrieve_messages_from_log(game_session.gameLog)
            if game_session.state == GameSession.ENDED:
                return render(
                    request,
                    "end_game_session.html",
                    {
                        "game_id": game_id,
                        "messages_by_sender": dict(messages_by_sender),
                    },
                )
        else:
            player = request.user.player
            # Check if the user is a participant of the game session
            if player not in [game_session.playerA, game_session.playerB]:
                messages.error(
                    request, "You are not a participant of this game session."
                )
                return redirect("home")

            chat_messages_for_session = game_session.gameLog.chat_messages.all()

            # Context that is common to all states
            context = {
                "game_session": game_session,
                "chat_messages": chat_messages_for_session,
                "active_player": game_session.current_game_turn.get_active_player(),
                "playerC": player.character_name,
            }

            # Add state-specific context
            turn = game_session.current_game_turn

            if turn.state == GameTurn.SELECT_QUESTION:
                # Fetch unasked questions
                unasked_questions = Question.objects.exclude(
                    id__in=game_session.asked_questions.values_list("id", flat=True)
                )
                # Randomly select 3 questions
                random_questions = random.sample(
                    list(unasked_questions), min(len(unasked_questions), 3)
                )
                context.update({"random_questions": random_questions})

            elif turn.state == GameTurn.ANSWER_QUESTION:
                words = Word.objects.all()
                tags_answer = [word.word for word in words]
                context.update({"tags_answer": tags_answer})
                context.update(
                    {
                        "answer_form": AnswerForm(),
                    }
                )

            elif turn.state == GameTurn.REACT_EMOJI:
                context.update(
                    {
                        "emoji_form": EmojiReactForm(),
                    }
                )
            elif turn.state == GameTurn.NARRATIVE_CHOICES:
                choice_made = False
                if (
                    player == game_session.playerA
                    and turn.player_a_narrative_choice_made is True
                ):
                    choice_made = True
                elif (
                    player == game_session.playerB
                    and turn.player_b_narrative_choice_made is True
                ):
                    choice_made = True

                context.update(
                    {
                        "narrative_form": NarrativeChoiceForm(),
                        "choice_made": choice_made,
                    }
                )
            elif game_session.current_game_turn.state == GameTurn.MOON_PHASE:
                turn = game_session.current_game_turn
                context.update(
                    {
                        "moon_phase": turn.get_moon_phase(),
                    }
                )

            return render(request, self.template_name, context)


def end_game_session(request, game_id):
    try:
        game_session = GameSession.objects.get(game_id=game_id)
        if (
            request.user not in [game_session.playerA.user, game_session.playerB.user]
            and not request.user.is_staff
        ):
            messages.error(request, "You are not a participant of this game session.")
            return redirect("home")

        messages_by_sender = retrieve_messages_from_log(game_session.gameLog)

        with transaction.atomic():  # Start a database transaction
            # Lock the game session row
            game_session = GameSession.objects.select_for_update().get(game_id=game_id)
            # User checks if GameSession's state is ENDED
            if game_session.state != GameSession.ENDED:
                # Retrieve the players (users) involved in the game session
                user1 = game_session.playerA.user
                user2 = game_session.playerB.user
                
                game_session.end_session()
                game_session.save()

                # Query and delete the match involving these two users
                Match.objects.filter(
                    (Q(user1=user1) & Q(user2=user2)) | (Q(user1=user2) & Q(user2=user1))
                ).delete()

        return render(
            request,
            "end_game_session.html",
            {"game_id": game_id, "messages_by_sender": dict(messages_by_sender)},
        )

    except GameSession.DoesNotExist:
        messages.error(request, "Game session not found.")
        return redirect("initiate_game_session")


def retrieve_messages_from_log(game_log):
    messages_by_sender = defaultdict(list)
    for message in game_log.chat_messages.all():
        messages_by_sender[message.sender].append(message)
    return messages_by_sender
