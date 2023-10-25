from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.forms import PasswordChangeForm
from .models import *

class ProfileModelTest(TestCase):
    
    def setUp(self):
        # Create a test user for associating with a profile
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_create_profile(self):
        # Given the post-save signal, there should already be one profile.
        # We will just verify that the profile was created correctly.
        profile = self.user.profile
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(profile.user, self.user)
        
    def test_string_representation(self):
        # Test the string representation of the profile.
        profile = self.user.profile
        self.assertEqual(str(profile), 'testuser')

    def test_default_values(self):
        # Test the default values for fields.
        profile = self.user.profile
        self.assertEqual(profile.gender, 'NS')
        self.assertEqual(profile.pronoun_preference, 'not_specified')

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


class DatingPreferenceModelTest(TestCase):
    
    def test_create_defaults(self):
        # Test the creation of default DatingPreference entries.

        DatingPreference.create_defaults()
        
        # Check if all default preferences are created
        self.assertEqual(DatingPreference.objects.count(), len(DatingPreference.gender_choices_pref))
        
        for gender_code, _ in DatingPreference.gender_choices_pref:
            self.assertTrue(DatingPreference.objects.filter(gender=gender_code).exists())

    def test_string_representation(self):
        # Test the string representation of the DatingPreference model.

        preference = DatingPreference.objects.create(gender='M')
        self.assertEqual(str(preference), 'Males')
        
        preference = DatingPreference.objects.create(gender='F')
        self.assertEqual(str(preference), 'Females')
        
        preference = DatingPreference.objects.create(gender='N')
        self.assertEqual(str(preference), 'Non-binary Individuals')
        
        preference = DatingPreference.objects.create(gender='NS')
        self.assertEqual(str(preference), 'Not Specified')

    def test_duplicate_create_defaults(self):
        # Test that create_defaults doesn't duplicate entries.

        DatingPreference.create_defaults()
        initial_count = DatingPreference.objects.count()
        
        # Call create_defaults again
        DatingPreference.create_defaults()
        
        # Check that the count hasn't changed
        self.assertEqual(DatingPreference.objects.count(), initial_count)

class AccountViewTest(TestCase):
    
    def setUp(self):
        # Create a test user for authentication and testing purposes
        self.client = Client()
        self.account_url = reverse('account')  # assuming 'account' is the name of the URL pattern for the account view
        self.user = User.objects.create_user(username='testuser', password='testpassword123')

    def test_redirect_if_not_logged_in(self):
        # Tests if an unauthenticated  user trying to access the account
        #  view is redirected to the login page
        response = self.client.get(self.account_url)
        self.assertRedirects(response, '/accounts/login/?next=/accounts/account/') # adjust the expected URL if your login URL is different

    def test_logged_in_uses_correct_template(self):
        # Test that if a user is logged in and accesses the account 
        # view, the correct template (account.html) is used
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(self.account_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account.html')

    def test_change_username_successfully(self):
        # Test checks if a logged-in user can successfully change 
        # their username
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.post(self.account_url, {'username': 'newusername'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Username updated successfully')

    def test_change_username_to_existing_one(self):
        # Test that a logged-in user cannot change their username 
        # to one that already exists in the database
        User.objects.create_user(username='existinguser', password='testpassword123')
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.post(self.account_url, {'username': 'existinguser'})
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'This username is already taken. Choose another.')

    def test_change_password_successfully(self):
        # Test checks if a logged-in user can successfully change 
        # their password.
        self.client.login(username='testuser', password='testpassword123')
        data = {
            'old_password': 'testpassword123',
            'new_password1': 'newtestpassword123',
            'new_password2': 'newtestpassword123',
        }
        response = self.client.post(self.account_url, data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newtestpassword123'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Password updated successfully')