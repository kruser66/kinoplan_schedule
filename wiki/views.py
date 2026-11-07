import os
import sqlite3
import tempfile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponseForbidden, StreamingHttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from wiki.models import Article, Category, Tag
from wiki.permissions import can_edit
from wiki.render import render_markdown


@login_required
def account(request):
    """Профиль + настройки (только staff). Открывается карточкой пользователя в сайдбаре."""
    return render(request, 'wiki/account.html', {
        'nav_active': 'account',
        'db_name': os.path.basename(str(settings.DATABASES['default']['NAME'])),
        'is_sqlite': settings.DATABASES['default']['ENGINE'].endswith('sqlite3'),
    })


def _chunks_then_delete(path):
    """Отдаём файл кусками; в конце (или при обрыве) удаляем временный снимок."""
    try:
        with open(path, 'rb') as fh:
            while chunk := fh.read(64 * 1024):
                yield chunk
    finally:
        if os.path.exists(path):
            os.unlink(path)


@login_required
def db_backup(request):
    """Консистентный снимок всей SQLite-базы через backup API (безопасно при работе gunicorn)."""
    if not can_edit(request.user):
        return HttpResponseForbidden('Выгрузку базы может делать только администратор')
    if not settings.DATABASES['default']['ENGINE'].endswith('sqlite3'):
        return HttpResponseForbidden('Автовыгрузка настроена только для SQLite')

    # connection.connection может быть None, если БД в этом запросе
    # ещё не трогали — ensure_connection поднимает её явно
    connection.ensure_connection()
    tmp = tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False)
    tmp.close()
    dst = sqlite3.connect(tmp.name)
    try:
        connection.connection.backup(dst)  # «бэкап на горячую», не блокирует записи
    finally:
        dst.close()

    filename = f"kzzfun-db-{timezone.localdate():%Y-%m-%d}.sqlite3"
    response = StreamingHttpResponse(
        _chunks_then_delete(tmp.name),
        content_type='application/octet-stream',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['X-Robots-Tag'] = 'noindex'
    return response


@login_required
def home(request):
    categories = Category.objects.filter(parent__isnull=True)
    articles = Article.objects.filter(is_draft=False)
    return render(request, 'wiki/home.html', {
        'categories': categories,
        'articles': articles,
        'nav_active': 'all',
    })


@login_required
def search(request):
    query = request.GET.get('q', '').strip()
    articles = Article.objects.filter(is_draft=False)
    if query:
        # search_text хранится в нижнем регистре (см. Article.save) —
        # иначе SQLite не находит кириллицу без учёта регистра.
        articles = articles.filter(search_text__contains=query.lower())
    return render(request, 'wiki/search_results.html', {
        'query': query,
        'articles': articles,
    })


@login_required
def category_page(request, slug):
    category = get_object_or_404(Category, slug=slug)
    return render(request, 'wiki/article_list.html', {
        'category': category,
        'articles': category.articles.filter(is_draft=False),
        'nav_active': category.slug,
    })


@login_required
def tag_page(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    return render(request, 'wiki/tag_articles.html', {
        'tag': tag,
        'articles': tag.article_set.filter(is_draft=False),
    })


@login_required
def article_page(request, slug):
    article = get_object_or_404(Article, slug=slug, is_draft=False)
    return render(request, 'wiki/article_detail.html', {
        'article': article,
        'body_html': render_markdown(article.body),
    })
