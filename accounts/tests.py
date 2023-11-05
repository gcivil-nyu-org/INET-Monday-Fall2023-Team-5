from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages

# from django.contrib.sessions.middleware import SessionMiddleware
# from django.contrib.auth.forms import PasswordChangeForm
from .models import DatingPreference, Profile, Like  # , Match
import tempfile

# from django.core.files import File
from .forms import EditProfileForm
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO
from django.utils.http import urlsafe_base64_encode

# from django.utils.encoding import force_str
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from accounts.views import get_recommended_profiles
from accounts.admin import ProfileAdmin
from django.contrib.admin.sites import AdminSite

# from importlib import import_module
# from django.apps import apps


class ProfileModelTest(TestCase):
    def setUp(self):
        # Create a test user for associating with a profile
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_create_profile(self):
        # Given the post-save signal, there should already be one profile.
        # We will just verify that the profile was created correctly.
        profile = self.user.profile
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(profile.user, self.user)

    def test_string_representation(self):
        # Test the string representation of the profile.
        profile = self.user.profile
        self.assertEqual(str(profile), "testuser")

    def test_default_values(self):
        # Test the default values for fields.
        profile = self.user.profile
        self.assertEqual(profile.gender, "NS")
        self.assertEqual(profile.pronoun_preference, "not_specified")

    def test_profile_picture_field(self):
        # Retrieve the existing profile associated with the user.
        profile = self.user.profile

        # Check that the profile_picture field can be left blank.
        self.assertFalse(profile.profile_picture.name)

    def test_automatic_profile_creation_with_user(self):
        # Given that only one user has been created in the setUp,
        # there should already be one profile associated with that user.
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(self.user.profile.user, self.user)

    def test_profile_deletion_with_user(self):
        self.user.delete()
        self.assertEqual(Profile.objects.count(), 0)


class ViewProfileViewTest(TestCase):
    def setUp(self):
        # Create a test user and log in
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

        # Create a test profile for the user or fetch it if it already exists
        self.profile, created = Profile.objects.get_or_create(user=self.user)

        # Always create or get dating preferences and associate them with the profile
        f_pref, _ = DatingPreference.objects.get_or_create(gender="F")
        m_pref, _ = DatingPreference.objects.get_or_create(gender="M")

        # Clear any existing preferences and then add the new ones
        self.profile.open_to_dating.clear()
        self.profile.open_to_dating.add(m_pref, f_pref)

    def tearDown(self):
        # Clean up after tests to ensure no leftover data
        # Though with TestCase, each test is transactional and rolled back
        self.profile.delete()
        self.user.delete()

    def test_view_profile_requires_login(self):
        # Log out and try accessing the view
        self.client.logout()
        response = self.client.get(reverse("view_profile"))
        print("Redirected URL:", response.url)  # Add this line to debug
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_view_profile_displays_correct_context(self):
        response = self.client.get(reverse("view_profile"))

        # Check the user and profile in the context
        self.assertEqual(response.context["user"], self.user)
        self.assertEqual(response.context["profile"], self.profile)
        self.assertEqual(
            response.context["pronoun_preference"],
            self.profile.get_pronoun_preference_display(),
        )

        # Check the open_to_dating in the context
        # Updated to match the actual string representation
        self.assertQuerysetEqual(
            response.context["open_to_dating"].order_by("-gender"),
            ["Males", "Females"],
            transform=str,
            ordered=True,
        )


