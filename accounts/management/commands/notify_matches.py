from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import Match
from django.core.mail import send_mail
from django.conf import settings
import logging

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
                user1_msg = (
                    f"Hello {match.user1.username},\n\n"
                    "You have been matched with someone on our platform. "
                    "Please log in to see more details about your match."
                )
                user2_msg = (
                    f"Hello {match.user2.username},\n\n"
                    "You have been matched with someone on our platform. "
                    "Please log in to see more details about your match."
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
                    f"{match.user1.username} and {match.user2.username}"
                )
                self.stdout.write(self.style.SUCCESS(success_message))

            except Exception as e:
                error_message = (
                    f"Failed to send notification for match between "
                    f"{match.user1.username} and {match.user2.username}: {e}"
                )
                logger.error(error_message)
                self.stderr.write(self.style.ERROR(error_message))
