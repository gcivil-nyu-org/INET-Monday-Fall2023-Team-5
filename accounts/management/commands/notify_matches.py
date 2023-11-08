from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import logging

from accounts.models import Match
from game.models import GameSession, Player

# Configure a logger for the command
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Sends notifications to users about new matches at midnight."

    def handle(self, *args, **options):
        yesterday = timezone.now() - timedelta(days=1)
        new_matches = Match.objects.filter(
            matched_at__gte=yesterday, notification_sent=False
        )

        for match in new_matches:
            try:
                # Create a game session for the match
                game_session, created = GameSession.objects.get_or_create(
                    playerA__user=match.user1,
                    playerB__user=match.user2,
                    defaults={
                        'playerA': Player.objects.get_or_create(user=match.user1)[0],
                        'playerB': Player.objects.get_or_create(user=match.user2)[0],
                        'is_active': True,  # Assuming you want to start the session as active
                    }
                )
                
                # Ensure the game session is initialized properly
                if created and not game_session.current_game_turn_id:
                    game_session.initialize_game()

                # Generate the URL for the game session
                game_session_url = self.get_full_url_with_domain(game_session.get_absolute_url())

                # Email messages including the game session link
                user1_msg = (
                    f"Hello {match.user1.username},\n\n"
                    "You have been matched with someone on our platform. "
                    "Please log in to see more details about your match."
                    f"\n\nClick here to join the game: {game_session_url}"
                )
                user2_msg = (
                    f"Hello {match.user2.username},\n\n"
                    "You have been matched with someone on our platform. "
                    "Please log in to see more details about your match."
                    f"\n\nClick here to join the game: {game_session_url}"
                )

                # Send notification to user1
                send_mail(
                    subject="You have a new match!",
                    message=user1_msg,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[match.user1.email],
                    fail_silently=False,
                )
                # Send notification to user2
                send_mail(
                    subject="You have a new match!",
                    message=user2_msg,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[match.user2.email],
                    fail_silently=False,
                )

                # Mark the match as notified
                match.notification_sent = True
                match.save()

                success_message = (
                    f"Notification sent for match between "
                    f"{match.user1.username} and {match.user2.username}. "
                    f"Game session link included: {game_session_url}"
                )
                self.stdout.write(self.style.SUCCESS(success_message))

            except Exception as e:
                error_message = (
                    f"Failed to send notification for match between "
                    f"{match.user1.username} and {match.user2.username}: {e}"
                )
                logger.error(error_message)
                self.stderr.write(self.style.ERROR(error_message))
    
    def get_full_url_with_domain(self, relative_url):
        # Ensure that SITE_URL ends with a slash
        site_url = settings.SITE_URL if settings.SITE_URL.endswith('/') else settings.SITE_URL + '/'
        return f"{site_url}{relative_url.lstrip('/')}"

# In your settings.py, make sure to define the SITE_URL like so:
# SITE_URL = 'http://roleplaydate-dev3.us-east-1.elasticbeanstalk.com/'
