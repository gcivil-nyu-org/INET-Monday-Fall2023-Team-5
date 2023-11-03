from django.core.management.base import BaseCommand
from accounts.models import Profile, Like

class Command(BaseCommand):
    help = "Resets the number of likes for all users to 3 and clears all likes"

    def add_arguments(self, parser):
        parser.add_argument('--dbname', help='Database name', default='default')

    def handle(self, *args, **options):
        # If --dbname is provided, you can use it to connect to a specific database
        db_name = options['dbname']
        # Ensure your database operations target the 'db_name' database
        # For example, Like.objects.using(db_name).all().delete()

        # Clear all the likes
        Like.objects.using(db_name).all().delete()
        self.stdout.write(self.style.SUCCESS("Successfully cleared all likes"))

        # Reset the like counters
        Profile.objects.using(db_name).update(likes_remaining=3)
        self.stdout.write(self.style.SUCCESS("Successfully reset likes for all users"))
