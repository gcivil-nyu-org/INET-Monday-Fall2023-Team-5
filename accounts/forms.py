from django import forms
from .models import Profile
from django.contrib.auth.models import User

from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail


# This is the form that will be used to create a new user, and check for valid email
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="NYU Email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email.endswith("@nyu.edu"):
            raise ValidationError("Please use your NYU email.")
        return email

    
# This is the form that will be used to edit a user's profile
class EditProfileForm(forms.ModelForm):
     pronoun_preference = forms.ChoiceField(
        choices=[
            ('he_him', 'He/Him'),
            ('she_her', 'She/Her'),
            ('they_them', 'They/Them'),
            ('other', 'Other'),
        ],
        widget=forms.RadioSelect,
        required=False
    )
     custom_pronoun = forms.CharField(
          max_length=255,
          required=False,
          widget=forms.TextInput(attrs={'placeholder': 'Custom Pronoun'}),
     )

     class Meta:
          model = Profile
          fields = ('open_to_dating','pronoun_preference')

