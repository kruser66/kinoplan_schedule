from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class WikiSmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='kassir', password='testpass123')

    def test_login_page_ok(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_wiki_requires_login(self):
        response = self.client.get(reverse('wiki:home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_wiki_placeholder_ok_for_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('wiki:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'База знаний')

    def test_index_redirects_to_current_week(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 302)  # редирект на текущую неделю
