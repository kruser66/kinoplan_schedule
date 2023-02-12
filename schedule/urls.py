from django.urls import path
from django.conf import settings
from schedule.views import index
from django.conf.urls.static import static

urlpatterns = [
    path('', index, name='index'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)