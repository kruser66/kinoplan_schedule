from datetime import timedelta

from django import template
from django.utils import timezone

from wiki.models import Article, Category

register = template.Library()

_MONTHS = {1: 'янв.', 2: 'фев.', 3: 'мар.', 4: 'апр.', 5: 'мая', 6: 'июн.',
           7: 'июл.', 8: 'авг.', 9: 'сент.', 10: 'окт.', 11: 'нояб.', 12: 'дек.'}


@register.filter
def friendly_date(dt):
    """'сегодня' / 'вчера' / '4 нояб.' / '4 нояб. 2025'."""
    if not dt:
        return ''
    now = timezone.localtime()
    d = timezone.localtime(dt)
    if d.date() == now.date():
        return 'сегодня'
    if d.date() == (now - timedelta(days=1)).date():
        return 'вчера'
    if d.year == now.year:
        return f'{d.day} {_MONTHS[d.month]}'
    return f'{d.day} {_MONTHS[d.month]} {d.year}'


@register.simple_tag
def wiki_root_categories():
    """Корневые категории с детьми; тегаем в шаблонах вики, а не контекст-процессором,
    чтобы не дёргать БД на страницах расписания."""
    return Category.objects.filter(parent__isnull=True).prefetch_related('children')


@register.simple_tag
def wiki_article_total():
    return Article.objects.filter(is_draft=False).count()


@register.simple_tag
def wiki_category_total():
    return Category.objects.count()
