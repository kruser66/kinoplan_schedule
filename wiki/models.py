import re

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from wiki.render import render_markdown


def _unique_slug(model, slug_field, title, pk=None):
    """Slug из заголовка (юникод разрешён), при конфликте добавляет -2, -3..."""
    base = slugify(title, allow_unicode=True) or 'bezzagolovok'
    slug, n = base, 1
    qs = model.objects.all()
    if pk:
        qs = qs.exclude(pk=pk)
    while qs.filter(**{slug_field: slug}).exists():
        n += 1
        slug = f'{base}-{n}'
    return slug


class Category(models.Model):
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField('URL', max_length=120, unique=True, allow_unicode=True)
    parent = models.ForeignKey(
        'self', verbose_name='Родительская категория',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children',
    )
    order = models.PositiveSmallIntegerField(
        'Порядок', default=0, help_text='Меньше — выше в списке')

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Category, 'slug', self.name, pk=self.pk)
        super().save(*args, **kwargs)

    def clean(self):
        """Запрет цикла parent (cat A -> B -> A): иначе breadcrumbs() уходит в
        бесконечный while, а children_deep_count() — в RecursionError, т.е.
        500/висячий запрос на любой странице вики с деревом."""
        super().clean()
        if self.parent_id and self.pk:
            node, seen = self.parent, {self.pk}
            while node is not None:
                if node.pk in seen:
                    raise ValidationError(
                        {'parent': 'Категория не может быть своей собственной '
                                   'подкатегорией (получился цикл).'})
                seen.add(node.pk)
                node = node.parent

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('wiki:category', args=[self.slug])

    def breadcrumbs(self):
        """Путь от корня до этой категории: [(категория, ...), ...]"""
        chain, node = [], self
        while node is not None:
            chain.append(node)
            node = node.parent
        return list(reversed(chain))

    def children_deep_count(self):
        """Статей в категории и во всех подкатегориях."""
        total = self.articles.count()
        for child in self.children.all():
            total += child.children_deep_count()
        return total


class Tag(models.Model):
    name = models.CharField('Название', max_length=50, unique=True)
    slug = models.SlugField('URL', max_length=60, unique=True, allow_unicode=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Tag, 'slug', self.name, pk=self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'#{self.name}'


class Article(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    slug = models.SlugField('URL', max_length=220, unique=True, allow_unicode=True)
    category = models.ForeignKey(
        Category, verbose_name='Категория',
        on_delete=models.PROTECT, related_name='articles',
    )
    body = models.TextField('Текст (markdown)')
    search_text = models.TextField('Поисковый текст', blank=True, default='', editable=False)
    tags = models.ManyToManyField(Tag, verbose_name='Теги', blank=True)
    is_draft = models.BooleanField('Черновик', default=False)
    author = models.ForeignKey(
        'auth.User', verbose_name='Автор',
        on_delete=models.SET_NULL, null=True, related_name='wiki_articles',
    )
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Изменена', auto_now=True)

    class Meta:
        verbose_name = 'статья'
        verbose_name_plural = 'статьи'
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Article, 'slug', self.title, pk=self.pk)
        # Поиск: SQLite не умеет регистронезависимый LIKE для кириллицы,
        # поэтому храним нормализованный нижний регистр (Python справляется корректно).
        self.search_text = f'{self.title}\n{self.body}'.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('wiki:article', args=[self.slug])

    def breadcrumbs(self):
        return self.category.breadcrumbs()

    def excerpt(self, length=200):
        """Человеческое превью для карточки: читаемый текст, а не обломки разметки.

        Бывало так, что превью выглядело как 'Как пользоваться - Слева —
        категории': markdown-разметка просто вычиталась посимвольно, и от
        '#*`>- ' оставались огрызки. Теперь чистка построчная:
        код-блоки выкидываем, маркеры заголовков/цитат/списков снимаем,
        ссылки оставляем текстом, всё склеиваем в аккуратную строку.
        """
        body = re.sub(r'```.*?```', ' ', self.body, flags=re.S)  # код-блоки врезать целиком
        body = re.sub(r'`([^`]*)`', r'\1', body)                 # inline-код — без штрихов
        body = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', body)   # ссылки/картинки — текстом
        parts = []
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            line = re.sub(r'^#{1,6}\s+', '', line)      # заголовки — просто строкой
            line = re.sub(r'^>\s*', '', line)           # цитаты
            line = re.sub(r'^(?:[-*+]|\d+[.)])\s+', '', line)  # маркеры списков
            line = re.sub(r'\*\*(.+?)\*\*|\*([^*]+)\*|__?(.+?)__?', lambda m: m.group(1) or m.group(2) or m.group(3) or '', line)
            parts.append(line.strip())
        text = ' '.join(' '.join(parts).split())
        return text[:length].rstrip(' ,;.') + '…' if len(text) > length else text

    @property
    def preview_html(self):
        """Карточка — это карточка: ровный анонс в пару строк, а не «портянка».

        Берём только вступительные абзацы (без заголовков, списков, цитат,
        таблиц — они делали карточки разношерстными по высоте), склеиваем в
        один абзац и рендерим ТЕМ же markdown+bleach, что и страницу: в
        карточке живое выделение и ссылки, но форма карточки едина.
        Обрезка до 3-4 строк — CSS (line-clamp), многоточие честное.
        """
        body = re.sub(r'```.*?```', '', self.body, flags=re.S)
        body = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', body)  # картинки в анонс не лезут

        def is_prose(s):  # не заголовок/цитата/список/таблица/HTML
            return not re.match(r'^(#{1,6}\s|>|[-*+]\s|\d+[.)]\s|\||<)', s)
        blocks, total = [], 0
        for block in re.split(r'\n\s*\n', body.strip()):
            block = block.strip()
            if not block or not is_prose(block):
                continue
            blocks.append(block)
            total += len(block)
            if total >= 260:
                break
        if not blocks:  # статья сразу со списка/таблицы — показываем хоть что-то
            blocks = [b.strip() for b in re.split(r'\n\s*\n', body.strip()) if b.strip()][:1]
        # склейка через \n = мягкий перенос: markdown соберёт один <p>
        return mark_safe(render_markdown('\n'.join(blocks)))

    def reading_time(self):
        words = len(self.body.split())
        return max(1, round(words / 200))
