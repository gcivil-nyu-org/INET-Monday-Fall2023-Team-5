from django.contrib import messages
from django.contrib.auth.models import User
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


from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


@login_required
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
        return redirect("game_progress", game_id=game_session.game_id)
    else:
        # Fetch the list of users that can be selected as partners
        # Excluding the logged-in user from the list
        selectable_users = User.objects.exclude(id=request.user.id)

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

        player = request.user.player
        # Check if the user is a participant of the game session
        if player not in [game_session.playerA, game_session.playerB]:
            messages.error(request, "You are not a participant of this game session.")
            return redirect("home")

        chat_messages_for_session = game_session.chat_messages.all()

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


"""
    def post(self, request, *args, **kwargs):
        game_id = kwargs["game_id"]
        player = request.user.player
        try:
            game_session = GameSession.objects.get(game_id=game_id)
        except GameSession.DoesNotExist:
            return redirect("end_game_session", game_id=game_id)

        current_game_turn = game_session.current_game_turn
        # Get the data from the POST request
        data = request.POST

        # Call the appropriate method on the FSM based on the current state
        try:
            if current_game_turn.state == GameTurn.SELECT_QUESTION:
                selected_question_id = data.get("question")
                current_game_turn.select_question(selected_question_id, player)
                current_game_turn.save()
                game_session.asked_questions.add(
                    Question.objects.get(id=selected_question_id)
                )
                game_session.save()

            elif current_game_turn.state == GameTurn.ANSWER_QUESTION:
                answer = data.get("answer")
                current_game_turn.answer_question(answer, player)
                current_game_turn.save()

            elif current_game_turn.state == GameTurn.REACT_EMOJI:
                current_game_turn.react_with_emoji(data.get("emoji"), player)
                current_game_turn.save()

            elif current_game_turn.state == GameTurn.NARRATIVE_CHOICES:
                current_game_turn.make_narrative_choice(data.get("narrative"), player)
                current_game_turn.save()

            elif current_game_turn.state == GameTurn.MOON_PHASE:
                current_game_turn.write_message_about_moon_phase(
                    data.get("moon_meaning"), player
                )
                current_game_turn.save()
        except Exception as e:
            # Handle any other exceptions that might occur.
            # Update players or send a message to inform them of the error.
            messages.error(request, str(e))
            return redirect("game_progress", game_id=game_id)

        return redirect("game_progress", game_id=game_id)
"""


# def end_game_session(request, game_id):
#     try:
#         game_session = GameSession.objects.get(game_id=game_id)
#         if (
#             request.user not in [game_session.playerA.user, game_session.playerB.user]
#             and not request.user.is_staff
#         ):
#             messages.error(request, "You are not a participant of this game session.")
#             return redirect(
#                 "home"
#             )  # or another suitable view name with an error message
#         game_session.end_session()
#         messages.success(request, "Game session ended successfully.")
#     except GameSession.DoesNotExist:
#         messages.error(request, "Game session not found.")
#     return redirect("initiate_game_session")


def end_game_session(request, game_id):
    try:
        game_session = GameSession.objects.get(game_id=game_id)
        if (
            request.user not in [game_session.playerA.user, game_session.playerB.user]
            and not request.user.is_staff
        ):
            messages.error(request, "You are not a participant of this game session.")
            return redirect("home")

        # Fetch chat messages for the session
        chat_messages_for_session = game_session.chat_messages.all().order_by(
            "timestamp"
        )
        # Organize messages by sender
        messages_by_sender = defaultdict(list)
        for message in chat_messages_for_session:
            name = message.sender
            messages_by_sender[name].append(message)

        game_session.end_session()
        messages.success(request, "Game session ended successfully.")

        return render(
            request,
            "initiate_game_session.html",
            {"game_id": game_id, "messages_by_sender": dict(messages_by_sender)},
        )

    except GameSession.DoesNotExist:
        messages.error(request, "Game session not found.")
        return redirect("initiate_game_session")