class AccountViewTest(TestCase):
    def setUp(self):
        # Create a test user for authentication and testing purposes
        self.client = Client()
        self.account_url = reverse(
            "account"
        )  # assuming 'account' is the name of the URL pattern for the account view
        self.user = User.objects.create_user(
            username="testuser", password="testpassword123"
        )

    def test_redirect_if_not_logged_in(self):
        # Tests if an unauthenticated  user trying to access the account
        #  view is redirected to the login page
        response = self.client.get(self.account_url)
        self.assertRedirects(
            response, "/accounts/login/?next=/accounts/account/"
        )  # adjust the expected URL if your login URL is different

    def test_logged_in_uses_correct_template(self):
        # Test that if a user is logged in and accesses the account
        # view, the correct template (account.html) is used
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.account_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/account.html")

    def test_change_username_successfully(self):
        # Test checks if a logged-in user can successfully change
        # their username
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.post(self.account_url, {"username": "newusername"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "newusername")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Username updated successfully")

    def test_change_username_to_existing_one(self):
        # Test that a logged-in user cannot change their username
        # to one that already exists in the database
        User.objects.create_user(username="existinguser", password="testpassword123")
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.post(self.account_url, {"username": "existinguser"})
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "This username is already taken. Choose another."
        )

    def test_change_password_successfully(self):
        # Test checks if a logged-in user can successfully change
        # their password.
        self.client.login(username="testuser", password="testpassword123")
        data = {
            "old_password": "testpassword123",
            "new_password1": "newtestpassword123",
            "new_password2": "newtestpassword123",
        }
        response = self.client.post(self.account_url, data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newtestpassword123"))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Password updated successfully")

    def test_change_password_with_invalid_data(self):
        # Test checks if the error message is shown when a user tries to change
        # their password with invalid data (e.g. mismatched new passwords)
        self.client.login(username="testuser", password="testpassword123")
        data = {
            "old_password": "testpassword123",
            "new_password1": "newtestpassword123",
            "new_password2": "differentnewtestpassword123",  # Mismatched password
        }
        response = self.client.post(self.account_url, data)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Please correct the errors below.")


