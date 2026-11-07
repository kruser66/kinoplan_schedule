"""Учебный демо-контент вики: категории (с вложенностью), теги, статьи-примеры.

Создаётся при деплое, чтобы было «с чего начинать» и видно, как оформлять статьи.
Идемпотентна (get_or_create), обратима (unseed удаляет только демо-сущности).
Удалить демо с прода: manage.py migrate wiki 0004 — откатит только эту миграцию
(welcome-статья из 0002 останется, её удалять в админке); либо снести демо-статьи
и категории галочками в админке.
ВНИМАНИЕ: unseed опознаёт демо по заголовкам/слагам/именам — если за время жизни
продажи заведут свою статью «Частые вопросы» или тег «касса», откат удалит и их.
"""
import datetime

from django.db import migrations
from django.utils.text import slugify


def _slug(Model, title, slug_field='slug'):
    base = slugify(title, allow_unicode=True) or 'bezzagolovok'
    slug, n = base, 1
    while Model.objects.filter(**{slug_field: slug}).exists():
        n += 1
        slug = f'{base}-{n}'
    return slug


DEMO_CATEGORY_SLUGS = ['помощь', 'работа-с-контентом', 'касса', 'возврат-и-обмен-билетов']
# слаги демо-статей при allow_unicode кириллические и могут получить суффикс
# -2 при коллизии — удаляем по заголовкам, они у seed стабильные (get_or_create по ним)
DEMO_ARTICLE_TITLES = [
    'Как добавить изображение в статью',
    'Оформление и структура статьи',
    'Частые вопросы',
    'Открытие и закрытие смены',
    'Возврат билета зрителю',
]
# ровно те теги, что создаёт seed (несовпадение с art() = враньё в откате)
DEMO_TAG_NAMES = ['навигация', 'редактор', 'форматирование', 'faq',
                  'данные', 'касса', 'смены', 'возврат']


def seed(apps, schema_editor):
    Category = apps.get_model('wiki', 'Category')
    Tag = apps.get_model('wiki', 'Tag')
    Article = apps.get_model('wiki', 'Article')
    User = apps.get_model('auth', 'User')

    admin = User.objects.filter(username='admin').first()

    def cat(name, parent=None, order=10):
        found = Category.objects.filter(name=name).first()
        if found:
            return found
        return Category.objects.create(
            name=name, slug=_slug(Category, name), parent=parent, order=order)

    def tag(name):
        found = Tag.objects.filter(name=name).first()
        if found:
            return found
        return Tag.objects.create(name=name, slug=_slug(Tag, name))

    def art(title, category, body, tag_names=()):
        found = Article.objects.filter(title=title).first()
        if not found:
            found = Article.objects.create(
                title=title, slug=_slug(Article, title), category=category, body=body,
                author=admin, search_text=f'{title}\n{body}'.lower(),
                created_at=datetime.datetime.now(tz=datetime.timezone.utc),
                updated_at=datetime.datetime.now(tz=datetime.timezone.utc))
        for tag_name in tag_names:
            found.tags.add(tag(tag_name))

    nachalo = Category.objects.filter(slug='nachalo-raboty').first()
    pomosh = cat('Помощь', order=2)
    content = cat('Работа с контентом', order=3)
    kassa = cat('Касса', order=4)
    cat('Возврат и обмен билетов', parent=kassa, order=1)

    art('Как добавить изображение в статью', content, """
Пока прямого редактора на сайте нет, картинки вставляются markdown-ссылкой в медиафайл,
уже загруженный на сервер (папка `media/`):

    ![подпись](/media/imya.png)

**Как подготовиться:**
1. Попросите администратора загрузить картинку (например, скриншот киноплана);
2. В статье на новой строке вставьте ссылку вида выше;
3. Сохраните статью в админке — картинка появится на странице.

Когда подключим редактор с загрузкой, способ станет проще — статья будет обновлена.
""", ('редактор', 'навигация'))

    art('Оформление и структура статьи', content, """
Хорошая статья отвечает на один конкретный вопрос и легко просматривается.

## Структура

- **Заголовок** — вопрос или задача: «Как вернуть билет», а не «Билеты».
- **Первый абзац** — краткий ответ на вопрос.
- **Шаги** — нумерованный список (`1.` `2.` `3.`).
- **Важное** — **жирным**, предупреждения — цитатой (`>` в начале строки).

## Чего избегать

- простыней текста без заголовков;
- скриншотов whole экранов без подписи;
- дублей: лучше сослаться на существующую статью.

Примеры форматирования — в статье «Добро пожаловать в Базу знаний».
""", ('редактор', 'форматирование'))

    art('Частые вопросы', pomosh, """
**Где хранятся статьи?** В базе данных проекта на нашем сервере; доступ из браузера после входа.

- **Кто может писать?** Только администратор.
- **Кто может читать?** Все сотрудники после входа.
- **Ищется всё?** Да — заголовки и текст, в любом регистре.
- **Что означают #решетки внизу статей?** Это теги, по ним статья можно найти.
- **Что если инструкция устарела?** Скажите администратору — обновим.
""", ('faq', 'данные'))

    art('Открытие и закрытие смены', kassa, """
## Открытие смены

1. Включить терминал, войти под своей учётной записью.
2. Пересчитать ночную наличность, зафиксировать в отчёте.
3. Открыть X-отчёт.

## Закрытие смены

1. Закрыть продажи за 10 минут до последнего сеанса.
2. Снять Z-отчёт, сверить с терминалом.
3. Сдать наличность по акту.

> Это демо-пример оформления. Реальный регламент — у администратора.
""", ('касса', 'смены'))

    art('Возврат билета зрителю', Category.objects.filter(
            slug='возврат-и-обмен-билетов').first() or nachalo, """
Возврат оформляется в киноплане до начала сеанса.

1. Найти билет по номеру или телефону;
2. Кнопка **Вернуть** → выбрать причину возврата;
3. Деньги вернутся тем же способом, которым была оплата (1-3 банковских дня).

> После начала сеанса возврат — только с разрешения директора.

Это демо-пример вложенной категории: «Касса» → «Возврат и обмен билетов».
""", ('касса', 'возврат'))


def unseed(apps, schema_editor):
    Category = apps.get_model('wiki', 'Category')
    Tag = apps.get_model('wiki', 'Tag')
    Article = apps.get_model('wiki', 'Article')
    Article.objects.filter(title__in=DEMO_ARTICLE_TITLES).delete()
    Category.objects.filter(slug__in=DEMO_CATEGORY_SLUGS).delete()
    Tag.objects.filter(name__in=DEMO_TAG_NAMES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0004_backfill_search_text'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
