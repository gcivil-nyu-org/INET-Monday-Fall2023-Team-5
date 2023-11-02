from django.core.management.base import BaseCommand
from accounts.models import Profile


class Command(BaseCommand):
    help = "Resets the number of likes for all users to 3"

    def handle(self, *args, **kwargs):
        Profile.objects.update(likes_remaining=3)
        self.stdout.write(self.style.SUCCESS("Successfully reset likes for all users"))
