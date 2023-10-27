from django.db import migrations


def update_gender_descriptions_to_codes(apps, schema_editor):
    Profile = apps.get_model("accounts", "Profile")

    # Update Profile model
    # (this part assumes there are no profiles set to "Not Specified" yet)
    profile_gender_mapping = {
        "Male": "M",
        "Female": "F",
        "Non-binary": "N",
    }

    for profile in Profile.objects.all():
        profile.gender = profile_gender_mapping.get(profile.gender, profile.gender)
        profile.save()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0009_auto_20231019_1046"),
    ]

    operations = [
        migrations.RunPython(
            update_gender_descriptions_to_codes, reverse_code=migrations.RunPython.noop
        )
    ]
