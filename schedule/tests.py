from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class PortalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='kassir', password='x')

    def test_anonymous_redirected_to_login(self):
        self.assertEqual(self.client.get(reverse('index')).status_code, 302)

    def test_portal_shows_both_sections(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Расписание')
        self.assertContains(response, 'База знаний')
        self.assertContains(response, reverse('current_week'))

    def test_current_week_redirects_to_this_week_schedule(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('current_week'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/schedule/', response['Location'])

    def test_wiki_still_requires_login(self):
        self.assertEqual(self.client.get(reverse('wiki:home')).status_code, 302)
