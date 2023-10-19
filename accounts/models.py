from django.db import models
from django.contrib.auth.models import User

gender_choices_pref = (
    ('Males', 'Males'),
    ('Females', 'Females'),
    ('Non-binary Individuals', 'Non-binary Individuals')
)


class DatingPreference(models.Model):
    gender = models.CharField(max_length=25, choices=gender_choices_pref)
    
    @classmethod
    def create_defaults(cls):
        default_preferences = ['Males', 'Females', 'Non-binary Individuals']
        for preference in default_preferences:
            cls.objects.get_or_create(gender=preference)

    def __str__(self):
        return self.gender
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    open_to_dating = models.ManyToManyField(DatingPreference, blank=True)
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('N', 'Non-binary'),
    ]

    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default="Not Specified")
    pronoun_preference = models.CharField(
        max_length=20,
        choices=[
            ('not_specified', 'Not specified'),
            ('he_him', 'He/Him'),
            ('she_her', 'She/Her'),
            ('they_them', 'They/Them'),
            ('other', 'Other'),
        ],
        default='not_specified',
    )

    def __str__(self):
        return self.user.username