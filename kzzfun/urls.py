from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # ЭТУ СТРОКУ ДОБАВИТЬ
    path('wiki/', include('wiki.urls')),
    path('', include('schedule.urls'))
]
