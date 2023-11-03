from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
import uuid


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
        if not self.game_session.current_game_turn.current_player:
            self.game_session.current_game_turn.current_player = self
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
    game_id = models.CharField(max_length=255, unique=True)

    player1 = models.ForeignKey(
        "Player",
        on_delete=models.SET_NULL,
        related_name="player1_sessions",
        null=True,
        blank=True,
    )
    player2 = models.ForeignKey(
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

    def end_session(self):
        # Delete the associated players to release their one-to-one relation with users
        self.player1.delete()
        self.player2.delete()
        # Delete the associated game turn and game step
        self.current_game_turn.child_step.delete()
        self.current_game_turn.delete()
        # Delete the associated chat messages
        self.chat_messages.all().delete()
        # Delete the session itself
        self.delete()

    def set_game_inactive(self):
        self.is_active = False
        self.save()


class GameTurn(models.Model):
    current_player = models.ForeignKey(
        "Player", on_delete=models.SET_NULL, null=True, blank=True
    )

    turn_number = models.IntegerField(default=1)
    child_step = models.OneToOneField(
        "GameStep", on_delete=models.CASCADE, related_name="parent_turn"
    )

    narrative_choices_made = models.PositiveIntegerField(default=0)
    moon_meanings_submitted = models.PositiveIntegerField(default=0)

    def switch_active_player(self):
        """Switch the active player for this turn."""
        if self.current_player == self.parent_game.player1:
            self.current_player = self.parent_game.player2
        else:
            self.current_player = self.parent_game.player1
        self.save()

    def save(self, *args, **kwargs):
        # Check if it's a new instance
        is_new = not self.pk
        # If it's a new instance, create a new GameStep and assign it to the child_step field
        if is_new:
            game_step = GameStep.objects.create()
            self.child_step = game_step
        # Call the default save method
        super(GameTurn, self).save(*args, **kwargs)


class GameStep(models.Model):
    # Constants for turn steps with an explicit player identifier
    P1_SELECT_QUESTION = "p1_select_question"
    P2_ANSWER_QUESTION = "p2_answer_question"
    P1_REACT_EMOJI = "p1_react_emoji"
    P2_SELECT_QUESTION = "p2_select_question"
    P1_ANSWER_QUESTION = "p1_answer_question"
    P2_REACT_EMOJI = "p2_react_emoji"
    AWAITING_NARRATIVE_CHOICES = "awaiting_narrative_choices"

    TURN_STEPS = [
        (P1_SELECT_QUESTION, "Player 1: Select Question"),
        (P2_ANSWER_QUESTION, "Player 2: Answer Question"),
        (P1_REACT_EMOJI, "Player 1: React with Emoji"),
        (P2_SELECT_QUESTION, "Player 2: Select Question"),
        (P1_ANSWER_QUESTION, "Player 1: Answer Question"),
        (P2_REACT_EMOJI, "Player 2: React with Emoji"),
        (AWAITING_NARRATIVE_CHOICES, "Awaiting Narrative Choices"),
    ]

    step = models.CharField(
        max_length=30, choices=TURN_STEPS, default=P1_SELECT_QUESTION
    )

    def advance_step(self):
        """Advance to the next step in the turn sequence."""

        # Extracting the identifiers from the TURN_STEPS list of tuples
        sequence = [step[0] for step in self.TURN_STEPS]

        index = sequence.index(self.step)

        # Check if it's the last step in the sequence
        if index == len(sequence) - 1:
            self.parent_turn.switch_active_player()
            self.parent_turn.turn_number += 1
            self.parent_turn.save()
            self.step = sequence[0]
        else:
            # Otherwise, move to the next step in the sequence
            self.step = sequence[index + 1]
            self.parent_turn.switch_active_player()
            self.parent_turn.save()

        # Save the changes to the database
        self.save()


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
