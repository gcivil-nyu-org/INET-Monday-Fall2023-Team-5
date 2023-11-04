from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
import uuid

from django_fsm import FSMField, transition


class Player(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE
    )  # if the user is deleted, the 'Player' is deleted.
    word_pool = models.ManyToManyField("Word", blank=True)
    question_pool = models.ManyToManyField("Question", blank=True)

    game_session = models.ForeignKey(
        "GameSession", related_name="game_players", on_delete=models.CASCADE
    )

    def save(self, *args, **kwargs):
        if not self.game_session:
            raise ValidationError(
                "A player must be associated with a GameSession before saving."
            )
        super(Player, self).save(*args, **kwargs)

        # Update current_game_turn's current_player if it's None
        if not self.game_session.current_game_turn.active_player:
            self.game_session.current_game_turn.active_player = self
            self.game_session.current_game_turn.save()

    def delete(self, *args, **kwargs):
        # Update the related GameSession's is_active field
        self.game_session.set_game_inactive()

        # Now, actually delete the player
        super(Player, self).delete(*args, **kwargs)


def generate_game_id():
    return str(uuid.uuid4())


def generate_unique_game_id():
    game_id = generate_game_id()
    while GameSession.objects.filter(game_id=game_id).exists():
        game_id = generate_game_id()
    return game_id


