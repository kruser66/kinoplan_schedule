"""Дедупликация Schedule и уникальное ограничение (year, week).

Причина: просмотр страницы недели раньше делал get_or_create на каждый GET,
а без unique-ограничения параллельные запросы создавали дубликаты —
на проде набежало >100k строк. Миграция:
1) склеивает дубликаты одной недели в одну запись (картинки переносятся
   к «выжившему», файлы на диске не трогаем);
2) вешает UniqueConstraint — с ним get_or_create становится атомарным
   и дубликаты невозможны в принципе.

Обратима: откат снимает только ограничение (склеивание не отменяется).
"""
from django.db import migrations, models


def dedupe(apps, schema_editor):
    Schedule = apps.get_model('schedule', 'Schedule')
    ScheduleImage = apps.get_model('schedule', 'ScheduleImage')

    groups = {}
    for pk, year, week in Schedule.objects.order_by('year', 'week', 'id').values_list(
            'id', 'year', 'week'):
        groups.setdefault((year, week), []).append(pk)

    drop_ids = []
    for ids in groups.values():
        keep, rest = ids[0], ids[1:]
        if not rest:
            continue
        # картинки проваливших копий переезжают к выжившему (их может быть
        # несколько на неделю — это штативно), теряется только лишняя бирка
        ScheduleImage.objects.filter(schedule_id__in=rest).update(schedule_id=keep)
        drop_ids.extend(rest)

    # чистим пачками — на проде это может быть >100k id
    for i in range(0, len(drop_ids), 500):
        Schedule.objects.filter(id__in=drop_ids[i:i + 500]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0003_created_at_from_week'),
    ]

    operations = [
        migrations.RunPython(dedupe, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='schedule',
            constraint=models.UniqueConstraint(
                fields=('year', 'week'), name='unique_year_week'),
        ),
    ]
