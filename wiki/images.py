"""Загрузка картинок в вики: единственная точка, где файл становится media-файлом.

Правило дня: на проде 1.6 ГБ свободного диска, поэтому любую загрузку
пережимаем — длинная сторона <= 1400px, JPEG quality 82. Снимки экрана
документов это переживают спокойно (текст читается), а megabyte-скрины
с телефона превращаются в ~150-250 КБ.
"""
import os
import uuid
from io import BytesIO

from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from PIL import Image, ImageOps

MAX_SIDE = 1400
QUALITY = 82
MAX_INPUT_BYTES = 10 * 1024 * 1024  # принимаем на вход до 10 МБ, на выходе будет меньше


class BadImage(Exception):
    pass


def save_wiki_image(upload, hint=''):
    """Проверяет, сжимает, кладёт в MEDIA_ROOT/wiki/ГГГГ/ММ/. Возвращает MEDIA_URL-путь."""
    if upload.size > MAX_INPUT_BYTES:
        raise BadImage('Файл больше 10 МБ')
    try:
        img = Image.open(upload)
        img.load()
    except Exception:
        raise BadImage('Это не картинка (или битый файл)')

    img = ImageOps.exif_transpose(img)
    if img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, format='JPEG', quality=QUALITY, optimize=True)

    stamp = timezone.localdate().strftime('%Y/%m')
    folder = os.path.join(settings.MEDIA_ROOT, 'wiki', stamp)
    os.makedirs(folder, exist_ok=True)
    name = f'{slugify(hint, allow_unicode=True) or "izobrazhenie"}-{uuid.uuid4().hex[:8]}.jpg'
    path = os.path.join(folder, name)
    with open(path, 'wb') as fh:
        fh.write(buf.getvalue())

    return f'{settings.MEDIA_URL}wiki/{stamp}/{name}'
