from django.contrib import messages
from django.db import transaction
from .forms import (
    AnswerForm,
    EmojiReactForm,
    NarrativeChoiceForm,
    CharacterSelectionForm,
    MoonSignInterpretationForm,
)
from .models import (
    Player,
    GameSession,
    GameTurn,
    Word,
    Question,
    Character,
    MoonSignInterpretation,
)
from django.shortcuts import redirect, render
from django.views import View
import random
from collections import defaultdict
from django.contrib.auth.models import User
from django.db.models import Q
from accounts.models import Match
from django.http import JsonResponse


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
                # Check if both players are not None
                if game_session.playerA and game_session.playerB:
                    user1 = game_session.playerA.user
                    user2 = game_session.playerB.user

                    # Query and delete the match involving these two users
                    Match.objects.filter(
                        (Q(user1=user1) & Q(user2=user2))
                        | (Q(user1=user2) & Q(user2=user1))
                    ).delete()

                game_session.end_session()
                game_session.save()

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


class CharacterCreationView(View):
    template_name = "character_creation.html"

    def get(self, request, *args, **kwargs):
        game_id = kwargs["game_id"]
        try:
            game_session = GameSession.objects.get(game_id=game_id)
            if game_session.state != GameSession.CHARACTER_CREATION:
                # If the game is not in the character creation state,
                # redirect to the game progress
                return redirect(game_session.get_absolute_url())

            # Proceed with character creation form since the
            # game is in the correct state
            form = CharacterSelectionForm()
            return render(
                request, self.template_name, {"form": form, "game_id": game_id}
            )

        except GameSession.DoesNotExist:
            # Handle the error, e.g., by showing a message or redirecting
            messages.error(request, "Game session not found.")
            return redirect(
                "game:game_list"
            )  # Redirect to a view where the user can see a list of games

    def post(self, request, *args, **kwargs):
        game_id = kwargs["game_id"]
        try:
            game_session = GameSession.objects.get(game_id=game_id)
            if game_session.state != GameSession.CHARACTER_CREATION:
                # If the game is not in the character creation state,
                # redirect to the game progress
                return redirect("moon_sign_interpretation", game_id=game_id)

            form = CharacterSelectionForm(request.POST)
            if form.is_valid():
                # The form is valid, save the character for the player
                player, _ = Player.objects.get_or_create(
                    user=request.user, defaults={"game_session": game_session}
                )
                player.character = form.cleaned_data["character"]
                player.save()

                # Fetch players associated with this game session
                players = Player.objects.filter(game_session=game_session)

                # Ensure there are exactly two players
                if players.count() == 2:
                    playerA, playerB = players.all()
                    if playerA.character and playerB.character:
                        # game_session.start_regular_turn()
                        # game_session.save()
                        game_session.start_moon_sign_creation()
                        game_session.save()
                        return redirect("moon_sign_interpretation", game_id=game_id)
                else:
                    print(
                        "The game session state remains in CHARACTER_CREATION as there "
                        "are not exactly 2 players to transition to MOON_PHASE."
                    )

                return redirect("moon_sign_interpretation", game_id=game_id)

        except GameSession.DoesNotExist:
            # Handle the error, e.g., by showing a message or redirecting
            messages.error(request, "Game session not found.")
            return redirect("game:game_list")

        # Re-render the form with errors if it's not valid
        return render(request, self.template_name, {"form": form, "game_id": game_id})


def get_character_details(request):
    character_id = request.GET.get("id")
    if not character_id:
        return JsonResponse({"error": "No character ID provided"}, status=400)

    try:
        character = Character.objects.get(id=character_id)
        return JsonResponse(
            {
                "name": character.name,
                "description": character.description,
                "image_url": character.image.url if character.image else "",
            }
        )
    except Character.DoesNotExist:
        return JsonResponse({"error": "Character not found"}, status=404)


class MoonSignInterpretationView(View):
    template_name = "moon_sign_interpretation.html"

    def get(self, request, *args, **kwargs):
        game_id = kwargs["game_id"]
        try:
            # Ensure the game session is in the right state
            form = MoonSignInterpretationForm()
            return render(
                request, self.template_name, {"form": form, "game_id": game_id}
            )

        except GameSession.DoesNotExist:
            messages.error(request, "Game session not found.")
            return redirect("game:game_list")

    def post(self, request, *args, **kwargs):
        game_id = kwargs["game_id"]
        form = MoonSignInterpretationForm(request.POST)
        if form.is_valid():
            game_session = GameSession.objects.get(game_id=game_id)
            player, _ = Player.objects.get_or_create(
                user=request.user, defaults={"game_session": game_session}
            )
            # player.first_quarter = form.cleaned_data['first_quarter']
            player.save()
            # Process the form data here
            moon_sign_interpretation = MoonSignInterpretation(
                first_quarter=form.cleaned_data["first_quarter"],
                first_quarter_reason=form.cleaned_data["first_quarter_reason"],
                full_moon=form.cleaned_data["full_moon"],
                full_moon_reason=form.cleaned_data["full_moon_reason"],
                last_quarter=form.cleaned_data["last_quarter"],
                last_quarter_reason=form.cleaned_data["last_quarter_reason"],
                new_moon=form.cleaned_data["new_moon"],
                new_moon_reason=form.cleaned_data["new_moon_reason"],
            )
            moon_sign_interpretation.save()
            # Transition the game session to the regular turn
            try:
                players = Player.objects.filter(game_session=game_session)

                # Ensure there are exactly two players
                if players.count() == 2:
                    if game_session.state == GameSession.MOON_SIGN_INTERPRETATION:
                        game_session.start_regular_turn()
                        game_session.save()
                        return redirect("game_progress", game_id=game_id)

            except GameSession.DoesNotExist:
                messages.error(request, "Game session not found.")
                return redirect("game:game_list")

            return redirect("game_progress", game_id=game_id)

        # Re-render the form with errors if it's not valid
        return render(request, self.template_name, {"form": form, "game_id": game_id})
