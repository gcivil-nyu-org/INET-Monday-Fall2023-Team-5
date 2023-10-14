from django.db import models

class Profile(models.Model):
    gender_choices_pref = (('Males', 'Males'),('Females', 'Females'), ('Non-binary Individuals', 'Non-binary Individuals'))
    open_to_dating = models.CharField(max_length = 25, choices = gender_choices_pref, blank = False)