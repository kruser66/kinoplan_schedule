from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from schedule.cleanup import cleanup_empty_schedules, cleanup_old_images
from schedule.models import ScheduleImage


class Command(BaseCommand):
    """Ручная чистка старых картинок расписаний.

    Обычно не нужна: очистка происходит автоматически при логине
    (см. schedule/cleanup.py). Команда — для ручного запуска и проверок.
    """

    help = ('Чистка старых картинок расписаний (по умолчанию старше 30 дней) '
            'и пустых недель без картинок')

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30,
                            help='Сколько дней хранить картинки (по умолчанию 30)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Только показать, что удалилось бы')

    def handle(self, *args, **options):
        if options['dry_run']:
            cutoff = timezone.now() - timedelta(days=options['days'])
            names = ScheduleImage.objects.filter(created_at__lt=cutoff).values_list(
                'image', flat=True)
            empty = cleanup_empty_schedules(dry_run=True)
            self.stdout.write(f'[dry-run] картинок к удалению {len(names)} шт: '
                              + ', '.join(names))
            self.stdout.write(f'[dry-run] пустых недель без картинок: {empty} шт')
            return

        result = cleanup_old_images(days=options['days'])
        self.stdout.write(self.style.SUCCESS(
            f"Удалено: {result['rows']} записей картинок, {result['files']} файлов "
            f"(уже отсутствовали: {result['missing']}), "
            f"пустых недель: {result['schedules']}"
        ))
