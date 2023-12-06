from django.contrib.messages import get_messages
from django.test import TestCase, RequestFactory, Client
from .models import (
    Character,
    Quality,
    Interest,
    Activity,
    GameSession,
    Player,
    ChatMessage,
    GameTurn,
    Question,
    Word,
    NarrativeChoice,
    MoonSignInterpretation,
)
from django.core.exceptions import ValidationError
from .forms import (
    CharacterSelectionForm,
    MoonSignInterpretationForm,
    PublicProfileCreationForm,
    AnswerFormMoon,
)
from django import forms
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.core.files.storage import default_storage
import io, os, uuid
from roleplaydate import settings
from django.urls import reverse
from .views import CharacterCreationView, GameProgressView, end_game_session
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from .context_processors import game_session_processor
from uuid import uuid4
from unittest.mock import patch


class CharacterModelTest(TestCase):
    def setUp(self):
        # Create instances of Quality, Interest, and Activity for testing
        self.quality1 = Quality.objects.create(name="Quality 1")
        self.quality2 = Quality.objects.create(name="Quality 2")
        self.interest1 = Interest.objects.create(name="Interest 1")
        self.interest2 = Interest.objects.create(name="Interest 2")
        self.activity1 = Activity.objects.create(name="Activity 1")
        self.activity2 = Activity.objects.create(name="Activity 2")

        # Create a Character instance
        self.character = Character.objects.create(
            name="Test Character", description="A test description"
        )

        # Add qualities, interests, and activities to the character
        self.character.quality_1_choices.add(self.quality1)
        self.character.quality_2_choices.add(self.quality2)
        self.character.interest_1_choices.add(self.interest1)
        self.character.interest_2_choices.add(self.interest2)
        self.character.activity_1_choices.add(self.activity1)
        self.character.activity_2_choices.add(self.activity2)

    def test_character_creation(self):
        """Test the character creation with all fields."""
        self.assertEqual(self.character.name, "Test Character")
        self.assertEqual(self.character.description, "A test description")

        # Test the relationships
        self.assertIn(self.quality1, self.character.quality_1_choices.all())
        self.assertIn(self.quality2, self.character.quality_2_choices.all())
        self.assertIn(self.interest1, self.character.interest_1_choices.all())
        self.assertIn(self.interest2, self.character.interest_2_choices.all())
        self.assertIn(self.activity1, self.character.activity_1_choices.all())
        self.assertIn(self.activity2, self.character.activity_2_choices.all())

    def test_string_representation(self):
        """Test the character string representation."""
        self.assertEqual(str(self.character), "Test Character")

    def test_name_max_length(self):
        """Test that the 'name' field does not exceed 255 characters."""
        character = Character(
            name="a" * 256, description="A test description"  # 256 characters long
        )
        with self.assertRaises(ValidationError):
            character.full_clean()  # This will validate the model fields

    def test_description_accepts_text(self):
        """Test that the 'description' field correctly accepts text."""
        character = Character.objects.create(
            name="Test Character",
            description="A long description" * 10,  # A longer text
        )
        self.assertEqual(character.description, "A long description" * 10)

    def test_add_and_remove_qualities(self):
        """Test adding and removing Quality objects to a Character."""
        quality3 = Quality.objects.create(name="Quality 3")
        self.character.quality_1_choices.add(quality3)

        # Test adding
        self.assertIn(quality3, self.character.quality_1_choices.all())

        # Test removing
        self.character.quality_1_choices.remove(quality3)
        self.assertNotIn(quality3, self.character.quality_1_choices.all())

    def test_add_and_remove_interests(self):
        """Test adding and removing Interest objects to a Character."""
        interest3 = Interest.objects.create(name="Interest 3")
        self.character.interest_1_choices.add(interest3)

        # Test adding
        self.assertIn(interest3, self.character.interest_1_choices.all())

        # Test removing
        self.character.interest_1_choices.remove(interest3)
        self.assertNotIn(interest3, self.character.interest_1_choices.all())

    def test_add_and_remove_activities(self):
        """Test adding and removing Activity objects to a Character."""
        activity3 = Activity.objects.create(name="Activity 3")
        self.character.activity_1_choices.add(activity3)

        # Test adding
        self.assertIn(activity3, self.character.activity_1_choices.all())

        # Test removing
        self.character.activity_1_choices.remove(activity3)
        self.assertNotIn(activity3, self.character.activity_1_choices.all())

    def test_image_field_upload(self):
        """Test uploading an in-memory image to the image field."""
        # Create an in-memory image
        image = Image.new("RGB", (100, 100), color="red")  # Creates a red image
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)

        image_file = InMemoryUploadedFile(
            image_io,
            None,
            "test_image.jpg",
            "image/jpeg",
            image_io.getbuffer().nbytes,
            None,
        )

        # Create a Character instance and assign the image
        character = Character.objects.create(
            name="Test Character", description="Test Description"
        )
        character.image = image_file
        character.save()

        # Reload the character from the database
        character_from_db = Character.objects.get(id=character.id)

        # Check that the image has been saved and has the correct path
        self.assertTrue(character_from_db.image.url.endswith("test_image.jpg"))

    def test_image_field_upload(self):
        """Test uploading an in-memory image to the image field."""
        # Create an in-memory image
        image = Image.new("RGB", (100, 100), color="red")  # Creates a red image
        image_io = io.BytesIO()
        image.save(image_io, format="JPEG")
        image_io.seek(0)

        image_file = InMemoryUploadedFile(
            image_io,
            None,
            "test_image.jpg",
            "image/jpeg",
            image_io.getbuffer().nbytes,
            None,
        )

        # Create a Character instance and assign the image
        character = Character.objects.create(
            name="Test Character", description="Test Description"
        )
        character.image = image_file
        character.save()

        # Reload the character from the database
        character_from_db = Character.objects.get(id=character.id)

        # Check that the image exists in the storage
        self.assertTrue(default_storage.exists(character_from_db.image.name))

    def tearDown(self):
        """Clean up any created files."""
        # Check if the test image file exists and delete it
        test_image_path = os.path.join(
            settings.MEDIA_ROOT, "characters", "test_image.jpg"
        )
        if os.path.exists(test_image_path):
            os.remove(test_image_path)

        # Additionally, clean up any image associated with the character
        if self.character.image and default_storage.exists(self.character.image.name):
            default_storage.delete(self.character.image.name)


