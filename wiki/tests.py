from django.contrib.auth.models import User
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
        from django.db.models import ProtectedError
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
        from wiki.models import Tag
        t, _ = Tag.objects.get_or_create(name='возврат')
        self.article.tags.add(t)
        other = Article.objects.create(
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
        self.assertContains(r2, 'Как открыть смену')  # нашёл по тексту (подстрока «кассy»), не по заголовку
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
        from django.db.models import Q
        self.assertTrue(Article.objects.filter(
            Q(search_text__contains='x-отчёт')).exists())

