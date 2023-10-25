from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.forms import PasswordChangeForm

class AccountViewTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.account_url = reverse('account')  # assuming 'account' is the name of the URL pattern for the account view
        self.user = User.objects.create_user(username='testuser', password='testpassword123')

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.account_url)
        self.assertRedirects(response, '/accounts/login/?next=/accounts/account/') # adjust the expected URL if your login URL is different

    def test_logged_in_uses_correct_template(self):
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(self.account_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account.html')

    def test_change_username_successfully(self):
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.post(self.account_url, {'username': 'newusername'})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Username updated successfully')

    def test_change_username_to_existing_one(self):
        User.objects.create_user(username='existinguser', password='testpassword123')
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.post(self.account_url, {'username': 'existinguser'})
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'This username is already taken. Choose another.')

    def test_change_password_successfully(self):
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

   

