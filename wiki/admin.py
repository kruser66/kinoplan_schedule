from django.contrib import admin

from wiki.models import Article, Category, Tag


def _lower_contains_fallback(queryset, term, fields):
    """Регистронезависимый поиск для кириллицы на SQLite.

    Админский `icontains` на SQLite — это LIKE без UPPER для не-ASCII,
    т.е. по кириллице регистрозависим (тот же баг, из-за которого у Article
    есть поле `search_text`). Категории/теги — маленькие служебные таблицы,
    понижаем регистр в Python.
    """
    term = term.lower()
    pks = [obj.pk for obj in queryset
           if any(term in str(getattr(obj, field, '') or '').lower()
                  for field in fields)]
    return queryset.filter(pk__in=pks)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'order', 'articles_count']
    list_editable = ['order']
    list_display_links = ['name']
    prepopulated_fields = {'slug': ['name']}
    search_fields = ['name']

    def get_search_results(self, request, queryset, search_term):
        if search_term:
            return _lower_contains_fallback(queryset, search_term, ['name', 'slug']), False
        return super().get_search_results(request, queryset, search_term)

    @admin.display(description='статей')
    def articles_count(self, obj):
        return obj.children_deep_count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {'slug': ['name']}
    search_fields = ['name']

    def get_search_results(self, request, queryset, search_term):
        if search_term:
            return _lower_contains_fallback(queryset, search_term, ['name', 'slug']), False
        return super().get_search_results(request, queryset, search_term)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_draft', 'updated_at', 'author']
    list_filter = ['category', 'is_draft']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug': ['title']}
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at']

    def get_search_results(self, request, queryset, search_term):
        if search_term:
            # search_text уже в нижнем регистре (см. Article.save) — как во
            # фронтенд-поиске (wiki/views.py), contains экранирует LIKE-джокеры.
            return (queryset.filter(search_text__contains=search_term.lower()),
                    False)
        return super().get_search_results(request, queryset, search_term)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)
