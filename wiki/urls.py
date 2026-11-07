from django.urls import path

from wiki.views import wiki_placeholder

app_name = 'wiki'

urlpatterns = [
    path('', wiki_placeholder, name='home'),
]
