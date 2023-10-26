from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.forms import PasswordChangeForm
from .models import *
import os
from django.core.files import File 

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

class ViewProfileTest(TestCase):

    def setUp(self):
        # Create a test user and log in
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

        # Create a test profile for the user or fetch it if it already exists
        self.profile, created = Profile.objects.get_or_create(user=self.user)

        # Always create or get dating preferences and associate them with the profile
        f_pref, _ = DatingPreference.objects.get_or_create(gender='F')
        m_pref, _ = DatingPreference.objects.get_or_create(gender='M')

    
        # Clear any existing preferences and then add the new ones
        self.profile.open_to_dating.clear()
        self.profile.open_to_dating.add(m_pref, f_pref)


    def tearDown(self):
        # Optional: Clean up after tests to ensure no leftover data
        # Though with TestCase, each test is transactional and rolled back
        self.profile.delete()
        self.user.delete()

    def test_view_profile_requires_login(self):
        # Log out and try accessing the view
        self.client.logout()
        response = self.client.get(reverse('view_profile'))
        print("Redirected URL:", response.url)  # Add this line to debug
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))


    def test_view_profile_displays_correct_context(self):
        response = self.client.get(reverse('view_profile'))

        # Check the user and profile in the context
        self.assertEqual(response.context['user'], self.user)
        self.assertEqual(response.context['profile'], self.profile)
        self.assertEqual(response.context['pronoun_preference'], self.profile.get_pronoun_preference_display())

        # Check the open_to_dating in the context
        # Updated to match the actual string representation
        self.assertQuerysetEqual(
            response.context['open_to_dating'].order_by('-gender'), 
            ['Males', 'Females'], 
            transform=str,
            ordered=True
        )



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

class EditProfileTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.edit_profile_url = reverse('edit_profile')
        self.profile = Profile.objects.get(user=self.user)

    def test_get_edit_profile_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_get_edit_profile_authenticated(self):
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile/edit_profile.html')

    def test_post_edit_profile_valid_data(self):
        data = {
            'gender': 'M',
            'pronoun_preference': 'he_him',
            'open_to_dating': [],  # Empty for this test. Fill with valid data if necessary.
        }
        response = self.client.post(self.edit_profile_url, data)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.gender, 'M')
        self.assertEqual(self.profile.pronoun_preference, 'he_him')

    def test_post_edit_profile_invalid_data(self):
        data = {
            'gender': 'INVALID',
        }
        response = self.client.post(self.edit_profile_url, data)
        self.assertContains(response, 'There was an error in the form. Please check your inputs.')

    def test_custom_pronoun(self):
        profile, created = Profile.objects.get_or_create(user=self.user, defaults={'gender': 'M'})
        if not created:
            profile.gender = "M"
            profile.save()

        data = {
            'gender': 'M',
            'pronoun_preference': 'other',
            'custom_pronoun': 'ze/zir',
        }

        response = self.client.post(self.edit_profile_url, data)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.pronoun_preference, 'ze/zir')

    def test_custom_pronoun_without_providing_one(self):
        profile, created = Profile.objects.get_or_create(user=self.user, defaults={'gender': 'M'})
        if not created:
            profile.gender = "M"
            profile.save()

        data = {
            'gender': 'M',
            'pronoun_preference': 'other',
        }
        # Ensure that the pronoun_preference is set to 'other' and custom_pronoun is not set
        self.assertEqual(data['pronoun_preference'], 'other')
        self.assertNotIn('custom_pronoun', data)

        response = self.client.post(self.edit_profile_url, data)

        self.assertContains(response, 'You must provide a custom pronoun when selecting &quot;Other&quot;.')



    def test_profile_picture_upload(self):
        with open('test_files/test_image.jpg', 'rb') as pic:
            data = {
                'profile_picture': pic,
                'gender': 'M',
                'pronoun_preference': 'he_him',
            }
            response = self.client.post(self.edit_profile_url, data)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.profile_picture.name.startswith('profile_pictures/'))

        # Cleanup the uploaded test image at the end
        self.profile.profile_picture.delete()

    def test_initial_data_matches_user_profile(self):
        self.profile.gender = 'M'
        self.profile.pronoun_preference = 'he_him'
        self.profile.save()
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.context['form'].initial['gender'], 'M')
        self.assertEqual(response.context['form'].initial['pronoun_preference'], 'he_him')

    def test_no_changes_to_profile(self):
        # Setup: Define the initial state
        self.profile.gender = 'M'
        self.profile.pronoun_preference = 'he_him'
        self.profile.save()

        # Action: Submit the form without any updates
        initial_data = {
            'gender': 'M',
            'pronoun_preference': 'he_him',
            'open_to_dating': [],  # Assuming this was empty initially
        }
        response = self.client.post(self.edit_profile_url, initial_data)

        # Refresh the profile from the database
        self.profile.refresh_from_db()

        # Assert: Check that the profile attributes remain unchanged
        self.assertEqual(self.profile.gender, 'M')
        self.assertEqual(self.profile.pronoun_preference, 'he_him')
    


    def test_profile_picture_removal(self):
        # Setup: Upload a profile picture to start with
        with open('test_files/test_image.jpg', 'rb') as pic:
            self.profile.profile_picture.save('test_image.jpg', File(pic))
            self.profile.save()

        # Ensure the profile picture was saved
        self.assertTrue(self.profile.profile_picture)

        # Action: Submit the form for profile picture removal
        data = {
            'profile_picture-clear': True,  # Set to True to clear the image
            'gender': 'M',  # include other necessary fields
            'pronoun_preference': 'he_him',
            'open_to_dating': [],
        }
        response = self.client.post(self.edit_profile_url, data)

        # Refresh the profile from the database
        self.profile.refresh_from_db()

        # Assert: Check that the profile picture has been removed
        self.assertFalse(self.profile.profile_picture) # Check if the profile picture is None

        # Cleanup: If the file still exists, remove it
        if self.profile.profile_picture and os.path.exists(self.profile.profile_picture.path):
            os.remove(self.profile.profile_picture.path)

    def test_updating_dating_preferences(self):
        # Setup: Create default dating preferences
        DatingPreference.create_defaults()

        # Fetch the dating preferences to use for testing
        male_pref = DatingPreference.objects.get(gender='M')
        nb_pref = DatingPreference.objects.get(gender='N')

        # Action: Update the profile with selected dating preferences
        data = {
            'gender': 'M',
            'pronoun_preference': 'he_him',
            'open_to_dating': [male_pref.id, nb_pref.id],  # Using the IDs of the DatingPreference objects
        }
        response = self.client.post(self.edit_profile_url, data)

        # Refresh the profile from the database
        self.profile.refresh_from_db()

        # Assertion: Check that the profile's dating preferences have been updated
        self.assertIn(male_pref, self.profile.open_to_dating.all())
        self.assertIn(nb_pref, self.profile.open_to_dating.all())

        # Optionally, you can also check the response to make sure there are no errors and perhaps it redirects to the right place
        self.assertEqual(response.status_code, 302)  # assuming you're redirecting after a successful post




    
    
    
