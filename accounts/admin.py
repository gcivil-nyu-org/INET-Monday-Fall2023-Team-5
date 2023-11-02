from django.contrib import admin
from .models import Profile, DatingPreference, Like


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "pronoun_preference",
        "display_open_to_dating",
    ]  # Use the custom method here

    # Define the custom method
    def display_open_to_dating(self, obj):
        return ", ".join([preference.gender for preference in obj.open_to_dating.all()])

    # Provide a short description for the column header
    display_open_to_dating.short_description = "Open to Dating"


admin.site.register(DatingPreference)


class LikeAdmin(admin.ModelAdmin):
    list_display = (
        "from_user",
        "to_user",
        "created_at",
    )  # Fields to display in the admin list view
    search_fields = (
        "from_user__username",
        "to_user__username",
    )  # Fields to search in the admin
    list_filter = ("created_at",)  # Fields to filter in the admin list view
    ordering = ("-created_at",)  # Default ordering


# Register the Like model with the admin site
admin.site.register(Like, LikeAdmin)
