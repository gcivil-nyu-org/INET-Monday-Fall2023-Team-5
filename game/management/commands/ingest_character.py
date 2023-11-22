from django.core.management.base import BaseCommand
import json
from game.tools.character_ingest import ingest_json_data  # Import your function


class Command(BaseCommand):
    help = "Ingest data from a JSON file into the database"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="Path to the JSON file")

    def handle(self, *args, **options):
        json_file = options["json_file"]

        with open(json_file, "r") as file:
            json_data = json.load(file)

        ingest_json_data(json_data)
        self.stdout.write(self.style.SUCCESS("Successfully ingested data"))
