from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from wiki.models import Article, Category
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
def category_page(request, slug):
    category = get_object_or_404(Category, slug=slug)
    return render(request, 'wiki/article_list.html', {
        'category': category,
        'articles': category.articles.filter(is_draft=False),
    })


@login_required
def article_page(request, slug):
    article = get_object_or_404(Article, slug=slug, is_draft=False)
    return render(request, 'wiki/article_detail.html', {
        'article': article,
        'body_html': render_markdown(article.body),
    })
