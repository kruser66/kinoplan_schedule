import logging

from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in

logger = logging.getLogger(__name__)


def cleanup_on_login(sender, request, user, **kwargs):
    """При входе — прибрать картинки старше месяца (см. schedule/cleanup.py)."""
    try:
        from schedule.cleanup import cleanup_old_images
        result = cleanup_old_images()
        if result['rows']:
            logger.info('Автоочистка картинок: %s', result)
    except Exception:
        logger.exception('Автоочистка картинок не удалась (на вход не влияет)')


class ScheduleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'schedule'

    def ready(self):
        user_logged_in.connect(cleanup_on_login)
