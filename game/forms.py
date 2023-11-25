from django import forms

from .models import (
    Character,
    PublicProfile,
)  # Ensure this import is correct based on your project structure


class AnswerForm(forms.Form):
    answer = forms.CharField(
        widget=forms.HiddenInput(),
    )


class EmojiReactForm(forms.Form):
    EMOJI_CHOICES = (
        ("🌑", "🌑"),
        ("🌓", "🌓"),
        ("🌕", "🌕"),
        ("🌗", "🌗"),
    )
    emoji = forms.ChoiceField(
        choices=EMOJI_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "emoji-radio"}),
        label="React with an Emoji",
    )


class NarrativeChoiceForm(forms.Form):
    NARRATIVE_CHOICES = (
        ("choice1", "Choice 1 Description"),
        ("choice2", "Choice 2 Description"),
        # ... add other choices as needed
    )
    narrative = forms.ChoiceField(
        choices=NARRATIVE_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "narrative-radio"}),
        label="Select a Narrative Choice",
    )


class CharacterSelectionForm(forms.Form):
    character = forms.ModelChoiceField(
        queryset=Character.objects.all(),
        widget=forms.RadioSelect(attrs={"onclick": "loadCharacterDetails(this)"}),
        empty_label=None,
        to_field_name="id",
    )


class PublicProfileCreationForm(forms.ModelForm):
    class Meta:
        model = PublicProfile
        fields = [
            "quality_1",
            "quality_2",
            "quality_3",
            "interest_1",
            "interest_2",
            "interest_3",
            "activity_1",
            "activity_2",
        ]

    def __init__(self, *args, **kwargs):
        character = kwargs.pop("character", None)
        super().__init__(*args, **kwargs)

        if character:
            self.fields["quality_1"].choices = [
                (q.id, q.name) for q in character.quality_1_choices.all()
            ]
            self.fields["quality_2"].choices = [
                (q.id, q.name) for q in character.quality_2_choices.all()
            ]
            self.fields["quality_3"].choices = [
                (q.id, q.name) for q in character.quality_3_choices.all()
            ]
            self.fields["interest_1"].choices = [
                (q.id, q.name) for q in character.interest_1_choices.all()
            ]
            self.fields["interest_2"].choices = [
                (q.id, q.name) for q in character.interest_2_choices.all()
            ]
            self.fields["interest_3"].choices = [
                (q.id, q.name) for q in character.interest_3_choices.all()
            ]
            self.fields["activity_1"].choices = [
                (q.id, q.name) for q in character.activity_1_choices.all()
            ]
            self.fields["activity_2"].choices = [
                (q.id, q.name) for q in character.activity_2_choices.all()
            ]
