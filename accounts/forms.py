from django import forms
from .models import*

class EditProfileForm(forms.ModelForm):
    GENDER_CHOICES = Profile.GENDER_CHOICES  # Use the choices from the Profile model

    pronoun_preference = forms.ChoiceField(
        choices=[
            ('he_him', 'He/Him'),
            ('she_her', 'She/Her'),
            ('they_them', 'They/Them'),
            ('other', 'Other'),
            ('not_specified', 'Not Specified'),  # Added this choice
        ],
        widget=forms.RadioSelect,
        required=False
    )

    open_to_dating = forms.ModelMultipleChoiceField(
        queryset=DatingPreference.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    custom_pronoun = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Custom Pronoun'}),
    )

    class Meta:
        model = Profile
        fields = ('gender', 'open_to_dating', 'pronoun_preference', 'custom_pronoun')  # Added 'custom_pronoun'
