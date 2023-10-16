from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'pronoun_preference', 'open_to_dating']  # Display fields in list view
    # Add any other desired configurations.
