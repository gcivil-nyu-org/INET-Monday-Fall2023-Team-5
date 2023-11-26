from django import forms
from .models import (
    Character,
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


class MoonSignInterpretationForm(forms.Form):
    MOON_SIGN_CHOICES = [
        ("positive", "Positive"),
        ("negative", "Negative"),
        ("ambiguous1", "Ambiguous 1"),
        ("ambiguous2", "Ambiguous 2"),
    ]

    first_quarter = forms.ChoiceField(
        choices=MOON_SIGN_CHOICES,
        label="The First Quarter is a",
        widget=forms.RadioSelect,
    )
    first_quarter_reason = forms.CharField(
        max_length=150,
        label="because",
        widget=forms.TextInput(attrs={"placeholder": "Your reason..."}),
    )

    full_moon = forms.ChoiceField(
        choices=MOON_SIGN_CHOICES, label="The Full Moon is a", widget=forms.RadioSelect
    )
    full_moon_reason = forms.CharField(
        max_length=150,
        label="because",
        widget=forms.TextInput(attrs={"placeholder": "Your reason..."}),
    )

    last_quarter = forms.ChoiceField(
        choices=MOON_SIGN_CHOICES,
        label="The Last Quarter is a",
        widget=forms.RadioSelect,
    )
    last_quarter_reason = forms.CharField(
        max_length=150,
        label="because",
        widget=forms.TextInput(attrs={"placeholder": "Your reason..."}),
    )

    new_moon = forms.ChoiceField(
        choices=MOON_SIGN_CHOICES, label="The New Moon is a", widget=forms.RadioSelect
    )
    new_moon_reason = forms.CharField(
        max_length=150,
        label="because",
        widget=forms.TextInput(attrs={"placeholder": "Your reason..."}),
    )
