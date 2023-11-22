from django.contrib import admin
from .models import (
    Player,
    GameSession,
    GameTurn,
    Question,
    Word,
    ChatMessage,
    NarrativeChoice,
    Character
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
    list_display = ('name', 'description', 'quality_1_choices', 'quality_2_choices', 'quality_3_choices', 'interest_1_choices', 'interest_2_choices', 'interest_3_choices', 'activity_1_choices', 'activity_2_choices')
    search_fields = ('name',)

