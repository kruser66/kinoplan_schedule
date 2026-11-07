"""Автоочистка старых картинок расписаний.

Запускается автоматически при входе пользователя (сигнал user_logged_in) —
крон не нужен. Логика одна для сигнала и management-команды.
"""
from datetime import timedelta

from django.core.files.storage import default_storage
from django.utils import timezone

STORAGE_DAYS = 30


def cleanup_old_images(days=STORAGE_DAYS, dry_run=False):
    """Возвращает dict(rows=..., files=..., missing=...)."""
    from schedule.models import ScheduleImage

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
    return result
