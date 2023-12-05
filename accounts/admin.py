from django.contrib import admin
from .models import Profile, DatingPreference, Like, Match


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


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "created_at", "is_mutual")
    list_filter = ("from_user", "to_user")
    search_fields = ("from_user__username", "to_user__username")
    actions = ["make_mutual"]

    def make_mutual(self, request, queryset):
        for like in queryset:
            # Here you would implement the logic to check and create a mutual like
            pass

    make_mutual.short_description = "Mark selected likes as mutual"

    def is_mutual(self, obj):
        return obj.is_mutual()

    is_mutual.boolean = True
    is_mutual.short_description = "Mutual Like"




@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "user1",
        "user2",
        "matched_at",
        "notification_sent",
    )  # Add notification_sent
    search_fields = ("user1__username", "user2__username")
    list_filter = (
        "notification_sent",
    )  # Optional: to filter matches by notification status
