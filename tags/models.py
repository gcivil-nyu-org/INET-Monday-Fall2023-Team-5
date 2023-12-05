from django.db import models


class Tag(models.Model):
    word = models.CharField(max_length=100)
    # any other fields you might need

    def __str__(self):
        return self.word
