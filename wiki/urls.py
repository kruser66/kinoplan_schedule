from django.urls import path

from wiki.views import account, article_page, category_page, db_backup, home, search, tag_page

app_name = 'wiki'

urlpatterns = [
    path('', home, name='home'),
    path('search/', search, name='search'),
    path('account/', account, name='account'),
    path('account/db-backup/', db_backup, name='db_backup'),
    path('tag/<str:slug>/', tag_page, name='tag'),
    # str (не slug): слаги русские, slug-конвертер их не пропускает
    path('category/<str:slug>/', category_page, name='category'),
    path('article/<str:slug>/', article_page, name='article'),
]
