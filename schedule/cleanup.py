"""Автоочистка старых картинок расписаний и пустых недель.

Запускается автоматически при входе пользователя (сигнал user_logged_in) —
крон не нужен. Логика одна для сигнала и management-команды.

Первый прогон после деплоя может быть тяжёлым (на проде ~100k пустых недель):
в DEPLOY.md предписано сначала выгулять management-команду вручную. Чтобы
случайный ранний логин не подвесил вход, пустые недели удаляются пачками,
а когда чистить нечего — лишний запрос не выполняется вовсе.
"""
from datetime import timedelta

from django.core.files.storage import default_storage
from django.utils import timezone

from schedule.models import Schedule, ScheduleImage

STORAGE_DAYS = 30
DELETE_BATCH = 1000


def cleanup_empty_schedules(dry_run=False):
    """Удаляет «бирки» недель без картинок.

    Раньше такая строка создавалась на каждый просмотр недели (даже просто
    листание стрелками) — на проде их набежали десятки тысяч. Пустая запись
    бесполезна, а при повторном открытии недели чинно создастся заново
    (теперь только при генерации картинки). Возвращает число (удалённых).
    Удаляем пачками: один DELETE на десятки тысяч id — это долгий запрос
    прямо во время логина.
    """
    ids = list(Schedule.objects.filter(images__isnull=True).values_list('id', flat=True))
    if ids and not dry_run:
        for i in range(0, len(ids), DELETE_BATCH):
            Schedule.objects.filter(id__in=ids[i:i + DELETE_BATCH]).delete()
    return len(ids)


def cleanup_old_images(days=STORAGE_DAYS, dry_run=False):
    """Возвращает dict(rows=..., files=..., missing=..., schedules=...)."""
    cutoff = timezone.now() - timedelta(days=days)
    result = {'rows': 0, 'files': 0, 'missing': 0}

    if dry_run:
        result['rows'] = ScheduleImage.objects.filter(created_at__lt=cutoff).count()
        result['schedules'] = cleanup_empty_schedules(dry_run=True)
        return result

    for img in ScheduleImage.objects.filter(created_at__lt=cutoff):
        try:
            if default_storage.exists(img.image.name):
                default_storage.delete(img.image.name)
                result['files'] += 1
            else:
                result['missing'] += 1  # файла и так нет — запись всё равно чистим
        except OSError:
            result['missing'] += 1  # сбой диска не повод бросать весь прогон
        img.delete()
        result['rows'] += 1

    # после удаления старых картинок часть недель осталась без них — прибрать
    result['schedules'] = cleanup_empty_schedules()
    return result
