from django import forms
from django.core.exceptions import ValidationError

from .models import (
    Character,
)  # Ensure this import is correct based on your project structure


class AnswerForm(forms.Form):
    answer = forms.CharField(
        widget=forms.HiddenInput(),
    )


class AnswerFormMoon(forms.Form):
    moon_answer = forms.CharField(
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
        label="React with an Emoji",
    )

    def __init__(self, *args, **kwargs):
        super(EmojiReactForm, self).__init__(*args, **kwargs)
        self.fields["emoji"].widget = forms.RadioSelect(attrs={"class": "emoji-radio"})
        self.fields["emoji"].widget.choices = self.EMOJI_CHOICES


class NarrativeChoiceForm(forms.Form):
    NARRATIVE_CHOICES = ()
    narrative = forms.ChoiceField(
        choices=NARRATIVE_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "narrative-radio"}),
        label="Select a Narrative Choice",
    )

    def __init__(self, *args, **kwargs):
        player = kwargs.pop("player", None)
        night = kwargs.pop("night", None)
        super().__init__(*args, **kwargs)

        if player:
            self.fields["narrative"].choices = [
                (n.id, n.name)
                for n in player.narrative_choice_pool.filter(night_number=night)
            ]


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
        ("ambiguous", "Ambiguous"),
    ]

    first_quarter = forms.ChoiceField(
        choices=MOON_SIGN_CHOICES,
        label="The First Quarter is a",
        widget=forms.RadioSelect(attrs={"id": "id_first_quarter"}),
    )
    first_quarter_reason = forms.CharField(
        max_length=150,
        label="because",
        widget=forms.TextInput(attrs={"placeholder": "Your reason..."}),
    )

    full_moon = forms.ChoiceField(
        choices=MOON_SIGN_CHOICES,
        label="The Full Moon is a",
        widget=forms.RadioSelect(attrs={"id": "id_full_moon"}),
    )
    full_moon_reason = forms.CharField(
        max_length=150,
        label="because",
        widget=forms.TextInput(attrs={"placeholder": "Your reason..."}),
    )

    last_quarter = forms.ChoiceField(
        choices=MOON_SIGN_CHOICES,
        label="The Last Quarter is a",
        widget=forms.RadioSelect(attrs={"id": "id_last_quarter"}),
    )
    last_quarter_reason = forms.CharField(
        max_length=150,
        label="because",
        widget=forms.TextInput(attrs={"placeholder": "Your reason..."}),
    )

    new_moon = forms.ChoiceField(
        choices=MOON_SIGN_CHOICES,
        label="The New Moon is a",
        widget=forms.RadioSelect(attrs={"id": "id_new_moon"}),
    )
    new_moon_reason = forms.CharField(
        max_length=150,
        label="because",
        widget=forms.TextInput(attrs={"placeholder": "Your reason..."}),
    )

    def clean(self):
        cleaned_data = super().clean()

        # Extracting the moon sign values
        first_quarter = cleaned_data.get("first_quarter")
        full_moon = cleaned_data.get("full_moon")
        last_quarter = cleaned_data.get("last_quarter")
        new_moon = cleaned_data.get("new_moon")

        # Counting the occurrences of each choice
        choices_count = {
            "positive": [first_quarter, full_moon, last_quarter, new_moon].count(
                "positive"
            ),
            "negative": [first_quarter, full_moon, last_quarter, new_moon].count(
                "negative"
            ),
            "ambiguous": [first_quarter, full_moon, last_quarter, new_moon].count(
                "ambiguous"
            ),
        }

        # Validating the conditions
        if (
            choices_count["positive"] != 1
            or choices_count["negative"] != 1
            or choices_count["ambiguous"] != 2
        ):
            raise ValidationError(
                "There must be one positive, one negative, and two ambiguous responses."
            )

        return cleaned_data


class PublicProfileCreationForm(forms.Form):
    quality_1 = forms.ChoiceField(choices=[])
    quality_2 = forms.ChoiceField(choices=[])
    quality_3 = forms.ChoiceField(choices=[])
    interest_1 = forms.ChoiceField(choices=[])
    interest_2 = forms.ChoiceField(choices=[])
    interest_3 = forms.ChoiceField(choices=[])
    activity_1 = forms.ChoiceField(choices=[])
    activity_2 = forms.ChoiceField(choices=[])

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
                (i.id, i.name) for i in character.interest_1_choices.all()
            ]
            self.fields["interest_2"].choices = [
                (i.id, i.name) for i in character.interest_2_choices.all()
            ]
            self.fields["interest_3"].choices = [
                (i.id, i.name) for i in character.interest_3_choices.all()
            ]
            self.fields["activity_1"].choices = [
                (a.id, a.name) for a in character.activity_1_choices.all()
            ]
            self.fields["activity_2"].choices = [
                (a.id, a.name) for a in character.activity_2_choices.all()
            ]
