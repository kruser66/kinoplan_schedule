from django.urls import path

from wiki.views import article_page, category_page, home, search

app_name = 'wiki'

urlpatterns = [
    path('', home, name='home'),
    path('search/', search, name='search'),
    # str (не slug): слаги русские, slug-конвертер их не пропускает
    path('category/<str:slug>/', category_page, name='category'),
    path('article/<str:slug>/', article_page, name='article'),
]
