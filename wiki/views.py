import os
import sqlite3
import tempfile

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import connection
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseForbidden, JsonResponse,
                         StreamingHttpResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from wiki.forms import ArticleForm
from wiki.images import BadImage, save_wiki_image
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


# ---------- редактор статей (только staff, см. wiki.permissions.can_edit) ----------

@user_passes_test(can_edit, login_url='/accounts/login/')
def article_new(request):
    return _article_form(request, Article(), is_new=True)


@user_passes_test(can_edit, login_url='/accounts/login/')
def article_edit(request, slug):
    article = get_object_or_404(Article, slug=slug)
    return _article_form(request, article, is_new=False)


def _article_form(request, article, is_new):
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            obj = form.save()
            if not obj.author:
                obj.author = request.user
                obj.save(update_fields=['author'])
            messages.success(request, 'Статья сохранена')
            return redirect(obj if not obj.is_draft else 'wiki:home')
    else:
        form = ArticleForm(instance=article)
    return render(request, 'wiki/article_form.html', {
        'form': form, 'article': article, 'is_new': is_new,
        'nav_active': 'edit',
    })


@user_passes_test(can_edit, login_url='/accounts/login/')
def preview(request):
    """Через то же render_markdown, что рендерит боевую статью — превью
    показывает ровно то, что увидит читатель, включая фильтры bleach."""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    return HttpResponse(render_markdown(request.POST.get('body', '')))


@user_passes_test(can_edit, login_url='/accounts/login/')
def upload_image(request):
    """Картинка для вставки в статью: сжимается и кладётся в media/wiki/."""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    upload = request.FILES.get('file')
    if not upload:
        return JsonResponse({'error': 'Файл не пришёл'}, status=400)
    try:
        url = save_wiki_image(upload, hint=upload.name)
    except BadImage as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    alt = os.path.splitext(upload.name)[0][:60]
    return JsonResponse({'url': url, 'alt': alt})
