from django.db.models.signals import post_save, post_migrate
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, DatingPreference


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


@receiver(post_migrate)
def add_default_dating_preferences(sender, **kwargs):
    DatingPreference.create_defaults()
