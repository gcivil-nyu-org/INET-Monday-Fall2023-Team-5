from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.forms import PasswordChangeForm
from .models import *
import tempfile
from django.core.files import File 
from .forms import EditProfileForm
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO

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

class ViewProfileViewTest(TestCase):

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
        # Clean up after tests to ensure no leftover data
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


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())  # Create a temporary media directory for testing
class EditProfileViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.edit_profile_url = reverse('edit_profile')  # Assuming the URL name for the view is 'edit_profile'

    def test_logged_out_user_redirected_to_login(self):
        response = self.client.get(self.edit_profile_url)
        expected_redirect_url = f'/accounts/login/?next={self.edit_profile_url}'
        self.assertRedirects(response, expected_redirect_url)


    def test_logged_in_user_accesses_view(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile/edit_profile.html')
    

    def test_get_request_logged_in_user(self):
        # Log the user in
        self.client.login(username='testuser', password='testpassword')
        
        # Send a GET request
        response = self.client.get(self.edit_profile_url)
        
        # Check the response's status code and used template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile/edit_profile.html')

        # Check the context data
        form_in_context = response.context['form']
        self.assertIsInstance(form_in_context, EditProfileForm)
        
        # Ensure the form instance is related to the authenticated user's profile
        self.assertEqual(form_in_context.instance, self.user.profile)

    def test_valid_post_request_updates_profile(self):
        # Log the user in
        self.client.login(username='testuser', password='testpassword')
        
        # Prepare valid POST data
        post_data = {
            'gender': 'M',  # Male
            'pronoun_preference': 'he_him',
            # Add other required fields if needed
        }
        
        # Send a POST request
        response = self.client.post(self.edit_profile_url, post_data)
        
        # Check the response for redirection
        profile_updated_url = reverse('profile_updated')  # Assuming the URL name for the success view is 'profile_updated'
        self.assertRedirects(response, profile_updated_url)
        
        # Check the updated profile data
        self.user.refresh_from_db()  # Refresh the user instance to get updated related data
        self.assertEqual(self.user.profile.gender, 'M')  # Check gender was updated
        self.assertEqual(self.user.profile.pronoun_preference, 'he_him')  # Check pronoun preference was updated
        
        # Add other assertions as needed to ensure all provided data was saved correctly

    def create_mock_image(self, filename="test_image_1.jpg", format="JPEG"):
        """Generate a mock image for testing."""
        image = Image.new('RGB', (100, 100))
        buffered = BytesIO()
        image.save(buffered, format=format)
        return SimpleUploadedFile(name=filename, content=buffered.getvalue(), content_type=f"image/{format.lower()}")

    def test_upload_profile_picture(self):
        # Log the user in
        self.client.login(username='testuser', password='testpassword')
        
        # Create a mock image for upload
        uploaded_image = self.create_mock_image()
        
        # Send a POST request with the mock image
        post_data = {
            'gender': 'M',
            'profile_picture': uploaded_image,
            # Add other required fields if needed
        }
        response = self.client.post(self.edit_profile_url, post_data)

        
        # Check that the profile picture is saved
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.profile_picture)  # This ensures the ImageField has some value
        self.assertIn("test_image_1.jpg", self.user.profile.profile_picture.name) 

    def test_clear_profile_picture(self):
        # Ensure the profile has a picture first
        uploaded_image = self.create_mock_image()
        self.user.profile.profile_picture.save("test_image_2.jpg", uploaded_image)
        self.user.profile.save()
        
        # Log the user in
        self.client.login(username='testuser', password='testpassword')
        
        # Send a POST request to clear the profile picture
        post_data = {
            'gender': 'M',
            'profile_picture-clear': 'on',  # Django expects the value 'on' for a checked checkbox
            # Add other required fields if needed
        }
        response = self.client.post(self.edit_profile_url, post_data)
        
        # Check that the profile picture has been cleared
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.profile_picture.name)  # We expect the ImageField name attribute to be falsy if cleared
    
    
    def test_custom_pronoun_validation(self):
        # Log the user in
        self.client.login(username='testuser', password='testpassword')

        # Prepare POST data with "other" pronoun preference and a custom pronoun
        post_data = {
            'gender': 'M',  # Assuming 'M' for Male
            'pronoun_preference': 'other',
            'custom_pronoun': 'ze/zir',
            # Add other required fields if needed
        }

        # Send a POST request
        response = self.client.post(self.edit_profile_url, post_data)

        # Check that the response is a redirect (if that's the expected behavior)
        self.assertEqual(response.status_code, 302)  # 302 is a common status code for redirects

        # Refresh the user's profile data from the database
        self.user.profile.refresh_from_db()

        # Check that the custom pronoun was saved correctly
        self.assertEqual(self.user.profile.pronoun_preference, 'ze/zir')

    def test_custom_pronoun_without_providing_one(self):
        # Log the user in
        self.client.login(username='testuser', password='testpassword')

        # Prepare data with 'pronoun_preference' set to 'other' and no 'custom_pronoun'
        post_data = {
            'gender': 'M',
            'pronoun_preference': 'other',
        }

        # Send a POST request
        response = self.client.post(self.edit_profile_url, post_data)

        # Check that the response contains part of the error message
        self.assertContains(response, 'You must provide a custom pronoun when selecting "Other".', html=True)


        # Check that the response status code is 200 (indicating a form submission with validation errors)
        self.assertEqual(response.status_code, 200)

        # Check that the form instance in the response context is invalid
        form = response.context['form']
        self.assertFalse(form.is_valid())

        # Check that the 'custom_pronoun' field in the form has errors
        self.assertTrue('custom_pronoun' in form.errors)

    
    def test_select_multiple_dating_preferences(self):
        # Create a list of valid preference values
        preference_values = ['M', 'F']
        
        # Create a list of preference IDs to be used in the form
        preference_ids = [str(DatingPreference.objects.get(gender=value).id) for value in preference_values]
        
        # Login as the user
        self.client.login(username='testuser', password='testpassword')
        
        # Simulate a POST request to the Edit Profile view with selected preferences
        response = self.client.post('/accounts/edit_profile/', {
            'gender': 'M',
            'open_to_dating': preference_ids,  # List of preference IDs
            'pronoun_preference': 'he_him',
            'custom_pronoun': 'His pronoun',
        })
        
        # Check if the response is a successful redirect
        self.assertEqual(response.status_code, 302)
        
        # Get the user's profile and fetch the selected dating preferences
        user_profile = Profile.objects.get(user=self.user)
        selected_preferences = [preference.gender for preference in user_profile.open_to_dating.all()]
        
        # Assert that the selected preferences match the expected values
        self.assertEqual(selected_preferences, preference_values)

class DatingPreferenceModelTest(TestCase):

    def test_create_defaults(self):
        # Call the create_defaults method
        DatingPreference.create_defaults()

        # Verify that the default objects have been created
        male_preference = DatingPreference.objects.get(gender='M')
        female_preference = DatingPreference.objects.get(gender='F')
        nb_preference = DatingPreference.objects.get(gender='N')
        ns_preference = DatingPreference.objects.get(gender='NS')

        # Assert that the objects exist
        self.assertIsNotNone(male_preference)
        self.assertIsNotNone(female_preference)
        self.assertIsNotNone(nb_preference)
        self.assertIsNotNone(ns_preference)