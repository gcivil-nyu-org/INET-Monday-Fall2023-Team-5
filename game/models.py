from django.db import models
from django.contrib.auth.models import User


class Player(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE
    )  # if the user is deleted, the 'Player' is deleted.
    word_pool = models.ManyToManyField("Word", blank=True)
    question_pool = models.ManyToManyField("Question", blank=True)
    # Use the string 'GameSession' instead of GameSession
    game_session = models.ForeignKey(
        "GameSession", related_name="game_players", on_delete=models.CASCADE
    )


class GameSession(models.Model):
    # Create variables for two players per game session
    PLAYER_CHOICES = [
        ("1", "Player 1"),
        ("2", "Player 2"),
    ]
    player1 = models.ForeignKey(
        "Player", on_delete=models.CASCADE, related_name="player1_sessions"
    )
    player2 = models.ForeignKey(
        "Player", on_delete=models.CASCADE, related_name="player2_sessions"
    )
    active_player = models.CharField(
        max_length=1, choices=PLAYER_CHOICES, null=True, blank=True
    )

    # Constants for turn steps with an explicit player identifier
    P1_SELECT_QUESTION = "p1_select_question"
    P2_ANSWER_QUESTION = "p2_answer_question"
    P1_REACT_EMOJI = "p1_react_emoji"
    P2_SELECT_QUESTION = "p2_select_question"
    P1_ANSWER_QUESTION = "p1_answer_question"
    P2_REACT_EMOJI = "p2_react_emoji"
    SELECT_NARRATIVE_EVENT = "select_narrative_event"
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

    current_step = models.CharField(
        max_length=30, choices=TURN_STEPS, default=P1_SELECT_QUESTION
    )

    def advance_step(self):
        """Advance to the next step in the turn sequence."""
        # Sequence for the turn steps
        sequence = [
            self.P1_SELECT_QUESTION,
            self.P2_ANSWER_QUESTION,
            self.P1_REACT_EMOJI,
            self.P2_SELECT_QUESTION,
            self.P1_ANSWER_QUESTION,
            self.P2_REACT_EMOJI,
            self.AWAITING_NARRATIVE_CHOICES,
        ]

        # get the index of the current step in the sequence
        index = sequence.index(self.current_step)

        # if it's the last step in the sequence (before awaiting choices), set to AWAITING_NARRATIVE_CHOICES
        if index == len(sequence) - 2:
            self.current_step = self.AWAITING_NARRATIVE_CHOICES
        else:
            self.current_step = sequence[index + 1]

        # If the current step begins with 'p1', set active player to "1". If 'p2', set to "2".
        if self.current_step.startswith("p1"):
            self.active_player = "1"
        elif self.current_step.startswith("p2"):
            self.active_player = "2"

        self.save()

    def check_narrative_choices(self):
        """Check if both players have made their narrative choices."""
        # logic to check if both players made their choice, possibly by checking a related model or a flag on the player
        # if both have chosen:
        self.advance_step()


class Question(models.Model):
    text = models.CharField(max_length=1024)

    def __str__(self):
        return self.text


class Word(models.Model):
    word = models.CharField(max_length=255)

    def __str__(self):
        return self.word
