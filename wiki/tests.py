from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError, Q
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from wiki.models import Article, Category, Tag
from wiki.permissions import can_edit


class CategoryTests(TestCase):
    def test_unicode_slug_and_nesting(self):
        parent = Category.objects.create(name='Касса')
        child = Category.objects.create(name='Возврат билетов', parent=parent)
        self.assertEqual(child.slug, 'возврат-билетов')
        self.assertEqual(child.breadcrumbs(), [parent, child])
        self.assertEqual(parent.children_deep_count(), 0)

    def test_slug_conflict_gets_suffix(self):
        # имя берём уникальное, чтобы не пересекаться с демо-контентом из миграции
        Category.objects.create(name='Тестовый конфликт')
        second = Category.objects.create(name='Тестовый конфликт!')
        self.assertEqual(second.slug, 'тестовый-конфликт-2')

    def test_article_protects_category(self):
        cat = Category.objects.create(name='Касса')
        Article.objects.create(title='Тест', category=cat, body='текст')
        with self.assertRaises(ProtectedError):
            cat.delete()


class ArticleTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Начало работы')

    def test_slug_and_excerpt_and_reading_time(self):
        a = Article.objects.create(
            title='Как открыть смену',
            category=self.cat,
            body='## Шаг 1\nОткрой кассу. **Важно:** проверь ящик.\n' + ('слово ' * 400),
        )
        self.assertEqual(a.slug, 'как-открыть-смену')
        self.assertNotIn('#', a.excerpt())
        self.assertGreaterEqual(a.reading_time(), 2)

    def test_tags(self):
        a = Article.objects.create(title='X', category=self.cat, body='t')
        a.tags.add(Tag.objects.get_or_create(name='касса')[0])
        self.assertEqual(str(a.tags.first()), '#касса')


class PermissionTests(TestCase):
    def test_can_edit(self):
        plain = User.objects.create_user(username='kassir', password='x')
        staff = User.objects.create_user(username='boss', password='x', is_staff=True)
        self.assertFalse(can_edit(plain))
        self.assertTrue(can_edit(staff))
        self.assertFalse(can_edit(User(username='anon')))


class WikiViewTests(TestCase):
    def setUp(self):
        self.kassir = User.objects.create_user(username='kassir2', password='x')
        self.cat = Category.objects.create(name='Начало работы')
        self.article = Article.objects.create(
            title='Как открыть смену',
            category=self.cat,
            body='## Шаг 1\nОткрой кассу <script>alert(1)</script>',
        )

    def test_home_ok_for_logged_in(self):
        self.client.force_login(self.kassir)
        response = self.client.get(reverse('wiki:home'))
        self.assertContains(response, 'Как открыть смену')

    def test_wiki_requires_login(self):
        self.assertEqual(self.client.get(reverse('wiki:home')).status_code, 302)

    def test_article_renders_and_sanitizes(self):
        self.client.force_login(self.kassir)
        response = self.client.get(self.article.get_absolute_url())
        self.assertContains(response, '<h2>Шаг 1</h2>')
        self.assertNotContains(response, '<script>')

    def test_tag_page_filters_articles(self):
        t, _ = Tag.objects.get_or_create(name='возврат')
        self.article.tags.add(t)
        Article.objects.create(  # без тега — на странице тега быть не должна
            title='Уникальная другая статья', category=self.cat, body='текст без тега')
        self.client.force_login(self.kassir)
        response = self.client.get(reverse('wiki:tag', args=[t.slug]))
        self.assertContains(response, 'Как открыть смену')
        self.assertNotContains(response, 'Уникальная другая статья')

    def test_draft_not_visible(self):
        draft = Article.objects.create(title='Секрет', category=self.cat, body='t', is_draft=True)
        self.client.force_login(self.kassir)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)

    def test_search_finds_by_title_and_body(self):
        self.client.force_login(self.kassir)
        r1 = self.client.get(reverse('wiki:search'), {'q': 'смену'})
        self.assertContains(r1, 'Как открыть смену')
        r2 = self.client.get(reverse('wiki:search'), {'q': 'касс'})
        self.assertContains(r2, 'Как открыть смену')  # по тексту, не по заголовку
        r3 = self.client.get(reverse('wiki:search'), {'q': 'нет-такого'})
        self.assertContains(r3, 'Ничего не найдено')

    def test_search_case_insensitive_cyrillic(self):
        """Регресс: SQLite icontains не работает для кириллицы — проверяем разные регистры."""
        self.client.force_login(self.kassir)
        for q in ('КАК ОТКРЫТЬ', 'Как Открыть', 'как открыть', 'СМЕНУ'):
            response = self.client.get(reverse('wiki:search'), {'q': q})
            self.assertContains(response, 'Как открыть смену', msg_prefix=f'запрос: {q}')

    def test_search_requires_login(self):
        self.assertEqual(self.client.get(reverse('wiki:search')).status_code, 302)

    def test_edit_button_only_for_staff(self):
        self.client.force_login(self.kassir)
        self.assertNotContains(self.client.get(self.article.get_absolute_url()), 'Редактировать')
        boss = User.objects.create_user(username='boss2', password='x', is_staff=True)
        self.client.force_login(boss)
        self.assertContains(self.client.get(self.article.get_absolute_url()), 'Редактировать')


