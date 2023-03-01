from django.urls import path
from django.conf import settings
from schedule.views import index, week_schedule
from django.conf.urls.static import static

urlpatterns = [
    path('', index, name='index'),
    path('schedule/<int:year>/<int:week>/', week_schedule, name='week_schedule')
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)