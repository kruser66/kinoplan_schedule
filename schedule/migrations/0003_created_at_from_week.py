import datetime

from django.db import migrations


def set_created_at_from_week(apps, schema_editor):
    """AddField с auto_now_add выставил всем «сейчас»; честный возраст —
    дата начала кинонедели, но не позже уже стоявшего значения (eregeneration)."""
    ScheduleImage = apps.get_model('schedule', 'ScheduleImage')
    for img in ScheduleImage.objects.filter(created_at__isnull=False).select_related('schedule'):
        year, week = img.schedule.year, img.schedule.week
        try:
            monday = datetime.date.fromisocalendar(year, max(week, 1), 1)
            week_dt = datetime.datetime(
                monday.year, monday.month, monday.day, tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
        if week_dt < img.created_at:
            ScheduleImage.objects.filter(pk=img.pk).update(created_at=week_dt)


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0002_scheduleimage_created_at'),
    ]

    operations = [
        migrations.RunPython(set_created_at_from_week, migrations.RunPython.noop),
    ]
