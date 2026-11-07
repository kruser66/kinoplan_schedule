from django.db import migrations


def backfill_search_text(apps, schema_editor):
    Article = apps.get_model('wiki', 'Article')
    for article in Article.objects.iterator():
        article.search_text = f'{article.title}\n{article.body}'.lower()
        article.save(update_fields=['search_text'])


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0003_article_search_text'),
    ]

    operations = [
        migrations.RunPython(backfill_search_text, migrations.RunPython.noop),
    ]
