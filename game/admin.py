from django.contrib import admin
from .models import (
    Player,
    GameSession,
    GameTurn,
    Question,
    Word,
    ChatMessage,
    NarrativeChoice,
    Character,
)

# Register your models here.
admin.site.register(Player)
admin.site.register(GameSession)
admin.site.register(GameTurn)
admin.site.register(Question)
admin.site.register(Word)
admin.site.register(ChatMessage)
admin.site.register(NarrativeChoice)


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "description",
    )
    search_fields = ("name",)
