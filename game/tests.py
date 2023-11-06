from django.contrib.messages import get_messages
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Player, GameSession, GameTurn, generate_unique_game_id
from .forms import QuestionSelectForm, AnswerForm, EmojiReactForm, NarrativeChoiceForm


class GameViewTests(TestCase):
    def setUp(self):
        # Set up data for the tests
        self.client = Client()
        self.user1 = User.objects.create_user(username="admin5", password="password123")
        self.user2 = User.objects.create_user(username="admin6", password="password123")

    def test_initiate_game_session_post(self):
        # Test POST request to initiate_game_session
        self.client.login(username="admin5", password="password123")
        response = self.client.post(reverse("initiate_game_session"), follow=True)
        self.assertEqual(response.status_code, 200)
        # Check if the game session and players are created
        game_session = GameSession.objects.last()
        self.assertIsNotNone(game_session)
        self.assertEqual(game_session.playerA.user.username, "admin5")
        self.assertEqual(game_session.playerB.user.username, "admin6")
        self.assertRedirects(
            response, reverse("game_progress", kwargs={"game_id": game_session.game_id})
        )


class GameProgressViewTest(TestCase):
    def __init__(self, methodName: str = ...):
        super().__init__(methodName)
        self.game_session = None

    def setUp(self):
        # Set up data for the tests
        self.client = Client()
        self.user1 = User.objects.create_user(username="admin5", password="password123")
        self.user2 = User.objects.create_user(username="admin6", password="password123")

        self.client.login(username="admin5", password="password123")
        response = self.client.post(reverse("initiate_game_session"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.game_session = GameSession.objects.last()

    def test_get_with_valid_session(self):
        # Log the user in
        self.client.login(username="admin6", password="password123")

        # Get response using the 'game_progress' url
        url = reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        response = self.client.get(url)

        # Assert that the user retrieves the page correctly
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context["game_session"], self.game_session)

    def test_get_with_invalid_session(self):
        # Log the user in
        self.client.login(username="admin5", password="12345")
        # This should not conflict with the game_session id created in setUp, as it guarantees a unique id
        unique_uuid = generate_unique_game_id()
        # Use a non-existing game_id
        response = self.client.get(
            reverse("game_progress", kwargs={"game_id": unique_uuid}),
            follow=True,
        )
        # Now, check the final response after all redirects
        self.assertEqual(response.status_code, 200)

    def test_get_with_non_participant_user(self):
        # Create another user and associate player
        User.objects.create_user(username="otheruser", password="67890")
        Player.objects.create(
            user=User.objects.get(username="otheruser"), game_session=self.game_session
        )

        # Log the testuser in
        self.client.login(username="otheruser", password="67890")

        # Try to access game session of admin5
        url = reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        response = self.client.get(url)

        # User should be redirected to the 'home' url
        self.assertRedirects(response, reverse("home"))


class EndGameSessionViewTest(TestCase):
    def setUp(self):
        # Create a game session
        self.game_session = GameSession.objects.create()
        # Create two users and associate players
        self.user1 = User.objects.create_user(username="testuser1", password="12345")
        self.player1 = Player.objects.create(
            user=self.user1, game_session=self.game_session
        )
        self.user2 = User.objects.create_user(username="testuser2", password="12345")
        self.player2 = Player.objects.create(
            user=self.user2, game_session=self.game_session
        )

        # Create a game session
        self.game_session.playerA = self.player1
        self.game_session.playerB = self.player2

        self.game_session.save()

        # Client to simulate browser
        self.client = Client()

    def test_end_game_session_valid(self):
        self.client.login(username="testuser1", password="12345")
        response = self.client.get(
            reverse("end_game_session", kwargs={"game_id": self.game_session.game_id})
        )
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            "Game session ended successfully." in [m.message for m in messages]
        )
        self.assertRedirects(response, reverse("initiate_game_session"))

    def test_end_game_session_invalid_user(self):
        # Create another user who is not a participant of the game
        User.objects.create_user(username="otheruser", password="12345")
        self.client.login(username="otheruser", password="12345")
        response = self.client.get(
            reverse("end_game_session", kwargs={"game_id": self.game_session.game_id})
        )
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            "You are not a participant of this game session."
            in [m.message for m in messages]
        )
        self.assertRedirects(
            response, reverse("home")
        )  # Adjust the redirect to your home view

    def test_end_game_session_not_found(self):
        self.client.login(username="testuser1", password="12345")
        response = self.client.get(
            reverse("end_game_session", kwargs={"game_id": generate_unique_game_id()})
        )
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(response.status_code, 302)
        self.assertTrue("Game session not found." in [m.message for m in messages])
        self.assertRedirects(response, reverse("initiate_game_session"))
