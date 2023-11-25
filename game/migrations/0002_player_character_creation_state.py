# Generated by Django 4.2 on 2023-11-25 00:44

from django.db import migrations
import django_fsm


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="character_creation_state",
            field=django_fsm.FSMField(
                choices=[
                    ("character_avatar_selection", "Character Avatar Selection"),
                    ("moon_meaning_selection", "Moon Meaning Selection"),
                    ("public_profile_creation", "Public Profile Creation"),
                    ("character_complete", "Character Complete"),
                ],
                default="character_avatar_selection",
                max_length=50,
            ),
        ),
    ]