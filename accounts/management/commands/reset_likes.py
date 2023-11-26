from django.core.management.base import BaseCommand
from accounts.models import Profile, Like


class Command(BaseCommand):
    help = "Resets the number of likes for all users to 3 and clears all likes"

    def add_arguments(self, parser):
        parser.add_argument("--dbname", type=str, help="Optional database name")

    def handle(self, *args, **options):
        dbname = options.get("dbname")
        if dbname:
            self.stdout.write(f"Using database: {dbname}")

        # Clear all the likes
        Like.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Successfully cleared all likes"))

        # Reset the like counters
        Profile.objects.update(likes_remaining=3)
        self.stdout.write(self.style.SUCCESS("Successfully reset likes for all users"))
