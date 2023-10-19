from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'pronoun_preference', 'display_open_to_dating']  # Use the custom method here
    
    # Define the custom method
    def display_open_to_dating(self, obj):
        return ", ".join([preference.gender for preference in obj.open_to_dating.all()])

    # Provide a short description for the column header
    display_open_to_dating.short_description = "Open to Dating"