import random
from collections import Counter

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
import uuid
from django.urls import reverse
from django_fsm import FSMField, transition


class Player(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE
    )  # if the user is deleted, the 'Player' is deleted.

    character_name = models.CharField(max_length=255, blank=True)
    character_word_pool = models.ManyToManyField("Word", blank=True, related_name="wp")
    simple_word_pool = models.ManyToManyField("Word", blank=True, related_name="swp")
    question_pool = models.ManyToManyField("Question", blank=True)
    narrative_choice_pool = models.ManyToManyField("NarrativeChoice", blank=True)

    game_session = models.ForeignKey(
        "GameSession", related_name="game_players", on_delete=models.CASCADE
    )
    character = models.ForeignKey(
        "Character", on_delete=models.SET_NULL, null=True, blank=True
    )
    MoonSignInterpretation = models.ForeignKey(
        "MoonSignInterpretation", on_delete=models.SET_NULL, null=True, blank=True
    )

    # Constants for character creation states
    CHARACTER_AVATAR_SELECTION = "character_avatar_selection"
    MOON_MEANING_SELECTION = "moon_meaning_selection"
    PUBLIC_PROFILE_CREATION = "public_profile_creation"
    CHARACTER_COMPLETE = "character_complete"

    # Choices for character creation states
    CHARACTER_CREATION_STATE_CHOICES = [
        (CHARACTER_AVATAR_SELECTION, "Character Avatar Selection"),
        (MOON_MEANING_SELECTION, "Moon Meaning Selection"),
        (PUBLIC_PROFILE_CREATION, "Public Profile Creation"),
        (CHARACTER_COMPLETE, "Character Complete"),
    ]

    character_creation_state = FSMField(
        default=CHARACTER_AVATAR_SELECTION, choices=CHARACTER_CREATION_STATE_CHOICES
    )

    @transition(
        field=character_creation_state,
        source=CHARACTER_AVATAR_SELECTION,
        target=MOON_MEANING_SELECTION,
    )
    def select_character_avatar(self, character):
        self.character = character
        self.save()

    @transition(
        field=character_creation_state,
        source=MOON_MEANING_SELECTION,
        target=PUBLIC_PROFILE_CREATION,
    )
    def select_moon_meaning(self, moon_meaning):
        self.MoonSignInterpretation = moon_meaning
        self.save()

    @transition(
        field=character_creation_state,
        source=PUBLIC_PROFILE_CREATION,
        target=CHARACTER_COMPLETE,
    )
    def create_public_profile(self, qualities, interests, activities):
        self.character_name = self.character.name
        self.populate_character_with_creation_choices(qualities, interests, activities)
        self.save()

    def save(self, *args, **kwargs):
        if not self.game_session:
            raise ValidationError(
                "A player must be associated with a GameSession before saving."
            )
        if not self.character_name and self.user_id:
            # Set the nickname based on the related User instance
            self.character_name = "Character of " + self.user.get_username()
        super(Player, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Update the related GameSession's is_active field
        self.game_session.set_game_inactive()

        # Now, actually delete the player
        super(Player, self).delete(*args, **kwargs)

    def populate_character_with_creation_choices(
        self, qualities, interests, activities
    ):
        for quality_id in qualities:
            if quality_id is not None:
                quality = Quality.objects.get(id=quality_id)
                words = list(quality.words.all())
                random_words = random.sample(words, min(len(words), 15))
                for word in random_words:
                    self.character_word_pool.add(word)

        for activity_id in activities:
            if activity_id is not None:
                activity = Activity.objects.get(id=activity_id)
                questions = list(activity.questions.all())
                random_questions = random.sample(questions, min(len(questions), 3))
                for question in random_questions:
                    self.question_pool.add(question)

        for interest_id in interests:
            if interest_id is not None:
                interest = Interest.objects.get(id=interest_id)
                for narrative_choice in interest.narrative_choices.all():
                    self.narrative_choice_pool.add(narrative_choice)

        self.replenish_simple_words()

    def replenish_simple_words(self):
        # Count the current kind_of_words in the pool
        current_counts = Counter(
            word.kind_of_word for word in self.simple_word_pool.all()
        )
        target_counts = {
            "verb": 5,
            "pronoun": 3,
            "preposition": 5,
            "conjunction": 5,
            "article": 3,
            "determiner": 5,
            "modifier": 4,
        }  # Adjust numbers as needed

        simple_words = list(Word.objects.filter(isSimple=True).all())
        for kind, target_count in target_counts.items():
            current_count = current_counts[kind]
            words_to_add_count = target_count - current_count

            # Filter words of this kind
            words_of_this_kind = [
                word for word in simple_words if word.kind_of_word == kind
            ]
            print(f"Total simple words of kind '{kind}': {len(words_of_this_kind)}")
            print(f"Words to add for kind '{kind}': {words_to_add_count}")
            if words_to_add_count > 0 and len(words_of_this_kind) >= words_to_add_count:
                filtered_words = [
                    word
                    for word in words_of_this_kind
                    if word not in self.simple_word_pool.all()
                ]

                # Randomly select words to add
                words_to_add = random.sample(
                    filtered_words, k=min(len(words_of_this_kind), words_to_add_count)
                )

                for word in words_to_add:
                    self.simple_word_pool.add(word)

        self.save()
        current_counts = Counter(
            word.kind_of_word for word in self.simple_word_pool.all()
        )
        print(current_counts.get("verb"))


# Auxiliary functions for game session
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
    game_id = models.CharField(
        max_length=255,
        unique=True,
    )
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

    asked_questions = models.ManyToManyField("Question", blank=True)

    gameLog = models.OneToOneField(
        "GameLog",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parent_game",
    )

    def __init__(self, *args, **kwargs):
        super(GameSession, self).__init__(*args, **kwargs)
        if not self.game_id:
            self.game_id = generate_unique_game_id()

    @transition(field=state, source=INITIALIZING, target=CHARACTER_CREATION)
    def initialize_game(self):
        # Check if both players are set
        if not self.playerA or not self.playerB:
            raise ValueError("Both players must be set before initializing the game.")
        self.gameLog = GameLog.objects.create()
        self.save()
        self.current_game_turn = GameTurn.objects.create()
        self.current_game_turn.active_player = self.playerA
        self.current_game_turn.save()
        return True, "Game initialized successfully."

    @transition(field=state, source="*", target="inactive")
    def set_game_inactive(self):
        self.is_active = False
        self.save()

    @transition(field=state, source="*", target="ended")
    def end_session(self):
        self.playerA.delete()
        self.playerB.delete()
        self.current_game_turn.delete()
        self.refresh_from_db()
        # self.chat_messages.all().delete()
        # self.delete()

    def save(self, *args, **kwargs):
        super(GameSession, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("game:game_progress", kwargs={"game_id": self.game_id})

    @transition(field=state, source=CHARACTER_CREATION, target=REGULAR_TURN)
    def start_regular_turn(self):
        pass


class GameTurn(models.Model):
    active_player = models.ForeignKey(
        "Player", on_delete=models.SET_NULL, null=True, blank=True
    )
    turn_number = models.IntegerField(default=1)
    narrative_nights = models.IntegerField(default=1)
    player_a_completed_cycle = models.BooleanField(default=False)
    player_b_completed_cycle = models.BooleanField(default=False)

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

    def set_active_player(self, player):
        self.active_player = player
        self.save()

    def switch_active_player(self):
        if self.active_player == self.parent_game.playerA:
            self.active_player = self.parent_game.playerB
        else:
            self.active_player = self.parent_game.playerA
        self.save()

    @transition(field=state, source=SELECT_QUESTION, target=ANSWER_QUESTION)
    def select_question(self, selected_question_id, player):
        # Check if the current user is the active player
        if player != self.active_player:
            raise ValueError("It's not your turn.")

        # Get the selected question
        selected_question = Question.objects.get(id=selected_question_id)
        if not selected_question:
            raise ValueError("No question selected.")

        # Create a chat message and add it to the log
        chat_message = ChatMessage.objects.create(
            avatar_url=str(player.character.image.url),
            sender=str(player.character_name),
            text=str(selected_question.text),
        )
        self.parent_game.gameLog.chat_messages.add(chat_message)

        self.switch_active_player()

    @transition(field=state, source=ANSWER_QUESTION, target=REACT_EMOJI)
    def answer_question(self, answer, player):
        # Check if the current user is the active player
        if player != self.active_player:
            raise ValueError("It's not your turn.")

        # Create a chat message and add it to the log
        chat_message = ChatMessage.objects.create(
            avatar_url=str(player.character.image.url),
            sender=str(player.character_name),
            text=str(answer),
        )
        for word in answer.split():
            if player.simple_word_pool.filter(word=word):
                word = player.simple_word_pool.filter(word=word).first()
                player.simple_word_pool.remove(word)
                player.save()
            elif player.character_word_pool.filter(word=word):
                word = player.character_word_pool.filter(word=word).first()
                player.character_word_pool.remove(word)
                player.save()
        self.parent_game.gameLog.chat_messages.add(chat_message)
        self.switch_active_player()

    @transition(field=state, source=REACT_EMOJI, target=None)
    def react_with_emoji(self, emoji, player):
        # Ensure emoji is selected
        if not emoji:
            raise ValueError("Please select an emoji to react with.")

        # Check if the current user is the active player
        if player != self.active_player:
            raise ValueError("It's not your turn.")

        if player == self.parent_game.playerA:
            self.player_a_completed_cycle = True
        elif player == self.parent_game.playerB:
            self.player_b_completed_cycle = True
        else:
            raise ValueError("Invalid player.")

        # Fetch the latest message for the current game session to add the reaction
        latest_message = self.parent_game.gameLog.chat_messages.last()

        if latest_message:
            latest_message.reaction = emoji
            latest_message.save()

        self.switch_active_player()

        if self.player_a_completed_cycle and self.player_b_completed_cycle:
            # Reset the flags for the next turn
            self.player_a_completed_cycle = False
            self.player_b_completed_cycle = False
            # Set the state to the determined next state
            self.state = self.NARRATIVE_CHOICES
            self.save()
        else:
            self.state = self.SELECT_QUESTION
            self.save()

    @transition(
        field=state,
        source=NARRATIVE_CHOICES,
        target=None,
    )
    def make_narrative_choice(self, narrative_choice, player):
        # Update the narrative choice for the player
        if player == self.parent_game.playerA:
            self.player_a_narrative_choice_made = True
            self.process_narrative_choice(narrative_choice, player)
        elif player == self.parent_game.playerB:
            self.player_b_narrative_choice_made = True
            self.process_narrative_choice(narrative_choice, player)
        else:
            raise ValueError("Invalid player.")

        # process the narrative choice here:
        # adding the associated words to the player's word pool
        # selected_narrative_choice = NarrativeChoice.objects.get(id=narrative_choice)
        # Check if both players have made their choices
        if self.player_a_narrative_choice_made and self.player_b_narrative_choice_made:
            # Reset the flags for the next turn and transition the state
            self.reset_flags_and_transition()

    def process_narrative_choice(self, narrative_choice, player):
        # Fetch the selected narrative choice and add to word pool
        selected_narrative_choice = NarrativeChoice.objects.get(id=narrative_choice)
        if selected_narrative_choice:
            for word in selected_narrative_choice.words.all():
                player.character_word_pool.add(word)
                player.save()
        player.replenish_simple_words()

    def reset_flags_and_transition(self):
        # Reset the narrative choice flags
        self.player_a_narrative_choice_made = False
        self.player_b_narrative_choice_made = False

        # Increment turn number and check for game end
        self.turn_number += 1
        self.narrative_nights += 1
        MAX_NUMBER_OF_TURNS = 30
        if self.turn_number >= MAX_NUMBER_OF_TURNS:
            self.parent_game.set_game_inactive()
            self.parent_game.state = self.parent_game.ENDED

        # Determine and set the next state
        next_state = self.regular_or_special_moon_next()
        self.switch_active_player()
        self.state = next_state
        self.save()

    def regular_or_special_moon_next(self):
        if self.get_moon_phase():
            return self.MOON_PHASE
        else:
            return self.SELECT_QUESTION

    def get_moon_phase(self):
        moon_phases = {
            3: "new_moon",
            7: "first_quarter",
            11: "full_moon",
            15: "last_quarter",
        }
        return moon_phases.get(self.turn_number)

    def get_moon_emoji(self, moon_phase):
        moon_sign_mapping = {
            "new_moon": "🌑",
            "first_quarter": "🌓",
            "full_moon": "🌕",
            "last_quarter": "🌗",
        }
        return moon_sign_mapping.get(moon_phase, "Unknown sign")

    @transition(
        field=state,
        source=MOON_PHASE,
        target=SELECT_QUESTION,
    )
    def write_message_about_moon_phase(self, message, player):
        # Update the moon message for the player
        if player == self.parent_game.playerA:
            self.player_a_moon_phase_message_written = True
        elif player == self.parent_game.playerB:
            self.player_b_moon_phase_message_written = True
        else:
            raise ValueError("Invalid player.")
        self.save()
        # Create a chat message and add it to the log
        if player != self.active_player:
            raise ValueError("It's not your turn.")

        chat_message = ChatMessage.objects.create(
            avatar_url=str(player.character.image.url),
            sender=str(player.character_name),
            text=str(message),
        )
        self.parent_game.gameLog.chat_messages.add(chat_message)

        # Change the current moon sign reason to the message
        moon_phase = self.get_moon_phase()
        moon_sign_interpretation = player.MoonSignInterpretation
        moon_sign_interpretation.change_moon_sign(moon_phase, message)
        moon_sign_interpretation.save()

        # Process the answer and update word pools
        for word in message.split():
            if player.simple_word_pool.filter(word=word).exists():
                word_obj = player.simple_word_pool.filter(word=word).first()
                player.simple_word_pool.remove(word_obj)
            elif player.character_word_pool.filter(word=word).exists():
                word_obj = player.character_word_pool.filter(word=word).first()
                player.character_word_pool.remove(word_obj)

        player.save()

        self.switch_active_player()
        self.save()
        # Check if both players have written their messages
        if (
            self.player_a_moon_phase_message_written
            and self.player_b_moon_phase_message_written
        ):
            # Reset the flags for the next turn
            self.player_a_moon_phase_message_written = False
            self.player_b_moon_phase_message_written = False
            # Transition to the SELECT_QUESTION state and add 1 to the turn number
            self.turn_number += 1
        else:
            raise ValueError("Not both players have written their messages.")


class GameLog(models.Model):
    chat_messages = models.ManyToManyField(
        "ChatMessage", blank=True, related_name="game_log"
    )

    def __int__(self):
        return self.id


class ChatMessage(models.Model):
    avatar_url = models.CharField(max_length=255, null=True, blank=True)
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


class Character(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    quality_1_choices = models.ManyToManyField("Quality", blank=True, related_name="q1")
    quality_2_choices = models.ManyToManyField("Quality", blank=True, related_name="q2")
    quality_3_choices = models.ManyToManyField("Quality", blank=True, related_name="q3")
    interest_1_choices = models.ManyToManyField(
        "Interest", blank=True, related_name="i1"
    )
    interest_2_choices = models.ManyToManyField(
        "Interest", blank=True, related_name="i2"
    )
    interest_3_choices = models.ManyToManyField(
        "Interest", blank=True, related_name="i3"
    )
    activity_1_choices = models.ManyToManyField(
        "Activity", blank=True, related_name="a1"
    )
    activity_2_choices = models.ManyToManyField(
        "Activity", blank=True, related_name="a2"
    )
    # Image field for visual representation
    image = models.ImageField(upload_to="characters/", blank=True, null=True)

    def __str__(self):
        return self.name


class Quality(models.Model):
    name = models.CharField(max_length=255)
    words = models.ManyToManyField("Word", blank=True)

    def __str__(self):
        return self.name


class Activity(models.Model):
    name = models.CharField(max_length=255)
    questions = models.ManyToManyField("Question", blank=True)

    def __str__(self):
        return self.name


class Interest(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class NarrativeChoice(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="narrative_choices", blank=True, null=True)
    interest = models.ForeignKey(
        "Interest", on_delete=models.CASCADE, related_name="narrative_choices"
    )
    night_number = models.IntegerField()
    words = models.ManyToManyField("Word", blank=True)

    class Meta:
        unique_together = ("interest", "name", "night_number")
        # This ensures that the combination of interest and night_number is unique

    def __str__(self):
        return self.name


class Question(models.Model):
    text = models.CharField(max_length=1024)

    def __str__(self):
        return self.text


class Word(models.Model):
    word = models.CharField(max_length=255)
    isSimple = models.BooleanField(default=False)
    kind_of_word = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.word

    def __eq__(self, other):
        if isinstance(other, Word):
            return self.word == other.word and self.kind_of_word == other.kind_of_word
        return False

    def __hash__(self):
        return hash((self.word, self.kind_of_word))

    def __repr__(self):
        return f"<Word: {self.word}>"


class MoonSignInterpretation(models.Model):
    # Assuming you have a Player model that is linked to the User model
    on_player = models.ForeignKey(
        "Player", on_delete=models.CASCADE, null=True, blank=True
    )
    first_quarter = models.CharField(max_length=150)
    first_quarter_reason = models.TextField()
    full_moon = models.CharField(max_length=150)
    full_moon_reason = models.TextField()
    last_quarter = models.CharField(max_length=150)
    last_quarter_reason = models.TextField()
    new_moon = models.CharField(max_length=150)
    new_moon_reason = models.TextField()

    def get_moon_sign(self, moon_phase):
        # Implement your logic to return the moon sign based on the phase
        moon_sign_mapping = {
            "new_moon": self.new_moon,
            "first_quarter": self.first_quarter,
            "full_moon": self.full_moon,
            "last_quarter": self.last_quarter,
        }
        return moon_sign_mapping.get(moon_phase, "Unknown sign")

    def get_moon_sign_reason(self, moon_phase):
        moon_sign_mapping = {
            "new_moon": self.new_moon_reason,
            "first_quarter": self.first_quarter_reason,
            "full_moon": self.full_moon_reason,
            "last_quarter": self.last_quarter_reason,
        }
        return moon_sign_mapping.get(moon_phase, "Unknown sign")

    def change_moon_sign(self, moon_phase, new_sign):
        # Ensure the moon_phase key exists in the dictionary to avoid AttributeError
        if moon_phase not in [
            "new_moon",
            "new_moon_reason",
            "first_quarter",
            "first_quarter_reason",
            "full_moon",
            "full_moon_reason",
            "last_quarter",
            "last_quarter_reason",
        ]:
            raise ValueError(f"Invalid moon phase: {moon_phase}")

        # Use setattr to update the attribute
        setattr(self, moon_phase, new_sign)
        self.save()


class PublicProfile(models.Model):
    quality_1 = models.CharField(max_length=100)
    quality_2 = models.CharField(max_length=100)
    quality_3 = models.CharField(max_length=100)
    interest_1 = models.CharField(max_length=100)
    interest_2 = models.CharField(max_length=100)
    interest_3 = models.CharField(max_length=100)
    activity_1 = models.CharField(max_length=100)
    activity_2 = models.CharField(max_length=100)