class AccountBackupTests(TestCase):
    def setUp(self):
        self.kassir = User.objects.create_user(username='kassir3', password='x')
        self.admin = User.objects.create_user(username='boss3', password='x', is_staff=True)

    def test_account_requires_login(self):
        self.assertEqual(self.client.get(reverse('wiki:account')).status_code, 302)

    def test_account_page_shows_profile(self):
        self.client.force_login(self.kassir)
        response = self.client.get(reverse('wiki:account'))
        self.assertContains(response, 'kassir3')
        self.assertContains(response, 'Сотрудник (чтение)')

    def test_settings_block_only_for_staff(self):
        self.client.force_login(self.kassir)
        self.assertNotContains(self.client.get(reverse('wiki:account')), 'Резервная копия базы')
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('wiki:account')), 'Резервная копия базы')

    def test_db_backup_only_for_staff(self):
        self.client.force_login(self.kassir)
        self.assertEqual(self.client.get(reverse('wiki:db_backup')).status_code, 403)


class DbBackupDownloadTests(TransactionTestCase):
    """TransactionTestCase намеренно: TestCase держит открытую транзакцию,
    а SQLite backup API в чужой открытой транзакции виснет. В проде транзакции нет."""

    def test_db_backup_downloads_file(self):
        admin = User.objects.create_user(username='boss4', password='x', is_staff=True)
        self.client.force_login(admin)
        response = self.client.get(reverse('wiki:db_backup'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.sqlite3', response['Content-Disposition'])
        body = b''.join(response.streaming_content)
        self.assertTrue(body.startswith(b'SQLite format 3'))
        self.assertGreater(len(body), 0)


class DemoSeedTests(TestCase):
    """Тестовая БД строится миграциями с нуля — проверяем, что на чистом проде
    после migrate сразу есть учебный демо-контент."""

    def test_demo_content_seeded_by_migrations(self):
        self.assertGreaterEqual(Category.objects.count(), 5)
        self.assertGreaterEqual(Article.objects.count(), 6)
        self.assertTrue(Article.objects.filter(title='Частые вопросы').exists())
        child = Category.objects.filter(slug='возврат-и-обмен-билетов').first()
        self.assertIsNotNone(child, 'вложенная категория должна существовать')
        self.assertEqual(child.parent.slug, 'касса')

    def test_demo_articles_searchable(self):
        """Демо-статьи находятся поиском (search_text заполнен в миграции)."""
        self.assertTrue(Article.objects.filter(
            Q(search_text__contains='x-отчёт')).exists())

    def test_unseed_removes_demo_and_keeps_user_content(self):
        """Откат 0005 реально чистит демо (по заголовкам) и не трогает своё."""
        import importlib
        from django.apps import apps
        seed_demo = importlib.import_module('wiki.migrations.0005_seed_demo')

        mine = Category.objects.create(name='Моя папка')
        Article.objects.create(title='Моя инструкция', category=mine,
                               body='как у нас принято')
        seed_demo.unseed(apps, None)

        self.assertFalse(Article.objects.filter(title='Частые вопросы').exists())
        self.assertFalse(Category.objects.filter(slug='касса').exists())
        self.assertFalse(Tag.objects.filter(name='касса').exists())
        self.assertTrue(Article.objects.filter(title='Моя инструкция').exists())
        self.assertTrue(Article.objects.filter(
            title__startswith='Добро').exists(), 'welcome из 0002 трогать нельзя')


class AdminSearchTests(TestCase):
    """Поиск админки на SQLite-проде: `icontains` по кириллице регистрозависим,
    поэтому у админов кастомный get_search_results."""

    def test_article_admin_finds_cyrillic_in_any_case(self):
        from wiki.admin import ArticleAdmin
        ma = ArticleAdmin(Article, admin.site)
        found, _ = ma.get_search_results(None, Article.objects.all(), 'добро')
        self.assertTrue(found.filter(title__startswith='Добро').exists(),
                        'строчное «добро» обязано находить «Добро…»')

    def test_category_admin_finds_cyrillic_in_any_case(self):
        from wiki.admin import CategoryAdmin
        Category.objects.create(name='Помощь покупателю')
        ca = CategoryAdmin(Category, admin.site)
        found, _ = ca.get_search_results(None, Category.objects.all(), 'помощь покупателю')
        self.assertEqual([c.name for c in found], ['Помощь покупателю'])

    def test_admin_search_like_wildcards_are_literal(self):
        from wiki.admin import ArticleAdmin
        ma = ArticleAdmin(Article, admin.site)
        found, _ = ma.get_search_results(None, Article.objects.all(), '%')
        self.assertFalse(found.exists(), '«%» не должен матчить всё подряд')


class CategoryCycleTests(TestCase):
    def test_parent_cycle_rejected_in_clean(self):
        a = Category.objects.create(name='Альфа')
        b = Category.objects.create(name='Бета', parent=a)
        a.parent = b
        with self.assertRaises(ValidationError):
            a.clean()

    def test_legal_nesting_passes_clean(self):
        a = Category.objects.create(name='Альфа')
        b = Category(name='Бета', parent=a)
        b.full_clean(exclude=['slug'])  # без цикл-сценария — чисто


class EditorTests(TestCase):
    """Редактор статей на сайте: права, сохранение, превью, загрузка картинок."""

    def setUp(self):
        self.staff = User.objects.create_user('zavhoz', password='x', is_staff=True)
        self.cashier = User.objects.create_user('kassir', password='x')
        self.cat = Category.objects.create(name='Касса')

    def test_cashier_redirected_from_editor(self):
        self.client.login(username='kassir', password='x')
        r = self.client.get(reverse('wiki:new'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r.url)

    def test_staff_creates_article_with_tags(self):
        self.client.login(username='zavhoz', password='x')
        r = self.client.post(reverse('wiki:new'), {
            'title': 'Как закрыть кассу', 'category': self.cat.pk,
            'body': '## Шаг 1\nСнять X-отчёт', 'tags_input': '#касса, Закрытие;',
        })
        art = Article.objects.get(title='Как закрыть кассу')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, art.get_absolute_url())
        self.assertEqual(art.author, self.staff)
        self.assertEqual({t.name for t in art.tags.all()}, {'касса', 'закрытие'})
        # обычному читателю статья видна
        self.client.login(username='kassir', password='x')
        self.assertContains(self.client.get(art.get_absolute_url()), 'Снять X-отчёт')

    def test_draft_creation_redirects_home_and_hidden(self):
        self.client.login(username='zavhoz', password='x')
        r = self.client.post(reverse('wiki:new'), {
            'title': 'Заготовка', 'category': self.cat.pk,
            'body': 'пишем потом', 'is_draft': 'on',
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse('wiki:home'))
        art = Article.objects.get(title='Заготовка')
        self.client.login(username='kassir', password='x')
        self.assertEqual(self.client.get(art.get_absolute_url()).status_code, 404)

    def test_edit_updates_body_and_tags(self):
        art = Article.objects.create(title='Правка', category=self.cat, body='раз')
        art.tags.set([Tag.objects.create(name='старый')])
        self.client.login(username='zavhoz', password='x')
        self.client.post(reverse('wiki:edit', args=[art.slug]), {
            'title': 'Правка', 'category': self.cat.pk,
            'body': 'два', 'tags_input': 'новый',
        })
        art.refresh_from_db()
        self.assertEqual(art.body, 'два')
        self.assertEqual([t.name for t in art.tags.all()], ['новый'])

    def test_preview_uses_same_sanitizer_as_page(self):
        self.client.login(username='zavhoz', password='x')
        r = self.client.post(reverse('wiki:preview'), {
            'body': '**жир** <script>alert(1)</script> <img src=x onerror=alert(1)>',
        })
        html = r.content.decode()
        self.assertIn('<strong>жир</strong>', html)
        self.assertNotIn('<script>', html)
        self.assertNotIn('onerror', html)

    def test_upload_compresses_to_jpeg(self):
        from io import BytesIO

        from PIL import Image

        from django.test import override_settings

        buf = BytesIO()
        Image.new('RGB', (2400, 1600), 'red').save(buf, format='PNG')
        buf.seek(0)
        buf.name = 'screen.png'
        with override_settings(MEDIA_ROOT=self.settings_media_root()):
            self.client.login(username='zavhoz', password='x')
            r = self.client.post(reverse('wiki:upload'), {'file': buf})
            data = r.json()
            self.assertTrue(data['url'].endswith('.jpg'), data)
            self.assertIn('/media/wiki/', data['url'])
            from django.conf import settings
            path = data['url'].replace(settings.MEDIA_URL, settings.MEDIA_ROOT + '/')
            self.assertLessEqual(max(Image.open(path).size), 1400)

    def settings_media_root(self):
        import tempfile
        return tempfile.mkdtemp()

    def test_upload_rejects_non_image(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.login(username='zavhoz', password='x')
        r = self.client.post(reverse('wiki:upload'), {
            'file': SimpleUploadedFile('virus.txt', b'not a picture', content_type='image/png'),
        })
        self.assertEqual(r.status_code, 400)
        self.assertIn('error', r.json())