class GameSessionProcessorTest(TestCase):
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(username="testuser", password="12345")
        another_user = User.objects.create_user(username="testuser2", password="12345")

        # Create a test game session
        self.game_session = GameSession.objects.create()

        # Create test players and associate them with the game session
        self.playerA = Player.objects.create(
            user=self.user, game_session=self.game_session
        )
        self.playerB = Player.objects.create(
            user=another_user, game_session=self.game_session
        )

        # Optionally associate the players with the game session
        self.game_session.playerA = self.playerA
        self.game_session.playerB = self.playerB
        self.game_session.save()

        # Set up a request factory
        self.factory = RequestFactory()

    def test_authenticated_user_with_active_game_session(self):
        # Create a test game session
        game_session = GameSession.objects.create(playerA=self.playerA, is_active=True)

        # Create a request object
        request = self.factory.get("/some/url")
        request.user = self.user

        # Call the context processor
        context = game_session_processor(request)

        # Check if the context contains the correct game session URL
        self.assertIsNotNone(context.get("game_session_url"))
        self.assertIn(game_session.get_absolute_url(), context["game_session_url"])

    def test_authenticated_user_no_active_game_session(self):
        # Make sure there are no active game sessions for the user
        GameSession.objects.filter(playerA=self.playerA).update(is_active=False)
        # Create a request object
        request = self.factory.get("/some/url")
        request.user = self.user

        # Call the context processor
        context = game_session_processor(request)

        # Check if the context does not contain a game session URL
        self.assertIsNone(context.get("game_session_url"))

    def test_unauthenticated_user(self):
        # Adjust the expected outcome to match the actual behavior
        request = self.factory.get("/some/url")
        request.user = User()  # User instance not saved to the database
        context = game_session_processor(request)
        self.assertEqual(context, {"game_session_url": None})


class GameProgressViewTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.client = Client()
        self.user = User.objects.create_user(username="testuser")
        self.another_user = User.objects.create_user(username="testuser2")
        self.client.force_login(self.user)

        user1 = self.user
        user2 = self.another_user
        # Create a new game session and save it
        self.game_session = GameSession()
        game_session = self.game_session
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

    def test_get_request_valid_game_id(self):
        # Make the request
        response = self.client.get(
            reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        )
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game_progress.html")
        self.assertIn("game_session", response.context)

    def test_get_request_invalid_game_id(self):
        # Create a game id that does not exist
        while True:
            game_id = uuid.uuid4()
            if not GameSession.objects.filter(game_id=game_id).exists():
                break

        response = self.client.get(
            reverse("game_progress", kwargs={"game_id": game_id})
        )

        # Assertions
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(message.message == "Game session not found." for message in messages)
        )
        # redirects to initiate game session page is currently the normal behavior, later when we
        # remove initiate game session page, we can change this to home page

        self.assertRedirects(
            response,
            reverse("end_game_session", kwargs={"game_id": game_id}),
            status_code=302,
            target_status_code=302,
        )

    def test_get_request_game_session_ended(self):
        self.game_session.state = GameSession.ENDED

        self.game_session.save()
        response = self.client.get(
            reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        )

        # Assertions
        self.assertTemplateUsed(response, "end_game_session.html")

    def test_get_chat_messages_after_game_session_ended(self):
        self.game_session.state = GameSession.ENDED

        chat_message = ChatMessage.objects.create(
            sender="testuser",
            text="test message",
        )
        chat_message2 = ChatMessage.objects.create(
            sender="testuser2",
            text="test message2",
        )

        self.game_session.gameLog.chat_messages.add(chat_message)
        self.game_session.gameLog.chat_messages.add(chat_message2)
        self.game_session.save()

        response = self.client.get(
            reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        )

        # Assertions
        self.assertTemplateUsed(response, "end_game_session.html")

        self.assertIn(chat_message, response.context["messages_by_sender"]["testuser"])
        self.assertIn(
            chat_message2, response.context["messages_by_sender"]["testuser2"]
        )

    def test_get_request_non_participant_user(self):
        self.game_session.state = GameSession.REGULAR_TURN

        # Create a player object for a different user
        another_user = User.objects.create_user(username="another_user")
        new_game_session = GameSession()
        new_game_session.save()
        Player.objects.create(user=another_user, game_session=new_game_session)

        new_client = Client()
        new_client.force_login(another_user)

        # Make the request as the non-participant user
        response = new_client.get(
            reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        )

        # Assertions
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                message.message == "You are not a participant of this game session."
                for message in messages
            )
        )
        self.assertRedirects(response, reverse("home"))

    def test_game_turn_select_question(self):
        self.game_session.current_game_turn.state = GameTurn.SELECT_QUESTION
        self.game_session.current_game_turn.save()

        # Add a question to the player's question pool
        question = Question.objects.create(text="test question")
        self.user.player.question_pool.add(question)

        response = self.client.get(
            reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        )

        # Assertions
        self.assertIn("random_questions", response.context)
        self.assertIn("test question", response.context["random_questions"][0].text)
        self.assertTrue(len(response.context["random_questions"]) == 1)
        self.assertTemplateUsed(response, "game_progress.html")

    def test_game_turn_answer_question(self):
        # Set the game turn state to ANSWER_QUESTION
        self.game_session.current_game_turn.state = GameTurn.ANSWER_QUESTION
        self.game_session.current_game_turn.save()

        # Add words to the player's word pool
        word1 = Word.objects.create(word="Uno")
        word2 = Word.objects.create(word="Dos")
        word3 = Word.objects.create(word="Tres")
        self.user.player.simple_word_pool.add(word1)
        self.user.player.character_word_pool.add(word2)
        self.user.player.simple_word_pool.add(word3)
        self.user.player.save()
        # Assertions

        response = self.client.get(
            reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        )

        # test that the context contains the correct words
        self.assertIn("Uno", response.context["tags_answer"])
        self.assertIn("Dos", response.context["tags_answer"])
        self.assertIn("Tres", response.context["tags_answer"])
        self.assertIn("answer_form", response.context)
        self.assertIsInstance(response.context["answer_form"], forms.Form)
        self.assertTemplateUsed(response, "game_progress.html")

    def test_game_turn_react_emoji(self):
        # Set the game turn state to REACT_EMOJI
        self.game_session.current_game_turn.state = GameTurn.REACT_EMOJI
        self.game_session.current_game_turn.save()

        response = self.client.get(
            reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        )

        # Assertions
        self.assertIn("emoji_form", response.context)
        self.assertIsInstance(response.context["emoji_form"], forms.Form)
        self.assertTemplateUsed(response, "game_progress.html")

    def test_game_turn_narrative_choices(self):
        # Set the game turn state to NARRATIVE_CHOICES
        self.game_session.current_game_turn.state = GameTurn.NARRATIVE_CHOICES
        self.game_session.current_game_turn.save()

        # When the narrative choice is not made the game should send context with a false value
        if self.game_session.playerA.user == self.user:
            self.game_session.current_game_turn.player_a_narrative_choice_made = False
        elif self.game_session.playerB.user == self.user:
            self.game_session.current_game_turn.player_b_narrative_choice_made = False
        self.game_session.current_game_turn.save()

        response = self.client.get(
            reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        )

        self.assertFalse(response.context["choice_made"])
        self.assertIsInstance(response.context["narrative_form"], forms.Form)
        self.assertTemplateUsed(response, "game_progress.html")

        # When the narrative choice is made
        if self.game_session.playerA.user == self.user:
            self.game_session.current_game_turn.player_a_narrative_choice_made = True
        elif self.game_session.playerB.user == self.user:
            self.game_session.current_game_turn.player_b_narrative_choice_made = True
        self.game_session.current_game_turn.save()

        response2 = self.client.get(
            reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        )
        # Assertions
        self.assertTrue(response2.context["choice_made"])

    # def test_game_turn_moon_phase(self):
    #     # RETIRE this unit test when we rewrite the moon phase turn to not be hard coded

    #     self.game_session.current_game_turn.state = GameTurn.MOON_PHASE
    #     self.game_session.current_game_turn.save()

    #     response = self.client.get(
    #         reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
    #     )

    #     # Assertions
    #     self.assertFalse(response.context["moon_phase"])
    #     self.assertTemplateUsed(response, "game_progress.html")

    #     # Set the game turn to #3 which is hard coded to be a moon phase turn
    #     self.game_session.current_game_turn.turn_number = 3
    #     self.game_session.current_game_turn.save()

    #     response = self.client.get(
    #         reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
    #     )
    #     self.assertTrue(response.context["moon_phase"])

    def test_game_turn_moon_phase(self):
        # Set the game turn state to MOON_PHASE
        self.game_session.current_game_turn.state = GameTurn.MOON_PHASE
        self.game_session.current_game_turn.save()

        # Add words to the player's word pool
        word1 = Word.objects.create(word="Uno")
        word2 = Word.objects.create(word="Dos")
        word3 = Word.objects.create(word="Tres")
        self.user.player.simple_word_pool.add(word1)
        self.user.player.character_word_pool.add(word2)
        self.user.player.simple_word_pool.add(word3)
        self.user.player.save()

        self.user.player.MoonSignInterpretation = MoonSignInterpretation.objects.create(
            first_quarter="positive",
            first_quarter_reason="Some reason",
            full_moon="negative",
            full_moon_reason="Another reason",
            last_quarter="ambiguous1",
            last_quarter_reason="Yet another reason",
            new_moon="ambiguous2",
            new_moon_reason="Different reason",
            player=self.user.player,
        )
        self.user.player.save()

        # Make the request
        response = self.client.get(
            reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        )

        # Assertions
        # Corrected the name of the form to 'answer_moon_form'
        self.assertIn("answer_moon_form", response.context)
        self.assertIsInstance(response.context["answer_moon_form"], AnswerFormMoon)
        self.assertTemplateUsed(response, "game_progress.html")


class CharacterCreationViewTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.client = Client()
        self.user = User.objects.create_user(username="testuser")
        self.another_user = User.objects.create_user(username="testuser2")
        self.client.force_login(self.user)

        user1 = self.user
        user2 = self.another_user
        # Create a new game session and save it
        self.game_session = GameSession()
        game_session = self.game_session
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

        # Create a Sample Character

        # Create instances of Quality, Interest, and Activity for testing as iterables
        qualities = [Quality.objects.create(name=f"Quality {i}") for i in range(1, 10)]
        interests = [
            Interest.objects.create(name=f"Interest {i}") for i in range(1, 10)
        ]
        activities = [
            Activity.objects.create(name=f"Activity {i}") for i in range(1, 5)
        ]

        # Associate words to qualities
        for quality in qualities:
            for i in range(15):
                quality.words.add(Word.objects.create(word=f"{quality.name} word {i}"))

        # Associate questions to activities
        for activity in activities:
            for i in range(3):
                question = Question.objects.create(
                    text=f"{activity.name} question {i}", activity=activity
                )
                activity.questions.add(question)

        # Associate narrative choices to interests
        for interest in interests:
            for i in range(25):
                NarrativeChoice.objects.create(
                    name=f"{interest.name} narrative choice {i}",
                    interest=interest,
                    night_number=i,
                )

        # Create a Character instance and add qualities, interests, and activities
        self.test_character = Character.objects.create(
            name="Test Character", description="A test description"
        )
        self.test_character.quality_1_choices.set(qualities[0:3])
        self.test_character.quality_2_choices.set(qualities[3:6])
        self.test_character.quality_3_choices.set(qualities[6:9])
        self.test_character.interest_1_choices.set(interests[0:3])
        self.test_character.interest_2_choices.set(interests[3:6])
        self.test_character.interest_3_choices.set(interests[6:9])
        self.test_character.activity_1_choices.set(activities[0:2])
        self.test_character.activity_2_choices.set(activities[2:4])
        self.test_character.save()

    def test_get_valid_game_id_character_creation(self):
        # Make the request
        response = self.client.get(
            reverse("character_creation", kwargs={"game_id": self.game_session.game_id})
        )
        # Assertions
        self.assertEqual(response.status_code, 302)
        self.assertTemplateUsed(response, "character_creation.html")

    def test_get_invalid_game_id(self):
        # Create a game id that does not exist
        while True:
            game_id = uuid.uuid4()
            if not GameSession.objects.filter(game_id=game_id).exists():
                break

        response = self.client.get(
            reverse("character_creation", kwargs={"game_id": game_id})
        )

        # Assertions
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(message.message == "Game session not found." for message in messages)
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

    def test_get_game_not_in_character_creation(self):
        # Set the game session state to REGULAR_TURN
        self.game_session.state = GameSession.REGULAR_TURN
        self.game_session.save()

        # Test the GET method when the game is not in CHARACTER_CREATION state
        response = self.client.get(
            reverse("character_creation", kwargs={"game_id": self.game_session.game_id})
        )

        # Assertions
        self.assertRedirects(
            response,
            self.game_session.get_absolute_url(),
        )

    def test_get_form_in_context(self):
        # Set the game session state to CHARACTER_CREATION
        self.game_session.state = GameSession.CHARACTER_CREATION
        self.game_session.save()

        self.user.player.character_creation_state = Player.CHARACTER_AVATAR_SELECTION
        self.user.player.save()

        # Test the GET method when the player has not selected a character avatar
        response = self.client.get(
            reverse("character_creation", kwargs={"game_id": self.game_session.game_id})
        )

        # Assertions
        self.assertIsInstance(response.context["form"], CharacterSelectionForm)

        self.user.player.character_creation_state = Player.MOON_MEANING_SELECTION
        self.user.player.save()

        response = self.client.get(
            reverse("character_creation", kwargs={"game_id": self.game_session.game_id})
        )

        self.assertIsInstance(response.context["form"], MoonSignInterpretationForm)

        self.user.player.character_creation_state = Player.PUBLIC_PROFILE_CREATION
        self.user.player.save()

        response = self.client.get(
            reverse("character_creation", kwargs={"game_id": self.game_session.game_id})
        )

        self.assertIsInstance(response.context["form"], PublicProfileCreationForm)

        self.user.player.character_creation_state = Player.CHARACTER_COMPLETE
        self.user.player.save()

        response = self.client.get(
            reverse("character_creation", kwargs={"game_id": self.game_session.game_id})
        )

        self.assertRedirects(
            response,
            self.game_session.get_absolute_url(),
        )

    def test_post_valid_form_submission(self):
        # Set the game session state to CHARACTER_CREATION
        self.game_session.state = GameSession.CHARACTER_CREATION
        self.game_session.save()

        self.user.player.character = self.test_character
        self.user.player.character_creation_state = Player.PUBLIC_PROFILE_CREATION
        self.user.player.save()

        # Test the POST method for invalid form submissions
        response = self.client.post(
            reverse(
                "character_creation", kwargs={"game_id": self.game_session.game_id}
            ),
            {
                "invalid_field": "invalid_value",
            },
        )

        # Assertions
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                message.message == "Please complete your character profile."
                for message in messages
            )
        )
        self.assertRedirects(
            response,
            reverse(
                "game:character_creation", kwargs={"game_id": self.game_session.game_id}
            ),
        )

        # Submit a valid form
        form_data = {
            "quality_1": self.test_character.quality_1_choices.first().id,
            "quality_2": self.test_character.quality_2_choices.first().id,
            "quality_3": self.test_character.quality_3_choices.first().id,
            "interest_1": self.test_character.interest_1_choices.first().id,
            "interest_2": self.test_character.interest_2_choices.first().id,
            "interest_3": self.test_character.interest_3_choices.first().id,
            "activity_1": self.test_character.activity_1_choices.first().id,
            "activity_2": self.test_character.activity_2_choices.first().id,
        }

        # Send the POST request with the form data
        response = self.client.post(
            reverse(
                "character_creation", kwargs={"game_id": self.game_session.game_id}
            ),
            form_data,
        )

        # Assertions
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                message.message == "Your dating profile has been updated."
                for message in messages
            )
        )

        # Assert that the players word pool has been updated with the correct words

        self.assertIn(
            self.test_character.quality_1_choices.first().words.first(),
            self.user.player.character_word_pool.all(),
        )
        self.assertIn(
            self.test_character.quality_2_choices.first().words.first(),
            self.user.player.character_word_pool.all(),
        )
        self.assertIn(
            self.test_character.quality_3_choices.first().words.first(),
            self.user.player.character_word_pool.all(),
        )

        # Assert that the players question pool has been updated with the correct question
        self.assertIn(
            self.test_character.activity_1_choices.first().questions.first(),
            self.user.player.question_pool.all(),
        )

        # Assert that the players narrative choice pool has been updated with the correct narrative choice
        self.assertIn(
            self.test_character.interest_3_choices.first().narrative_choices.first(),
            self.user.player.narrative_choice_pool.all(),
        )


class EndGameSessionViewTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.client = Client()
        self.user = User.objects.create_user(username="testuser")
        self.another_user = User.objects.create_user(username="testuser2")
        self.client.force_login(self.user)

        user1 = self.user
        user2 = self.another_user
        # Create a new game session and save it
        self.game_session = GameSession()
        game_session = self.game_session
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

    def test_get_valid_game_id_and_delete_successful(self):
        # Make the request
        response = self.client.get(
            reverse("end_game_session", kwargs={"game_id": self.game_session.game_id})
        )
        self.game_session.refresh_from_db()
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "end_game_session.html")
        self.assertEqual(self.game_session.state, GameSession.ENDED)

    def test_get_invalid_game_id(self):
        # Create a game id that does not exist
        while True:
            game_id = uuid.uuid4()
            if not GameSession.objects.filter(game_id=game_id).exists():
                break

        response = self.client.get(
            reverse("end_game_session", kwargs={"game_id": game_id})
        )

        # Assertions
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(message.message == "Game session not found." for message in messages)
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )

    def test_invalid_player(self):
        # Create a player object for a different user
        another_user = User.objects.create_user(username="another_user")
        new_game_session = GameSession()
        new_game_session.save()
        Player.objects.create(user=another_user, game_session=new_game_session)

        new_client = Client()
        new_client.force_login(another_user)

        # Make the request as the non-participant user
        response = new_client.get(
            reverse("end_game_session", kwargs={"game_id": self.game_session.game_id})
        )

        # Assertions
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                message.message == "You are not a participant of this game session."
                for message in messages
            )
        )
        self.assertRedirects(response, reverse("home"))


