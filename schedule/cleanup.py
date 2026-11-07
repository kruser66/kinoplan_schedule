"""Автоочистка старых картинок расписаний.

Запускается автоматически при входе пользователя (сигнал user_logged_in) —
крон не нужен. Логика одна для сигнала и management-команды.
"""
from datetime import timedelta

from django.core.files.storage import default_storage
from django.utils import timezone

from schedule.models import Schedule, ScheduleImage

STORAGE_DAYS = 30


def cleanup_empty_schedules(dry_run=False):
    """Удаляет «бирки» недель без картинок.

    Раньше такая строка создавалась на каждый просмотр недели (даже просто
    листание стрелками) — на проде их набежали десятки тысяч. Пустая запись
    бесполезна, а при повторном открытии недели чинно создастся заново
    (теперь только при генерации картинки). Возвращает число (удалённых).
    """
    empty = Schedule.objects.filter(images__isnull=True)
    count = empty.count()
    if count and not dry_run:
        empty.delete()
    return count


def cleanup_old_images(days=STORAGE_DAYS, dry_run=False):
    """Возвращает dict(rows=..., files=..., missing=..., schedules=...)."""
    cutoff = timezone.now() - timedelta(days=days)
    stale = ScheduleImage.objects.filter(created_at__lt=cutoff)

    result = {'rows': 0, 'files': 0, 'missing': 0}
    for img in stale:
        name = img.image.name
        if dry_run:
            result['rows'] += 1
            continue
        try:
            if default_storage.exists(name):
                default_storage.delete(name)
            result['files'] += 1
        except FileNotFoundError:
            result['missing'] += 1  # файла и так нет — запись всё равно чистим
        img.delete()
        result['rows'] += 1

    # после удаления старых картинок часть недель осталась без них — прибрать
    result['schedules'] = cleanup_empty_schedules(dry_run=dry_run)
    return result
