from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from wiki.models import Article, Category, Tag
from wiki.render import render_markdown


@login_required
def home(request):
    categories = Category.objects.filter(parent__isnull=True)
    articles = Article.objects.filter(is_draft=False)
    return render(request, 'wiki/home.html', {
        'categories': categories,
        'articles': articles,
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
