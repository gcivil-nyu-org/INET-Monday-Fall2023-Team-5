from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import F
from .forms import QuestionSelectForm, AnswerForm, EmojiReactForm, NarrativeChoiceForm
from .models import (
    Player,
    GameSession,
    Question,
    GameStep,
    ChatMessage,
    NarrativeChoice,
)

from django.shortcuts import redirect, render
from django.views import View


def initiate_game_session(request):
    if request.method == "POST":
        # Fetching two users to start the game
        user1 = User.objects.get(username="admin5")
        user2 = User.objects.get(username="admin6")

        game_session = GameSession()
        game_session.save()
        # Creating players
        player1 = Player.objects.create(user=user1, game_session=game_session)
        player2 = Player.objects.create(user=user2, game_session=game_session)

        # Creating game session
        game_session.playerA = player1
        game_session.playerB = player2
        game_session.save()

        # Redirecting to GameProgressView
        return redirect("game_progress", game_id=game_session.game_id)

    return render(request, "initiate_game.html")


class GameProgressView(View):
    template_name = "game_progress.html"

    def get(self, request, *args, **kwargs):
        game_id = kwargs["game_id"]
        try:
            game_session = GameSession.objects.get(game_id=game_id)
        except GameSession.DoesNotExist:
            messages.error(request, "Game session not found.")
            # Redirect to some other page when the game session does not exist
            return redirect("end_game_session", game_id=game_id)

        current_turn = game_session.current_game_turn
        is_active_player = request.user == current_turn.active_player.user
        chat_messages_for_session = ChatMessage.objects.filter(
            game_session=game_session
        )
        # Add Moon Sign Phase check:
        moon_phase = self.get_moon_phase(current_turn.turn_number)
        if moon_phase:
            context = {
                "game_session": game_session,
                "current_turn": current_turn,
                "moon_phase": moon_phase,
                "is_active_player": is_active_player,
                "chat_messages": chat_messages_for_session,
            }
            return render(request, self.template_name, context)
        else:  # It's a regular turn
            user_has_made_choice = NarrativeChoice.objects.filter(
                game_session=current_turn.parent_game,
                game_turn=current_turn,
                player=request.user.player,
            ).exists()

            context = {
                "game_session": game_session,
                "current_turn": current_turn,
                "is_active_player": is_active_player,
                "question_form": QuestionSelectForm(),
                "answer_form": AnswerForm(),
                "emoji_form": EmojiReactForm(),
                "narrative_form": NarrativeChoiceForm(),
                "chat_messages": chat_messages_for_session,
                "user_has_made_choice": user_has_made_choice,
            }

            return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        game_id = kwargs["game_id"]
        try:
            game_session = GameSession.objects.get(game_id=game_id)
        except GameSession.DoesNotExist:
            # Redirect to some other page when the game session does not exist
            return redirect("end_game_session", game_id=game_id)
        current_turn = game_session.current_game_turn
        moon_phase = self.get_moon_phase(current_turn.turn_number)
        if moon_phase:
            return self.handle_moon_phase(request, current_turn, game_id)

        regular_turn_handler_map = {
            GameStep.P1_SELECT_QUESTION: self.handle_select_question,
            GameStep.P2_ANSWER_QUESTION: self.handle_answer_question,
            GameStep.P1_REACT_EMOJI: self.handle_react_emoji,
            GameStep.P2_SELECT_QUESTION: self.handle_select_question,
            GameStep.P1_ANSWER_QUESTION: self.handle_answer_question,
            GameStep.P2_REACT_EMOJI: self.handle_react_emoji,
            GameStep.AWAITING_NARRATIVE_CHOICES: self.handle_awaiting_narrative_choices,
        }

        handler = regular_turn_handler_map.get(current_turn.child_step.step)
        if handler:
            return handler(request, current_turn, game_id)
        else:
            raise NotImplementedError(
                f"Handler for step {current_turn.child_step.step} not implemented"
            )

        # Separate handlers for each game phase

    @staticmethod
    def handle_moon_phase(request, current_turn, game_id):
        # Handle any Moon Sign Phase specific actions, decisions, or updates
        if request.method == "POST":
            moon_meaning = request.POST.get("moon_meaning", "").strip()
            if moon_meaning:
                # Here, create a new chat message and add it to the chat for this game session
                chat_message = ChatMessage(
                    sender=request.user,
                    text=moon_meaning,
                    game_session=current_turn.parent_game,
                )
                chat_message.save()

                # Implement any other logic as needed.
            current_turn.moon_meanings_submitted = F("moon_meanings_submitted") + 1
            current_turn.save()
            current_turn.refresh_from_db()

            if current_turn.moon_meanings_submitted == 2:
                current_turn.turn_number += 1
                current_turn.moon_meanings_submitted = 0
                current_turn.save()
            current_turn.switch_active_player()

        return redirect("game_progress", game_id=game_id)

    @staticmethod
    def handle_select_question(request, current_turn, game_id):
        selected_question_id = request.POST.get("question")
        selected_question = Question.objects.get(id=selected_question_id)

        if not selected_question:
            # If not selected, inform the user and redirect back
            messages.error(request, "Please select a question.")
            return redirect("game_progress", game_id)

        ChatMessage.objects.create(
            game_session=current_turn.parent_game,
            sender=str(current_turn.active_player.user),
            text=str(selected_question),
        )
        current_turn.child_step.advance_step()
        current_turn.save()
        return redirect("game_progress", game_id)

    @staticmethod
    def handle_answer_question(request, current_turn, game_id):
        # Retrieve the player's answer from POST data
        player_answer = request.POST.get("answer")

        if not player_answer:
            # Handle cases where the answer is not provided
            messages.error(request, "Please provide a non-empty answer.")
            return redirect("game_progress", game_id)

        # Store the player's answer as a message
        ChatMessage.objects.create(
            game_session=current_turn.parent_game,
            sender=str(current_turn.active_player.user),
            text=player_answer,
        )

        # Advance to the next step
        current_turn.child_step.advance_step()
        current_turn.save()

        # Redirect back to the game progress page
        return redirect("game_progress", game_id)

    @staticmethod
    def handle_react_emoji(request, current_turn, game_id):
        # Retrieve the selected emoji from POST data
        selected_emoji = request.POST.get("emoji")

        if not selected_emoji:
            # If no emoji is selected, inform the user and redirect back
            messages.error(request, "Please select an emoji to react with.")
            return redirect("game_progress", game_id)

        # Fetch the latest message for the current game session to add the reaction
        latest_message = ChatMessage.objects.filter(
            game_session=current_turn.parent_game
        ).last()

        if latest_message:
            latest_message.reaction = selected_emoji
            latest_message.save()

        # Advance to the next game step
        current_turn.child_step.advance_step()
        current_turn.save()

        # Redirect back to the game progress page
        return redirect("game_progress", game_id)

    @staticmethod
    def handle_awaiting_narrative_choices(request, current_turn, game_id):
        # Retrieve the selected narrative choice from POST data
        selected_narrative = request.POST.get("narrative")

        # Check if the user has already made a narrative choice for this game session
        existing_choice = NarrativeChoice.objects.filter(
            game_session=current_turn.parent_game,
            game_turn=current_turn,
            player=request.user.player,
        ).exists()

        if existing_choice:
            messages.info(
                request,
                "You've already made your narrative choice for this turn. Please wait for the other player.",
            )
            return redirect("game_progress", game_id)

        if not selected_narrative:
            messages.error(request, "Please select a narrative choice.")
            return redirect("game_progress", game_id)

        current_player = Player.objects.get(user=request.user)
        NarrativeChoice.objects.create(
            game_session=current_turn.parent_game,
            game_turn=current_turn,
            player=current_player,
            choice=selected_narrative,
        )
        # We use Django's F() to perform an atomic update to the database and
        # prevent a race condition
        current_turn.narrative_choices_made = F("narrative_choices_made") + 1
        current_turn.save()
        current_turn.refresh_from_db()

        if current_turn.narrative_choices_made == 2:
            current_turn.child_step.advance_step()
            current_turn.save()
            NarrativeChoice.objects.filter(
                game_session=current_turn.parent_game
            ).delete()
            current_turn.save()
            current_turn.narrative_choices_made = 0
            current_turn.save()
        # Redirect back to the game progress page
        return redirect("game_progress", game_id)

    @staticmethod
    def get_moon_phase(turn_number):
        # If you decide to add more phases or adjust the turn for each phase, modify this dictionary.
        moon_phases = {
            3: "new moon",
            7: "first quarter",
            11: "full",
            15: "last quarter",
        }
        return moon_phases.get(turn_number)


def end_game_session(request, game_id):
    try:
        game_session = GameSession.objects.get(game_id=game_id)
        if (
            request.user not in [game_session.playerA.user, game_session.playerB.user]
            and not request.user.is_staff
        ):
            # You can return an error message or redirect to another page if the user is not authorized
            return redirect(
                "home"
            )  # or another suitable view name with an error message
        game_session.end_session()
        messages.success(request, "Game session ended successfully.")
    except GameSession.DoesNotExist:
        messages.error(request, "Game session not found.")
    return redirect("initiate_game")