@override_settings(
    MEDIA_ROOT=tempfile.mkdtemp()
)  # Create a temporary media directory for testing
class EditProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.edit_profile_url = reverse(
            "edit_profile"
        )  # Assuming the URL name for the view is 'edit_profile'

    def test_logged_out_user_redirected_to_login(self):
        response = self.client.get(self.edit_profile_url)
        expected_redirect_url = f"/accounts/login/?next={self.edit_profile_url}"
        self.assertRedirects(response, expected_redirect_url)

    def test_logged_in_user_accesses_view(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile/edit_profile.html")

    def test_get_request_logged_in_user(self):
        # Log the user in
        self.client.login(username="testuser", password="testpassword")

        # Send a GET request
        response = self.client.get(self.edit_profile_url)

        # Check the response's status code and used template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile/edit_profile.html")

        # Check the context data
        form_in_context = response.context["form"]
        self.assertIsInstance(form_in_context, EditProfileForm)

        # Ensure the form instance is related to the authenticated user's profile
        self.assertEqual(form_in_context.instance, self.user.profile)

    def test_valid_post_request_updates_profile(self):
        # Log the user in
        self.client.login(username="testuser", password="testpassword")

        # Prepare valid POST data
        post_data = {
            "gender": "M",  # Male
            "pronoun_preference": "he_him",
            # Add other required fields if needed
        }

        # Send a POST request
        response = self.client.post(self.edit_profile_url, post_data)

        # Check the response for redirection
        profile_updated_url = reverse(
            "profile_updated"
        )  # Assuming the URL name for the success view is 'profile_updated'
        self.assertRedirects(response, profile_updated_url)

        # Check the updated profile data
        self.user.refresh_from_db()  # Refresh user instance to get updated data
        self.assertEqual(self.user.profile.gender, "M")  # Check gender was updated
        self.assertEqual(
            self.user.profile.pronoun_preference, "he_him"
        )  # Check pronoun preference was updated

        # Add other assertions as needed to ensure all provided data was saved correctly

    def create_mock_image(self, filename="test_image_1.jpg", format="JPEG"):
        """Generate a mock image for testing."""
        image = Image.new("RGB", (100, 100))
        buffered = BytesIO()
        image.save(buffered, format=format)
        return SimpleUploadedFile(
            name=filename,
            content=buffered.getvalue(),
            content_type=f"image/{format.lower()}",
        )

    def test_upload_profile_picture(self):
        # Log the user in
        self.client.login(username="testuser", password="testpassword")

        # Create a mock image for upload
        uploaded_image = self.create_mock_image()

        # Send a POST request with the mock image
        post_data = {
            "gender": "M",
            "profile_picture": uploaded_image,
            # Add other required fields if needed
        }
        response = self.client.post(self.edit_profile_url, post_data)  # noqa: F841

        # Check that the profile picture is saved
        self.user.profile.refresh_from_db()
        self.assertTrue(
            self.user.profile.profile_picture
        )  # This ensures the ImageField has some value
        self.assertIn("test_image_1.jpg", self.user.profile.profile_picture.name)

    def test_clear_profile_picture(self):
        # Ensure the profile has a picture first
        uploaded_image = self.create_mock_image()
        self.user.profile.profile_picture.save("test_image_2.jpg", uploaded_image)
        self.user.profile.save()

        # Log the user in
        self.client.login(username="testuser", password="testpassword")

        # Send a POST request to clear the profile picture
        post_data = {
            "gender": "M",
            "profile_picture-clear": "on",  # 'on' is for a checked checkbox
            # Add other required fields if needed
        }
        response = self.client.post(self.edit_profile_url, post_data)  # noqa: F841

        # Check that the profile picture has been cleared
        self.user.profile.refresh_from_db()
        self.assertFalse(
            self.user.profile.profile_picture.name
        )  # We expect the ImageField name attribute to be falsy if cleared

    def test_custom_pronoun_validation(self):
        # Log the user in
        self.client.login(username="testuser", password="testpassword")

        # Prepare POST data with "other" pronoun preference and a custom pronoun
        post_data = {
            "gender": "M",  # Assuming 'M' for Male
            "pronoun_preference": "other",
            "custom_pronoun": "ze/zir",
            # Add other required fields if needed
        }

        # Send a POST request
        response = self.client.post(self.edit_profile_url, post_data)

        # Check that the response is a redirect (if that's the expected behavior)
        self.assertEqual(
            response.status_code, 302
        )  # 302 is a common status code for redirects

        # Refresh the user's profile data from the database
        self.user.profile.refresh_from_db()

        # Check that the custom pronoun was saved correctly
        self.assertEqual(self.user.profile.pronoun_preference, "ze/zir")

    def test_custom_pronoun_without_providing_one(self):
        # Log the user in
        self.client.login(username="testuser", password="testpassword")

        # Prepare data with 'pronoun_preference' set to 'other' and no 'custom_pronoun'
        post_data = {
            "gender": "M",
            "pronoun_preference": "other",
        }

        # Send a POST request
        response = self.client.post(self.edit_profile_url, post_data)

        # Check that the response contains part of the error message
        self.assertContains(
            response,
            'You must provide a custom pronoun when selecting "Other".',
            html=True,
        )

        # Check that the response status code is 200 (indicating a form submission
        # with validation errors)
        self.assertEqual(response.status_code, 200)

        # Check that the form instance in the response context is invalid
        form = response.context["form"]
        self.assertFalse(form.is_valid())

        # Check that the 'custom_pronoun' field in the form has errors
        self.assertTrue("custom_pronoun" in form.errors)

    def test_select_multiple_dating_preferences(self):
        # Create a list of valid preference values
        preference_values = ["M", "F"]

        # Create a list of preference IDs to be used in the form
        preference_ids = [
            str(DatingPreference.objects.get(gender=value).id)
            for value in preference_values
        ]

        # Login as the user
        self.client.login(username="testuser", password="testpassword")

        # Simulate a POST request to the Edit Profile view with selected preferences
        response = self.client.post(
            "/accounts/edit_profile/",
            {
                "gender": "M",
                "open_to_dating": preference_ids,  # List of preference IDs
                "pronoun_preference": "he_him",
                "custom_pronoun": "His pronoun",
            },
        )

        # Check if the response is a successful redirect
        self.assertEqual(response.status_code, 302)

        # Get the user's profile and fetch the selected dating preferences
        user_profile = Profile.objects.get(user=self.user)
        selected_preferences = [
            preference.gender for preference in user_profile.open_to_dating.all()
        ]

        # Assert that the selected preferences match the expected values
        self.assertEqual(selected_preferences, preference_values)


class DatingPreferenceModelTest(TestCase):
    def test_create_defaults(self):
        # Call the create_defaults method
        DatingPreference.create_defaults()

        # Verify that the default objects have been created
        male_preference = DatingPreference.objects.get(gender="M")
        female_preference = DatingPreference.objects.get(gender="F")
        nb_preference = DatingPreference.objects.get(gender="N")
        ns_preference = DatingPreference.objects.get(gender="NS")

        # Assert that the objects exist
        self.assertIsNotNone(male_preference)
        self.assertIsNotNone(female_preference)
        self.assertIsNotNone(nb_preference)
        self.assertIsNotNone(ns_preference)


class SignUpViewTest(TestCase):
    def setUp(self):
        self.signup_url = reverse(
            "signup"
        )  # assuming 'signup' is the URL name for the SignUpView
        self.user_data = {
            "username": "newuser",
            "password1": "testpassword123",
            "password2": "testpassword123",
            "email": "newuser@example.com",
        }

    def test_signup_view_uses_correct_template(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/registration/signup.html")

    def test_signup_success(self):
        signup_data = {
            "username": "testuser",
            "email": "testuser@nyu.edu",
            "password1": "securepassword123",
            "password2": "securepassword123",
        }
        response = self.client.post(reverse("signup"), signup_data)
        print(
            response.content
        )  # This will output the response content to see if there's any error message
        self.assertRedirects(response, reverse("confirmation_required"))

    def test_signup_email_already_in_use(self):
        # First, create a user with the desired email
        User.objects.create_user(
            username="existinguser",
            email="testuser@nyu.edu",
            password="testpassword123",
        )

        signup_data = {
            "username": "newuser",
            "email": "testuser@nyu.edu",  # This email already exists now
            "password1": "securepassword123",
            "password2": "securepassword123",
        }
        response = self.client.post(reverse("signup"), signup_data)

        # Check if the response contains the expected error message
        self.assertContains(response, "Email already in use.")

    def test_signup_non_nyu_email(self):
        signup_data = {
            "username": "newuser",
            "email": "testuser@gmail.com",  # This is a non-NYU email
            "password1": "securepassword123",
            "password2": "securepassword123",
        }
        response = self.client.post(reverse("signup"), signup_data)

        # Check if the response contains the expected error message
        self.assertContains(response, "Please use your NYU email.")


"""
class ViewSingleProfileTest(TestCase):
    def setUp(self):
        # Create a test user and an associated profile
        self.user = User.objects.create_user(
            username="testuser", password="testpassword123"
        )
        self.profile = self.user.profile
        self.single_profile_url = reverse("view_single_profile", args=[self.profile.pk])

    def test_view_single_profile(self):
        # Authenticate the test client
        self.client.login(username="testuser", password="testpassword123")

        response = self.client.get(self.single_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile/single_profile.html")
        self.assertEqual(response.context["profile"], self.profile)
"""


class ActivateAccountTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword123", is_active=False
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)
        self.activation_url = reverse("activate_account", args=[self.uid, self.token])

    def test_activate_account(self):
        response = self.client.get(self.activation_url)
        self.user.refresh_from_db()  # Refresh the user instance to get updated data

        # Ensure the user is now active
        self.assertTrue(self.user.is_active)
        self.assertRedirects(response, reverse("login"))

    def test_activate_account_invalid_uid(self):
        invalid_uid = urlsafe_base64_encode(
            force_bytes(999999)
        )  # Assuming no user has this ID
        activation_url = reverse("activate_account", args=[invalid_uid, self.token])
        response = self.client.get(activation_url)

        # Expecting a redirect to 'home'
        self.assertRedirects(response, reverse("home"))

        # Check if the expected error message is in messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertIn(
            "Activation link is invalid!", [msg.message for msg in messages_list]
        )

    def test_activate_account_invalid_token(self):
        invalid_token = "invalid_token"
        activation_url = reverse("activate_account", args=[self.uid, invalid_token])
        response = self.client.get(activation_url)

        # Expecting a redirect to 'home'
        self.assertRedirects(response, reverse("home"))

        # Check if the expected error message is in messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertIn(
            "Activation link is invalid!", [msg.message for msg in messages_list]
        )


class BrowseProfilesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create DatingPreferences
        DatingPreference.objects.all().delete()
        DatingPreference.create_defaults()

    def setUp(self):
        # Create multiple users and profiles to simulate a user pool
        User.objects.all().delete()
        Profile.objects.all().delete()
        self.users = [
            User.objects.create(username=f"user{i}", password="testpass")
            for i in range(10)
        ]

        # Create profiles with varying genders, pronouns, and dating preferences
        for index, user in enumerate(self.users):
            if hasattr(user, "profile"):
                profile = user.profile

            else:
                profile = Profile.objects.create(
                    user=user,
                    gender=Profile.GENDER_CHOICES[index % len(Profile.GENDER_CHOICES)][
                        0
                    ],
                    # Cycles through gender choices
                    pronoun_preference=Profile._meta.get_field(
                        "pronoun_preference"
                    ).choices[
                        index
                        % len(Profile._meta.get_field("pronoun_preference").choices)
                    ][
                        0
                    ],
                    # Cycles through pronoun choices
                )
            # Add varying dating preferences to each profile
            dating_pref = DatingPreference.objects.get(
                gender=Profile.GENDER_CHOICES[
                    (index + 1) % len(Profile.GENDER_CHOICES)
                ][0]
            )
            profile.open_to_dating.add(dating_pref)

    def test_browse_profiles(self):
        # Simulate a user logged in and browsing other user profiles
        logged_in_user = self.users[0]
        self.client.force_login(logged_in_user)

        response = self.client.get(reverse("browse_profiles"))

        # Assuming your view places the profiles in the context with the name "profiles"
        context_profiles = response.context["profiles"]

        # Fetch the logged-in user's profile and his dating preferences
        current_profile = logged_in_user.profile
        desired_gender_codes = [
            dp.gender for dp in current_profile.open_to_dating.all()
        ]

        # Check if the fetched profiles from the view match the logged-in user's
        # preferences
        for profile in context_profiles:
            self.assertIn(profile.gender, desired_gender_codes)
            self.assertNotEqual(profile.user, logged_in_user)

        # If you render profiles directly within a template, you might want to check
        # if each profile is present in the rendered HTML too.
        for profile in context_profiles:
            self.assertContains(
                response, profile.user.username
            )  # or any other unique string related to the profile


