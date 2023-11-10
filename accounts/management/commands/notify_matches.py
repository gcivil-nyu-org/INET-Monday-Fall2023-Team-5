from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
import logging
from game.models import GameSession, Player
from accounts.models import Match

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
                with transaction.atomic():
                    game_session = GameSession(is_active=True)
                    game_session.save()

                    playerA, _ = Player.objects.get_or_create(
                        user=match.user1, defaults={"game_session": game_session}
                    )
                    playerB, _ = Player.objects.get_or_create(
                        user=match.user2, defaults={"game_session": game_session}
                    )

                    game_session.playerA = playerA
                    game_session.playerB = playerB
                    game_session.save()

                    if not game_session.current_game_turn_id:
                        game_session.initialize_game()

                try:
                    self.send_email(match.user1, "You have a new match!")
                    self.send_email(match.user2, "You have a new match!")

                    match.notification_sent = True
                    match.save()

                    success_message = (
                        f"Notification sent for match between {match.user1.username} "
                        f"and {match.user2.username}."
                    )
                    self.stdout.write(self.style.SUCCESS(success_message))

                except Exception as e:
                    logger.error(f"Error sending email: {e}")
                    self.stderr.write(self.style.ERROR(f"Error sending email: {e}"))
                    raise CommandError(f"Error sending email: {e}")

            except CommandError as ce:
                logger.error(str(ce))
                self.stderr.write(self.style.ERROR(str(ce)))
                raise  # Re-raise the CommandError so it can be caught by the test

    def send_email(self, user, subject):
        message = (
            f"Hello {user.username},\n\n"
            "Exciting news! You've been matched in 'Roleplay and then Date'. "
            "This isn't just another swipe-and-match encounter. Prepare yourself for "
            "an immersive journey of anonymous role-playing, and a unique 28-day "
            "narrative that lets you connect with your match on a deeper level.\n\n"
            "Log in to the app and play the game with your companion in this adventure "
            "of moonlit tales and mysterious connections. "
            "Once inside, you can embark on your journey together and see where the "
            "story takes you.\n\n"
            "Your moonlit adventure awaits!\n\n"
            "Best wishes,\n"
            "The Roleplay and then Date Team"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
