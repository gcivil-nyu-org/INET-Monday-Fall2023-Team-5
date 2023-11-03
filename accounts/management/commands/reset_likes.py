from django.core.management.base import BaseCommand
from accounts.models import Profile, Like

class Command(BaseCommand):
    help = "Resets the number of likes for all users to 3 and clears all likes"

    def handle(self, *args, **kwargs):
        # Clear all the likes
        Like.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Successfully cleared all likes"))

        # Reset the like counters
        Profile.objects.update(likes_remaining=3)
        self.stdout.write(self.style.SUCCESS("Successfully reset likes for all users"))