class GetRecommendedProfilesTest(TestCase):
    def setUp(self):
        # Clear all profiles and users before starting
        Profile.objects.all().delete()
        User.objects.all().delete()

        # Create dating preferences
        DatingPreference.create_defaults()

        # Create test users and profiles
        self.users = [
            User.objects.create_user(username=f"user{i}", password="123456")
            for i in range(4)
        ]

        # Assuming every user gets a profile automatically, we fetch the profile
        # and update it.

        # Profile 0: Male open to dating Females
        profile0 = self.users[0].profile
        profile0.gender = "M"
        profile0.open_to_dating.add(DatingPreference.objects.get(gender="F"))
        profile0.save()

        # Profile 1: Female open to dating Males
        profile1 = self.users[1].profile
        profile1.gender = "F"
        profile1.open_to_dating.add(DatingPreference.objects.get(gender="M"))
        profile1.save()

        # Profile 2: Female open to dating Non-binary
        profile2 = self.users[2].profile
        profile2.gender = "F"
        profile2.open_to_dating.add(DatingPreference.objects.get(gender="N"))
        profile2.save()

        # Profile 3: Non-binary open to dating Males and Females
        profile3 = self.users[3].profile
        profile3.gender = "N"
        profile3.open_to_dating.add(DatingPreference.objects.get(gender="M"))
        profile3.open_to_dating.add(DatingPreference.objects.get(gender="F"))
        profile3.save()

    def test_recommendation_logic(self):
        # Test for User 0 (Male open to dating Females)
        # Expected match: Profile 1 (Female open to dating Males)
        recommended_profiles = get_recommended_profiles(self.users[0])
        self.assertIn(self.users[1].profile, recommended_profiles)
        self.assertNotIn(
            self.users[2].profile, recommended_profiles
        )  # Different preferences
        self.assertNotIn(
            self.users[3].profile, recommended_profiles
        )  # Different preferences

        # Test for User 1 (Female open to dating Males)
        # Expected match: Profile 0 (Male open to dating Females)
        recommended_profiles = get_recommended_profiles(self.users[1])
        self.assertIn(self.users[0].profile, recommended_profiles)
        self.assertNotIn(
            self.users[2].profile, recommended_profiles
        )  # Same gender but different preferences
        self.assertNotIn(
            self.users[3].profile, recommended_profiles
        )  # Different preferences

        # Test for User 2 (Female open to dating Non-binary)
        # Expected match: Profile 3 based on current profiles
        recommended_profiles = get_recommended_profiles(self.users[2])
        self.assertIn(self.users[3].profile, recommended_profiles)
        self.assertNotIn(self.users[0].profile, recommended_profiles)
        self.assertNotIn(self.users[1].profile, recommended_profiles)

        # Test for User 3 (Non-binary open to dating Males and Females)
        # Expected match: Profile 2
        recommended_profiles = get_recommended_profiles(self.users[3])
        self.assertIn(self.users[2].profile, recommended_profiles)
        self.assertNotIn(self.users[0].profile, recommended_profiles)
        self.assertNotIn(self.users[1].profile, recommended_profiles)

    def test_excluding_own_profile(self):
        # For each user, ensure they don't get their own profile as a recommendation
        for user in self.users:
            recommendations = get_recommended_profiles(user)
            self.assertFalse(user.profile in recommendations)


