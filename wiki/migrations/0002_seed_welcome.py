from django.db import migrations


WELCOME_BODY = """Добро пожаловать в Базу знаний кинотеатра!

Здесь собираются **инструкции и ответы на рабочие вопросы**: как что делать,
где что лежит, что делать если «не работает».

## Как пользоваться

- **Слева** — категории разделов, сверху — поиск по всем статьям.
- Статья открывается кликом по карточке.
- Тексты пишет и редактирует администратор; смотреть могут все сотрудники.

## Оформление статей

Хорошая статья отвечает на один конкретный вопрос. Используйте:

- заголовки `##` для шагов;
- нумерованные списки для последовательности действий;
- **выделение жирным** важного, `код` — для названий кнопок и программ.

> Если чего-то не хватает — скажите администратору, добавим.
"""


def seed(apps, schema_editor):
    Category = apps.get_model('wiki', 'Category')
    Article = apps.get_model('wiki', 'Article')

    cat, _ = Category.objects.get_or_create(
        slug='nachalo-raboty',
        defaults={'name': 'Начало работы', 'order': 1},
    )
    Article.objects.get_or_create(
        slug='dobro-pozhalovat-v-bazu-znaniy',
        defaults={
            'title': 'Добро пожаловать в Базу знаний',
            'category': cat,
            'body': WELCOME_BODY,
        },
    )


def unseed(apps, schema_editor):
    Article = apps.get_model('wiki', 'Article')
    Category = apps.get_model('wiki', 'Category')
    Article.objects.filter(slug='dobro-pozhalovat-v-bazu-znaniy').delete()
    Category.objects.filter(slug='nachalo-raboty').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
