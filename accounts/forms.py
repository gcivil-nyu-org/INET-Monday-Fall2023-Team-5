from django import forms
from .models import *
from django.contrib.auth.models import User

from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site


# This is the form that will be used to create a new user, and check for valid email
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="NYU Email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        self.domain = kwargs.pop('domain', None)  # Extract domain if passed, else default to None
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already in use.")
        if not email.endswith("@nyu.edu"):
            raise ValidationError("Please use your NYU email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False  # Set user to inactive until email confirmation
        if commit:
            user.save()

            # Generate a token for email confirmation
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            confirmation_link = f'http://{self.domain}/accounts/confirm/{uid}/{token}/'

            # Send an email
            send_mail(
                'Confirm your registration',
                f'Click the link to confirm: {confirmation_link}',
                'from@example.com',
                [user.email],
                fail_silently=False,
            )
        return user

    
# This is the form that will be used to edit a user's profile
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

    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
    )

    class Meta:
        model = Profile
        fields = ('gender', 'open_to_dating', 'pronoun_preference', 'custom_pronoun', 'profile_picture')

    def clean(self):
        cleaned_data = super().clean()
        pronoun_preference = cleaned_data.get('pronoun_preference')
        custom_pronoun = cleaned_data.get('custom_pronoun')
        

        if pronoun_preference == 'other' and (not custom_pronoun or custom_pronoun.strip() == ''):
            self.add_error('custom_pronoun', 'You must provide a custom pronoun when selecting "Other".')

        return cleaned_data