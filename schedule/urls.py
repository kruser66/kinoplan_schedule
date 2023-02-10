from django.urls import path
from schedule.views import index

urlpatterns = [
    path('', index, name='index'),
]