# Generated by Django 4.2 on 2023-12-03 22:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="moonsigninterpretation",
            name="on_player",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="game.player",
            ),
        ),
        migrations.AddField(
            model_name="player",
            name="MoonSignInterpretation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="game.moonsigninterpretation",
            ),
        ),
    ]