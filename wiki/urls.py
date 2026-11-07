from django.urls import path

from wiki.views import (account, article_edit, article_new, article_page,
                        category_page, db_backup, home, preview, search,
                        tag_page, upload_image)

app_name = 'wiki'

urlpatterns = [
    path('', home, name='home'),
    path('search/', search, name='search'),
    path('account/', account, name='account'),
    path('account/db-backup/', db_backup, name='db_backup'),
    # str (не slug): слаги русские, slug-конвертер их не пропускает
    path('tag/<str:slug>/', tag_page, name='tag'),
    path('category/<str:slug>/', category_page, name='category'),
    # новые/редактирование — до ловушки article/<str:slug>, иначе 'new'
    # был бы принят за slug статьи
    path('article/new/', article_new, name='new'),
    path('article/<str:slug>/edit/', article_edit, name='edit'),
    path('article/<str:slug>/', article_page, name='article'),
    path('preview/', preview, name='preview'),
    path('upload/', upload_image, name='upload'),
]
