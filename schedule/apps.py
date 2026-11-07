import logging

from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in

logger = logging.getLogger(__name__)


def cleanup_on_login(sender, request, user, **kwargs):
    """При входе — прибрать картинки старше месяца и пустые недели
    (см. schedule/cleanup.py)."""
    try:
        # импорт внутри обработчика: apps.py грузится до моделей,
        # на верху файла импортировать schedule.cleanup нельзя
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
        # dispatch_uid: без него autoreload/повторная инициализация
        # регистрируют обработчик дважды — и чистка бегает дважды за логин
        user_logged_in.connect(cleanup_on_login, dispatch_uid='schedule_auto_cleanup')
