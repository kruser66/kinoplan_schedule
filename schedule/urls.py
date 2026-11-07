from django.urls import path
from django.conf import settings
from schedule.views import current_week, index, week_schedule, delete_image
from django.conf.urls.static import static

urlpatterns = [
    path('', index, name='index'),
    path('schedule/', current_week, name='current_week'),
    path('schedule/<int:year>/<int:week>/', week_schedule, name='week_schedule'),
    path('delete/<int:pk>', delete_image, name='delete_image')
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
