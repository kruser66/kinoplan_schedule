"""Одноразовое наполнение dev-базы демо-контентом вики.
Не миграция: на проде этот контент не появляется.
Запуск: .venv/bin/python manage.py shell < wiki/demo_content.py
"""
from django.contrib.auth.models import User

from wiki.models import Article, Category, Tag

admin = User.objects.filter(username='admin').first()


def cat(name, parent=None, order=10):
    c, _ = Category.objects.get_or_create(name=name, defaults={'parent': parent, 'order': order})
    return c


def tag(*names):
    return [Tag.objects.get_or_create(name=n)[0] for n in names]


def art(title, category, body, tags=()):
    a, created = Article.objects.get_or_create(
        title=title, defaults={'category': category, 'body': body, 'author': admin})
    if tags:
        flat = [t for tg in tags for t in (tg if isinstance(tg, list) else [tg])]
        a.tags.add(*flat)  # M2M add идемпотентен
    return a


nachalo = Category.objects.get(slug='nachalo-raboty')
pomosh = cat('Помощь', order=2)
content = cat('Работа с контентом', order=3)
kassa = cat('Касса', order=4)
vozvr = cat('Возврат и обмен билетов', parent=kassa, order=1)

t_start, t_nav = tag('старт', 'навигация')
t_edit, t_fmt = tag('редактор', 'форматирование')
t_faq, t_data = tag('faq', 'данные')
t_cash, t_shift = tag('касса', 'смены')
t_return = tag('возврат')

art('Как добавить изображение в статью', content, """
В редактор можно вставлять изображения тремя способами: выбрать файл, перетащить его или вставить из буфера обмена.

Пошагово:

1. Открой статью в режиме редактирования;
2. Поставь курсор в нужное место текста;
3. Прикрепи файл — он загрузится в общий каталог картинок.

**Пока вставка картинок из редактора не подключена!**
Картинки, загруженные в media/, вставляются ссылкой:

    ![подпись](/media/imya.png)
""", tags=(t_edit, t_nav))

art('Оформление и структура статьи', content, """
Хорошая статья отвечает на конкретный вопрос и легко просматривается. Используйте заголовки, короткие абзацы, списки и выделение.

## Структура

- **Заголовок** — вопрос или задача: «Как вернуть билет», а не «Билеты».
- **Первый абзац** — краткий ответ.
- **Шаги** — нумерованный список 1. 2. 3.
- **Важное** — **жирным**, предупреждения — цитатой.

## Чего избегать

- простыней текста без заголовков;
- скриншотов whole экранов без подписи;
- дублей: лучше сослаться на существующую статью.
""", tags=(t_edit, t_fmt))

art('Частые вопросы', pomosh, """
Где хранятся статьи? В базе данных проекта (SQLite) на нашем сервере; доступ из браузера после входа.

- **Кто может писать?** Только администратор.
- **Кто может читать?** Все сотрудники после входа.
- **Ищется всё?** Да, заголовки и текст, в любом регистре.
- **Что если инструкция устарела?** Скажите администратору — обновим.
""", tags=(t_faq, t_data))

art('Открытие и закрытие смены', kassa, """
## Открытие смены

1. Включить терминал, войти под своей учётной записью.
2. Пересчитать ночную наличность, зафиксировать в отчёте.
3. Открыть X-отчёт.

## Закрытие смены

1. Закрыть продажи за 10 минут до последнего сеанса.
2. Снять Z-отчёт, сверить с терминалом.
3. Сдать наличность по акту.
""", tags=(t_cash, t_shift))

art('Возврат билета зрителю', vozvr, """
Возврат оформляется в киноплане до начала сеанса.

1. Найти билет по номеру или телефону;
2. Кнопка **Вернуть** → причина возврата;
3. Деньги уйдут тем же способом, которым была оплата (1-3 банковских дня).

> После начала сеанса возврат — только с разрешения директора.
""", tags=(t_cash, t_return))

print('категории:', Category.objects.count(), '| статьи:', Article.objects.count(), '| теги:', Tag.objects.count())
for c in Category.objects.all():
    parent = c.parent.name if c.parent else '—'
    print(f'  {c.name} [родитель: {parent}] → статей с вложенными: {c.children_deep_count()}')
for a in Article.objects.all():
    print(f'  «{a.title}» → {a.category.name} | теги: {", ".join(str(t) for t in a.tags.all()) or "нет"}')
