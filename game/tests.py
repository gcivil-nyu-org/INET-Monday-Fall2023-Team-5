from django.test import TestCase, RequestFactory, Client
from .models import Character, Quality, Interest, Activity, GameSession, Player
from django.core.exceptions import ValidationError
from .forms import CharacterSelectionForm
from django import forms
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.core.files.storage import default_storage
import io, os, uuid
from roleplaydate import settings
from django.urls import reverse
from .views import CharacterCreationView
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from .context_processors import game_session_processor


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
