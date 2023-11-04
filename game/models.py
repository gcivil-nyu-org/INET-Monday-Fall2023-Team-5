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

    def switch_active_player(self):
        """Switch the active player for this turn."""
        if self.active_player == self.parent_game.playerA:
            self.active_player = self.parent_game.playerB
        else:
            self.active_player = self.parent_game.playerA
        self.save()

    @transition(field=state, source="SELECT_QUESTION", target="ANSWER_QUESTION")
    def select_question(self, selected_question_id):
        selected_question = Question.objects.get(id=selected_question_id)
        if not selected_question:
            raise ValueError("Please select a question.")
        ChatMessage.objects.create(
            game_session=self.game_session,
            sender=str(self.current_player.user),
            text=str(selected_question),
        )

    @transition(field=state, source=ANSWER_QUESTION, target=REACT_EMOJI)
    def p2_answers_question(self):
        pass  # Logic for player 2 answering a question

    # Continue adding transition methods for each step in the turn

    def save(self, *args, **kwargs):
        # Check if it's a new instance
        is_new = not self.pk

        # Call the default save method
        super(GameTurn, self).save(*args, **kwargs)

        # If it's a new turn, switch the active player
        if is_new:
            self.switch_active_player()


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
