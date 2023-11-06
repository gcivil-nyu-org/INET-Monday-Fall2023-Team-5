from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Player, GameSession, GameTurn
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
        self.assertEqual(response.status_code, 302)
        # Check if the game session and players are created
        game_session = GameSession.objects.last()
        self.assertIsNotNone(game_session)
        self.assertEqual(game_session.playerA.user.username, "admin5")
        self.assertEqual(game_session.playerB.user.username, "admin6")
        self.assertRedirects(
            response, reverse("game_progress", kwargs={"game_id": game_session.game_id})
        )


"""    def test_game_progress_view_get(self):
        # Test GET request to GameProgressView
        self.client.login(username="admin5", password="password123")
        response = self.client.post(reverse("initiate_game_session"), follow=True)
        game_session = GameSession.objects.last()
        self.client.login(username="admin5", password="password123")
        response = self.client.get(
            reverse("game_progress", kwargs={"game_id": self.game_session.game_id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "game_progress.html")
        
    def test_end_game_session(self):
        # Test end_game_session view
        self.client.login(username="admin5", password="password123")
        response = self.client.get(
            reverse("end_game_session", kwargs={"game_id": self.game_session.game_id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("initiate_game"))
        self.game_session.refresh_from_db()
        # Check if game_session status has been updated accordingly"""
