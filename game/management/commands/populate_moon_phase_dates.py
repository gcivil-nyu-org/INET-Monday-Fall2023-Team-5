from datetime import datetime
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
import requests
import pytz
from game.models import moon_phase_dates


class Command(BaseCommand):
    help = "Populates the database with moon phase dates up to the year 2100"

    def handle(self, *args, **kwargs):
        api_url = "https://aa.usno.navy.mil/api/moon/phases/year"
        utc_zone = pytz.utc
        eastern_zone = pytz.timezone("America/New_York")

        for year in range(datetime.now().year, 2101):  # From current year to 2100
            response = requests.get(f"{api_url}?year={year}")
            if response.status_code == 200:
                data = response.json()
                for phase in data.get("phasedata", []):
                    try:
                        # Convert UTC time to Eastern Time
                        utc_time = datetime(
                            phase["year"],
                            phase["month"],
                            phase["day"],
                            int(phase["time"].split(":")[0]),
                            int(phase["time"].split(":")[1]),
                        )
                        utc_time = utc_zone.localize(utc_time)
                        eastern_time = utc_time.astimezone(eastern_zone)

                        # Adjust the date if time conversion changes the day
                        moon_phase_date = eastern_time.date()

                        moon_phase_dates.objects.get_or_create(
                            moon_phase=phase["phase"].replace(" ", "_").lower(),
                            date=moon_phase_date,
                        )
                        print(f"Added {phase} on date {moon_phase_date}")
                    except IntegrityError:
                        self.stdout.write(
                            self.style.ERROR(f"Duplicate entry for {phase} not added")
                        )
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to retrieve data for year {year}")
                )

        self.stdout.write(self.style.SUCCESS("Successfully populated moon phase dates"))
