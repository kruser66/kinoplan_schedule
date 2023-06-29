import os
from django.conf import settings


TEMPLATE_IMAGE = settings.TEMPLATE

API_URL = settings.API_URL
API_KEY = settings.API_KEY

FONT = os.path.join(settings.BASE_DIR, 'static', "tahoma.ttf")
FONT_BOLD = os.path.join(settings.BASE_DIR, 'static', "tahomabd.ttf")