class InitiateGameSessionTestCase(TestCase):
    # Probably will delete when we remove the initiate game session page
    def setUp(self):
        # Set up test environment
        self.client = Client()
        self.user1 = User.objects.create_user("test1", "test1@example.com", "password")
        self.user2 = User.objects.create_user("test5", "prof@example.com", "password")
        # Create additional users for selectable users in GET request
        for i in range(2, 5):
            User.objects.create_user(f"test{i}", f"test{i}@example.com", "password")
        self.client.force_login(self.user1)

    def test_post_initiate_game_session(self):
        # Test POST request scenario
        url = reverse("initiate_game_session")  # Replace with your actual URL name
        response = self.client.post(url, {"selected_user": "test5"})

        # Assertions
        self.assertEqual(response.status_code, 302)  # Redirect status code
        game_session = GameSession.objects.first()
        self.assertIsNotNone(game_session)
        self.assertEqual(game_session.playerA.user, self.user1)
        self.assertEqual(game_session.playerB.user, self.user2)

    def test_get_initiate_game_session(self):
        # Test GET request scenario
        url = reverse("initiate_game_session")  # Replace with your actual URL name
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "initiate_game_session.html")
        self.assertIn("selectable_users", response.context)
        # Ensure the logged-in user is not in selectable_users
        self.assertNotIn(self.user1, response.context["selectable_users"])


class CharacterCreationViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.game_session = GameSession.objects.create(
            state=GameSession.CHARACTER_CREATION
        )
        self.player = Player.objects.create(
            user=self.user,
            game_session=self.game_session,
            character_creation_state=Player.CHARACTER_AVATAR_SELECTION,
        )
        self.client.force_login(self.user)

    def test_character_avatar_selection_get(self):
        response = self.client.get(
            reverse("character_creation", kwargs={"game_id": self.game_session.game_id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "character_creation.html")

    def test_redirect_when_not_in_character_creation_state(self):
        # Fetch the existing player object
        player = Player.objects.get(user=self.user)

        # Set up a game session in a different state
        game_session = GameSession.objects.create(state=GameSession.REGULAR_TURN)
        player.game_session = game_session
        player.save()

        # Make a GET request to the view
        response = self.client.get(
            reverse("character_creation", kwargs={"game_id": game_session.game_id}),
            follow=False,
        )

        # Check that the response is a redirect
        self.assertEqual(response.status_code, 302)

        # Check the URL of the redirect without following it
        expected_url = game_session.get_absolute_url()
        self.assertTrue(response["Location"].endswith(expected_url))

    def test_game_session_does_not_exist(self):
        non_existent_game_id = uuid4()  # Generate a random UUID
        response = self.client.get(
            reverse("character_creation", kwargs={"game_id": non_existent_game_id})
        )
        self.assertRedirects(
            response, reverse("home")
        )  # Update 'home' to your home URL name

    def test_post_character_avatar_selection(self):
        self.player.character_creation_state = Player.CHARACTER_AVATAR_SELECTION
        self.player.save()

        # Create a Character object for the test
        character = Character.objects.create(
            # Set the necessary fields for your Character model
            name="Test Character",
            description="Test Description",
        )

        post_data = {"character": character.id}

        response = self.client.post(
            reverse(
                "character_creation", kwargs={"game_id": self.game_session.game_id}
            ),
            post_data,
        )
        self.assertEqual(response.status_code, 302)  # or other expected behavior

    def test_post_moon_meaning_selection(self):
        self.player.character_creation_state = Player.MOON_MEANING_SELECTION
        self.player.save()

        post_data = {
            "first_quarter": "positive",
            "first_quarter_reason": "Some reason",
            "full_moon": "negative",
            "full_moon_reason": "Another reason",
        }

        response = self.client.post(
            reverse(
                "character_creation", kwargs={"game_id": self.game_session.game_id}
            ),
            post_data,
        )
        self.assertEqual(response.status_code, 302)  # or other expected behavior

    def test_post_public_profile_creation(self):
        # Create a Character instance for the test
        character = Character.objects.create(
            # Set the necessary fields for your Character model
            name="Test Character",
            description="Test Description",
        )

        # Associate the character with the player
        self.player.character = character
        self.player.character_creation_state = Player.PUBLIC_PROFILE_CREATION
        self.player.save()

        # Create necessary instances for the test
        quality1 = Quality.objects.create(name="Quality 1")
        quality2 = Quality.objects.create(name="Quality 2")
        quality3 = Quality.objects.create(name="Quality 3")
        interest1 = Interest.objects.create(name="Interest 1")
        # ... similarly create instances for other fields

        # Update your character instance to include these choices
        character.quality_1_choices.add(quality1, quality2, quality3)
        character.interest_1_choices.add(interest1)
        # ... similarly add instances to other choice fields
        character.save()

        post_data = {
            "quality_1": quality1.id,
            "quality_2": quality2.id,
            "quality_3": quality3.id,
            "interest_1": interest1.id,
        }

        response = self.client.post(
            reverse(
                "character_creation", kwargs={"game_id": self.game_session.game_id}
            ),
            post_data,
        )
        self.assertEqual(response.status_code, 302)  # or other expected behavior

    def test_general_exception_handling(self):
        # Mock a method in the view that could raise an exception
        with patch("game.models.GameSession.objects.get") as mock_get:
            mock_get.side_effect = Exception("Test exception")

            # Perform the POST request
            response = self.client.post(
                reverse(
                    "character_creation", kwargs={"game_id": self.game_session.game_id}
                ),
                {"dummy_key": "dummy_value"},
            )

            # Check if the response is a correct redirect but don't follow it
            self.assertRedirects(
                response,
                reverse("home"),
                status_code=302,
                target_status_code=200,
                fetch_redirect_response=False,
            )

            # Check if the correct error message is set
            messages = list(get_messages(response.wsgi_request))
            self.assertIn("Test exception", [str(message) for message in messages])

    def test_redirect_non_character_creation_state_post(self):
        # Set up a game session in a state other than CHARACTER_CREATION
        game_session_different_state = GameSession.objects.create(
            state=GameSession.REGULAR_TURN
        )
        self.player.game_session = game_session_different_state
        self.player.save()

        # Create minimal post data for the request
        post_data = {
            "dummy_key": "dummy_value"
        }  # Adjust based on what your view might expect

        # Make a POST request to the view
        response = self.client.post(
            reverse(
                "character_creation",
                kwargs={"game_id": game_session_different_state.game_id},
            ),
            post_data,
        )

        # Check that the response is a redirect to the game progress URL
        self.assertRedirects(
            response,
            game_session_different_state.get_absolute_url(),
            fetch_redirect_response=False,
        )

    def test_valid_moon_meaning_selection_post(self):
        self.player.character_creation_state = Player.MOON_MEANING_SELECTION
        self.player.save()

        post_data = {
            "first_quarter": "positive",
            "first_quarter_reason": "Some reason",
            "full_moon": "negative",
            "full_moon_reason": "Another reason",
            "last_quarter": "ambiguous",
            "last_quarter_reason": "Yet another reason",
            "new_moon": "ambiguous",
            "new_moon_reason": "Different reason",
        }

        with patch.object(Player, "select_moon_meaning") as mock_select_moon_meaning:
            mock_select_moon_meaning.return_value = None

            response = self.client.post(
                reverse(
                    "character_creation", kwargs={"game_id": self.game_session.game_id}
                ),
                post_data,
            )

            # Check response and form validity
            if response.context:
                form = response.context.get("form")
                if form and not form.is_valid():
                    print("Form errors:", form.errors)

            # Refresh the player instance to ensure it's up to date
            self.player.refresh_from_db()

            # Check that the select_moon_meaning method was called with the recently created MoonSignInterpretation
            mock_select_moon_meaning.assert_called_once_with(
                moon_meaning=MoonSignInterpretation.objects.first()
            )

            self.assertEqual(response.status_code, 302)

    def test_direct_select_moon_meaning_call(self):
        player, created = Player.objects.get_or_create(
            user=self.user, defaults={"game_session": self.game_session}
        )

        # Set the player to the correct state before calling select_moon_meaning
        player.character_creation_state = Player.MOON_MEANING_SELECTION
        player.save()

        # Create a MoonSignInterpretation() instance for the test, associate with the player
        moon_sign_interpretation = MoonSignInterpretation.objects.create(
            first_quarter="positive",
            first_quarter_reason="Some reason",
            full_moon="negative",
            full_moon_reason="Another reason",
            last_quarter="ambiguous1",
            last_quarter_reason="Yet another reason",
            new_moon="ambiguous2",
            new_moon_reason="Different reason",
            player=player,
        )

        # Directly call the method
        player.select_moon_meaning(moon_meaning=moon_sign_interpretation)

        # Add assertions as needed to check the result of the method call
        # For example, check the state of the player or other side effects
        assert player.character_creation_state == Player.PUBLIC_PROFILE_CREATION
        assert player.MoonSignInterpretation == moon_sign_interpretation

    def test_game_session_does_not_exist(self):
        # Simulate a non-existent game session by using a random UUID
        non_existent_game_id = uuid4()

        # Make a GET request to the view
        response = self.client.get(
            reverse("character_creation", kwargs={"game_id": non_existent_game_id})
        )

        # Check that the response is a redirect
        self.assertEqual(response.status_code, 302)

        # Check that it redirects to the home URL
        self.assertRedirects(response, reverse("home"))

        # Extract messages from the response
        messages = list(get_messages(response.wsgi_request))

        # Check if the specific error message is present
        self.assertTrue(
            any(msg.message == "Game session not found." for msg in messages)
        )


class CharacterDetailsTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a sample character for testing
        self.character = Character.objects.create(
            name="Test Character",
            description="Test Description",
            # If your Character model has an image field, handle it accordingly
            image=SimpleUploadedFile(
                name="test_image.jpg", content=b"", content_type="image/jpeg"
            ),
        )

    def tearDown(self):
        # Clean up the test image file
        if self.character.image:
            self.character.image.delete(
                save=False
            )  # Delete the image file, but don't save the model

        # Optionally, delete the character object itself
        self.character.delete()

    def test_no_character_id_provided(self):
        response = self.client.get(
            reverse("get_character_details")
        )  # Update with your actual URL name
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "No character ID provided"})

    def test_character_found(self):
        response = self.client.get(
            reverse("get_character_details"), {"id": self.character.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "name": self.character.name,
                "description": self.character.description,
                "image_url": self.character.image.url if self.character.image else "",
            },
        )

    def test_character_not_found(self):
        non_existent_character_id = 999999  # An ID unlikely to exist

        response = self.client.get(
            reverse("get_character_details"),  # Replace with your actual URL name
            {"id": non_existent_character_id},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Character not found"})
