from .models import Question
from django import forms


class QuestionSelectForm(forms.Form):
    question = forms.ModelChoiceField(
        queryset=Question.objects.none(),  # Set an empty initial queryset
        widget=forms.Select(attrs={"class": "select-question"}),
        label="Select a Question",
    )

    def __init__(self, *args, **kwargs):
        questions = kwargs.pop("questions", Question.objects.none())
        super(QuestionSelectForm, self).__init__(*args, **kwargs)
        self.fields["question"].queryset = questions


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
