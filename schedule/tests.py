from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from schedule.models import Schedule, ScheduleImage


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


@override_settings(MEDIA_ROOT='/tmp/opencode/test_media')
class CleanupOldImagesTests(TestCase):
    def setUp(self):
        User.objects.create_user(username='login_user', password='pass12345')

    def _make_image(self, schedule, age_days):
        img = ScheduleImage(schedule=schedule, title=f'test-{age_days}')
        img.image.save(f'test-{age_days}.jpg', ContentFile(b'fake-jpeg'), save=True)
        ScheduleImage.objects.filter(pk=img.pk).update(
            created_at=timezone.now() - timedelta(days=age_days))
        return img

    def test_login_triggers_cleanup(self):
        schedule = Schedule.objects.create(year=2026, week=39)
        old = self._make_image(schedule, 40)
        self.assertTrue(self.client.login(username='login_user', password='pass12345'))
        self.assertFalse(ScheduleImage.objects.filter(pk=old.pk).exists())

    def test_old_images_deleted_new_kept(self):
        schedule = Schedule.objects.create(year=2026, week=40)
        old = self._make_image(schedule, 45)
        fresh = self._make_image(schedule, 10)

        call_command('cleanup_old_images', '--days', '30')

        self.assertFalse(ScheduleImage.objects.filter(pk=old.pk).exists())
        self.assertTrue(ScheduleImage.objects.filter(pk=fresh.pk).exists())
        from django.core.files.storage import default_storage
        self.assertFalse(default_storage.exists(old.image.name))
        self.assertTrue(default_storage.exists(fresh.image.name))

    def test_dry_run_keeps_everything(self):
        schedule = Schedule.objects.create(year=2026, week=41)
        old = self._make_image(schedule, 60)

        call_command('cleanup_old_images', '--days', '30', '--dry-run')

        self.assertTrue(ScheduleImage.objects.filter(pk=old.pk).exists())
