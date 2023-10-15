from django.db import models
# from django.contrib.auth.models import User

class Profile(models.Model):
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender_choices_pref = (('Males', 'Males'),('Females', 'Females'), ('Non-binary Individuals', 'Non-binary Individuals'))
    open_to_dating = models.CharField(max_length = 25, choices = gender_choices_pref, blank = False)

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