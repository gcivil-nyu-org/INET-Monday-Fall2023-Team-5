from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q


class DatingPreference(models.Model):
    # Define gender_choices_pref at class-level
    gender_choices_pref = [
        ("M", "Males"),
        ("F", "Females"),
        ("N", "Non-binary Individuals"),
        ("NS", "Not Specified"),
    ]

    gender = models.CharField(max_length=2, choices=gender_choices_pref)

    @classmethod
    def create_defaults(cls):
        # Instead of hardcoded values, we reference gender_choices_pref
        for gender_code, gender_label in cls.gender_choices_pref:
            cls.objects.get_or_create(
                gender=gender_code
            )  # Changed from gender_label to gender_code

    def __str__(self):
        return (
            self.get_gender_display()
        )  # Using get_gender_display for better representation


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    open_to_dating = models.ManyToManyField(DatingPreference, blank=True)
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("N", "Non-binary"),
        ("NS", "Not Specified"),  # added this for completeness
    ]
    gender = models.CharField(max_length=2, choices=GENDER_CHOICES, default="NS")
    pronoun_preference = models.CharField(
        max_length=20,
        choices=[
            ("not_specified", "Not specified"),
            ("he_him", "He/Him"),
            ("she_her", "She/Her"),
            ("they_them", "They/Them"),
            ("other", "Other"),
        ],
        default="not_specified",
    )
    custom_pronoun = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )

    likes_remaining = models.PositiveIntegerField(default=3)

    def __str__(self):
        return self.user.username


class Like(models.Model):
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="likes_given"
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="likes_received"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def is_mutual(self):
        """Check if there is a mutual like between two users."""
        return Like.objects.filter(
            from_user=self.to_user, to_user=self.from_user
        ).exists()


class Match(models.Model):
    user1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="matches_user1"
    )
    user2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="matches_user2"
    )
    matched_at = models.DateTimeField(auto_now_add=True)
    notification_sent = models.BooleanField(
        default=False
    )  # New field to track notification status

    @classmethod
    def create_match(cls, user1, user2):
        # Check if there's already a match between the two users
        existing_match = cls.objects.filter(
            (Q(user1=user1) & Q(user2=user2)) | (Q(user1=user2) & Q(user2=user1))
        ).exists()
        if not existing_match:
            # Create a new match if not already matched
            match = cls(user1=user1, user2=user2)
            match.save()
            return match
        return None
