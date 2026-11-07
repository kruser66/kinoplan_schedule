from django.contrib import admin
from wiki.models import Article, Category, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'order', 'articles_count']
    list_editable = ['order']
    list_display_links = ['name']
    prepopulated_fields = {'slug': ['name']}
    search_fields = ['name']

    @admin.display(description='статей')
    def articles_count(self, obj):
        return obj.children_deep_count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {'slug': ['name']}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_draft', 'updated_at', 'author']
    list_filter = ['category', 'is_draft']
    search_fields = ['title', 'body']
    prepopulated_fields = {'slug': ['title']}
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)