class DisplayOpenToDatingTest(TestCase):
    def setUp(self):
        # Clean slate
        User.objects.all().delete()
        Profile.objects.all().delete()
        DatingPreference.objects.all().delete()

        # Create DatingPreferences
        DatingPreference.create_defaults()
        male_pref = DatingPreference.objects.get(gender="M")
        female_pref = DatingPreference.objects.get(gender="F")

        # Create a test user and a profile for them
        self.user = User.objects.create(username="testuser", password="testpass")
        self.profile, created = Profile.objects.get_or_create(user=self.user)

        # Add multiple dating preferences for the test user
        self.profile.open_to_dating.add(male_pref, female_pref)

        # Create an instance of the ProfileAdmin to test the method
        self.profile_admin = ProfileAdmin(model=Profile, admin_site=AdminSite())

    def test_display_open_to_dating(self):
        # Call the display_open_to_dating method with the profile
        display_result = self.profile_admin.display_open_to_dating(self.profile)

        # Test that the display shows both male and female preferences
        self.assertIn("M", display_result)
        self.assertIn("F", display_result)

        # Test that the results are comma-separated
        self.assertEqual(display_result, "M, F")


class TestProfileGenderMapping(TestCase):
    def setUp(self):
        # Create sample profiles
        self.user1 = User.objects.create_user(username="user1", password="password")
        self.user2 = User.objects.create_user(username="user2", password="password")
        self.user3 = User.objects.create_user(username="user3", password="password")

        # Assuming profiles are auto-created for these users:
        self.profile1 = self.user1.profile
        self.profile2 = self.user2.profile
        self.profile3 = self.user3.profile

        # Set initial gender values
        self.profile1.gender = "O1"
        self.profile1.save()

        self.profile2.gender = "O2"
        self.profile2.save()

        self.profile3.gender = "NS"
        self.profile3.save()

        self.profile_gender_mapping = {
            "O1": "N1",
            "O2": "N2",
        }

    def test_gender_mapping(self):
        # Run the code being tested
        for profile in Profile.objects.all():
            profile.gender = self.profile_gender_mapping.get(
                profile.gender, profile.gender
            )
            profile.save()

        # Refresh the profiles from the database
        self.profile1.refresh_from_db()
        self.profile2.refresh_from_db()
        self.profile3.refresh_from_db()

        # Verify that the genders are updated (or unchanged) correctly
        self.assertEqual(self.profile1.gender, "N1")
        self.assertEqual(self.profile2.gender, "N2")
        self.assertEqual(self.profile3.gender, "NS")


class TestViews(TestCase):
    def test_home_view(self):
        # Get the response for the home view
        response = self.client.get(reverse("home"))
        # Check that the response has a status code of 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Check that the correct template was used
        self.assertTemplateUsed(response, "home.html")

    def test_about_view(self):
        # Get the response for the about view
        response = self.client.get(reverse("about"))

        # Check that the response has a status code of 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Check that the correct template was used
        self.assertTemplateUsed(response, "accounts/about.html")

        # Check that the context data contains the title
        self.assertEqual(response.context["title"], "About")

class LikeModelTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.like1 = Like.objects.create(from_user=self.user1, to_user=self.user2)

    def test_is_mutual_false(self):
        self.assertFalse(self.like1.is_mutual())

    def test_is_mutual_true(self):
        Like.objects.create(from_user=self.user2, to_user=self.user1)
        self.assertTrue(self.like1.is_mutual())