class GameSession(models.Model):
    # Constants for game session states
    INITIALIZING = "initializing"
    CHARACTER_CREATION = "character_creation"
    REGULAR_TURN = "regular_turn"
    INACTIVE = "inactive"
    ENDED = "ended"

    # Choices for game session states
    STATE_CHOICES = [
        (INITIALIZING, "Initializing"),
        (CHARACTER_CREATION, "Character Creation"),
        (REGULAR_TURN, "Regular Turn"),
        (INACTIVE, "Inactive"),
        (ENDED, "Ended"),
    ]

    state = FSMField(default=INITIALIZING, choices=STATE_CHOICES)
    game_id = models.CharField(max_length=255, unique=True)
    playerA = models.ForeignKey(
        "Player",
        on_delete=models.SET_NULL,
        related_name="player1_sessions",
        null=True,
        blank=True,
    )
    playerB = models.ForeignKey(
        "Player",
        on_delete=models.SET_NULL,
        related_name="player2_sessions",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    current_game_turn = models.OneToOneField(
        "GameTurn",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parent_game",
    )

    chat_messages = models.ManyToManyField("ChatMessage", blank=True)

    @transition(field=state, source="INITIALIZING", target="REGULAR_TURN")
    def initialize_game(self):
        # Check if both players are set
        if not self.playerA or not self.playerB:
            raise ValueError("Both players must be set before initializing the game.")

        # Update the current game turn's active player
        self.current_game_turn.active_player = self.playerA
        self.current_game_turn.save()

        # Transition to the REGULAR_TURN state
        # This will change later when we add the character creation step
        return True, "Game initialized successfully."

    @transition(field=state, source="*", target="inactive")
    def set_game_inactive(self):
        self.is_active = False
        self.save()

    @transition(field=state, source="*", target="ended")
    def end_session(self):
        self.playerA.delete()
        self.playerB.delete()
        self.current_game_turn.child_step.delete()
        self.current_game_turn.delete()
        self.chat_messages.all().delete()
        self.delete()

    def save(self, *args, **kwargs):
        # Check if it's a new instance
        is_new = not self.pk

        # Generate a unique game_id if not already set
        if not self.game_id:
            self.game_id = generate_unique_game_id()

        # If it's a new instance, create an initial GameTurn
        if is_new:
            self.current_game_turn = GameTurn.objects.create()
        # Save the GameSession instance
        super(GameSession, self).save(*args, **kwargs)


class GameTurn(models.Model):
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    active_player = models.ForeignKey(
        "Player", on_delete=models.SET_NULL, null=True, blank=True
    )
    turn_number = models.IntegerField(default=1)

    player_a_narrative_choice_made = models.BooleanField(default=False)
    player_b_narrative_choice_made = models.BooleanField(default=False)

    player_a_moon_phase_message_written = models.BooleanField(default=False)
    player_b_moon_phase_message_written = models.BooleanField(default=False)

    SELECT_QUESTION = "select_question"
    ANSWER_QUESTION = "answer_question"
    REACT_EMOJI = "react_emoji"
    NARRATIVE_CHOICES = "narrative_choices"
    MOON_PHASE = "moon_phase"

    # Choices for game session states
    STATE_CHOICES = [
        (SELECT_QUESTION, "Select Question"),
        (ANSWER_QUESTION, "Answer Question"),
        (REACT_EMOJI, "React with Emoji"),
        (NARRATIVE_CHOICES, "Narrative Choices"),
        (MOON_PHASE, "Moon Phase"),
    ]

    state = FSMField(default=SELECT_QUESTION, choices=STATE_CHOICES)

    def get_active_player(self):
        return self.active_player

    def switch_active_player(self):
        """Switch the active player for this turn."""
        if self.active_player == self.parent_game.playerA:
            self.active_player = self.parent_game.playerB
        else:
            self.active_player = self.parent_game.playerA
        self.save()

    @transition(field=state, source="SELECT_QUESTION", target="ANSWER_QUESTION")
    def select_question(self, selected_question_id, user):
        # Check if the current user is the active player
        if user != self.active_player.user:
            return False, "You are not the active player. Please wait for your turn."

        # Get the selected question
        selected_question = Question.objects.get(id=selected_question_id)
        if not selected_question:
            return False, "Please select a question."

        # Create a chat message
        ChatMessage.objects.create(
            game_session=self.game_session,
            sender=str(user),
            text=str(selected_question),
        )

        return True, "Question selected successfully."

    @transition(field=state, source=ANSWER_QUESTION, target=REACT_EMOJI)
    def answer_question(self, answer, user):
        # Check if the current user is the active player
        if user != self.active_player.user:
            return False, "You are not the active player. Please wait for your turn."

        # Create a chat message
        ChatMessage.objects.create(
            game_session=self.game_session,
            sender=str(user),
            text=str(answer),
        )

        return True, "Answer submitted successfully."

    @transition(field=state, source="REACT_EMOJI", target="AWAITING_NARRATIVE_CHOICES")
    def react_with_emoji(self, emoji, user):
        # Ensure emoji is selected
        if not emoji:
            raise ValueError("Please select an emoji to react with.")

        # Check if the current user is the active player
        if user != self.active_player.user:
            raise ValueError("It's not your turn.")

        # Fetch the latest message for the current game session to add the reaction
        latest_message = ChatMessage.objects.filter(
            game_session=self.game_session
        ).last()

        if latest_message:
            latest_message.reaction = emoji
            latest_message.save()

        return True, "Emoji reaction submitted successfully."

    @transition(
        field=state,
        source="NARRATIVE_CHOICES",
        target=None,  # Keep the same state if conditions are not met
        custom=dict(
            target="get_next_state"
        ),  # Use get_next_state to determine the target
    )
    def make_narrative_choice(self, player, narrative_choice):
        # Update the narrative choice for the player
        if player == self.parent_game.playerA:
            self.player_a_choice_made = True
            # Update Player A's word pool here
        elif player == self.parent_game.playerB:
            self.player_b_choice_made = True
            # Update Player B's word pool here
        else:
            raise ValueError("Invalid player.")

        # process the narrative choice here:
        # adding the associated words to the player's word pool

        # Check if both players have made their choices
        if self.player_a_choice_made and self.player_b_choice_made:
            # Reset the flags for the next turn
            self.player_a_choice_made = False
            self.player_b_choice_made = False
            # Transition to the SELECT_QUESTION state and add 1 to the turn number
            self.turn_number += 1
            return True, "Both players have made their choices."
        # If not both players have made their choice, stay in the current state
        return False, "Waiting for the other player to make their choice."

    @staticmethod
    def get_next_state(self):
        # Your conditional check goes here
        if self.turn_number == self.get_moon_phase(self.turn_number):
            return "MOON_PHASE"
        else:
            return "SELECT_QUESTION"

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

    @transition(field=state, source="MOON_PHASE", target="SELECT_QUESTION")
    def write_message_about_moon_phase(self):
        # validate that both players have written their messages
        if (
            not self.player_a_moon_phase_message_written
            or not self.player_b_moon_phase_message_written
        ):
            raise ValueError(
                "Both players must write their messages before ending the turn."
            )
        # reset the flags
        self.player_a_moon_phase_message_written = False
        self.player_b_moon_phase_message_written = False
        # transition to the next state
        self.turn_number += 1
        return True, "Both players have written their messages."


class Question(models.Model):
    text = models.CharField(max_length=1024)

    def __str__(self):
        return self.text


class Word(models.Model):
    word = models.CharField(max_length=255)

    def __str__(self):
        return self.word


class ChatMessage(models.Model):
    game_session = models.ForeignKey(
        GameSession, on_delete=models.CASCADE
    )  # To relate the message to a game session
    sender = models.CharField(max_length=255)  # The name of the sender (player)
    text = models.TextField()  # The main content of the message (question/answer)
    reaction = models.CharField(
        max_length=255, null=True, blank=True
    )  # The emoji reaction, if any
    timestamp = models.DateTimeField(
        auto_now_add=True
    )  # To track when the message was sent

    def __str__(self):
        return self.text


class NarrativeChoice(models.Model):
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    game_turn = models.ForeignKey(GameTurn, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    choice = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
