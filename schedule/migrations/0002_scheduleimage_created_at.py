import datetime

from django.db import migrations, models


def backfill_created_at(apps, schema_editor):
    """Возраст старых картинок = дата начала их кинонедели."""
    ScheduleImage = apps.get_model('schedule', 'ScheduleImage')
    for img in ScheduleImage.objects.filter(created_at__isnull=True).select_related('schedule'):
        year, week = img.schedule.year, img.schedule.week
        try:
            monday = datetime.date.fromisocalendar(year, max(week, 1), 1)
            created = datetime.datetime(
                monday.year, monday.month, monday.day, tzinfo=datetime.timezone.utc)
        except ValueError:
            created = datetime.datetime.now(tz=datetime.timezone.utc)
        ScheduleImage.objects.filter(pk=img.pk).update(created_at=created)


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduleimage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, blank=True, null=True,
                                       verbose_name='Создана'),
        ),
        migrations.RunPython(backfill_created_at, migrations.RunPython.noop),
    ]
