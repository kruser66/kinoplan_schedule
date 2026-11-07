from django.core.management.base import BaseCommand

from schedule.cleanup import cleanup_old_images


class Command(BaseCommand):
    """Ручная чистка старых картинок расписаний.

    Обычно не нужна: очистка происходит автоматически при логине
    (см. schedule/cleanup.py). Команда — для ручного запуска и проверок.
    """

    help = 'Чистка старых картинок расписаний (по умолчанию старше 30 дней)'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30,
                            help='Сколько дней хранить картинки (по умолчанию 30)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Только показать, что удалилось бы')

    def handle(self, *args, **options):
        if options['dry_run']:
            from schedule.models import ScheduleImage
            from datetime import timedelta
            from django.utils import timezone
            cutoff = timezone.now() - timedelta(days=options['days'])
            names = ScheduleImage.objects.filter(created_at__lt=cutoff).values_list(
                'image', flat=True)
            self.stdout.write(f'[dry-run] к удалению {len(names)} шт: ' + ', '.join(names))
            return

        result = cleanup_old_images(days=options['days'])
        self.stdout.write(self.style.SUCCESS(
            f"Удалено: {result['rows']} записей, {result['files']} файлов "
            f"(уже отсутствовали: {result['missing']})"
        ))
