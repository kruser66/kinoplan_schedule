# Wiki MVP — план разработки (ветка `wiki_mvp`)

Основа: `docs/WIKI_PLAN.md` (решение — приложение `wiki` внутри текущего Django) +
прототип UI «База знаний» (сайдбар категорий, карточки статей, поиск, теги).

## Текущее состояние проекта (на что опираемся)
- Django 5.2 + SQLite (`db.sqlite3`), gunicorn -w 2, VDS ~1 ГБ RAM.
- Одно приложение `schedule`; `/` (`index`) редиректит на текущую неделю `week_schedule`.
- Авторизация `django.contrib.auth`, всё под `@login_required`, `LOGIN_REDIRECT_URL='/'`.
- UI: Bootstrap 5.3 (CDN), общий шаблон `templates/index.html` (без base-шаблона), `static/logo.svg`.
- `media/` + `STATICFILES_DIRS = assets/` настроены.

## UX-решение: главная-портал
- `/` — лёгкий портал: две карточки-кнопки «Расписание» и «База знаний» (в стиле прототипа).
- Шапка с навигацией (Расписание | База знаний | Выйти | username) на всех страницах обоих разделов.
- Прямые ссылки: `/schedule/` → текущая неделя, `/wiki/` → вики.

---

## Этап 0 — Подготовка (≈0.5 ч)
1. `python manage.py startapp wiki`; добавить `'wiki'` в `INSTALLED_APPS`.
2. `kzzfun/urls.py`: `path('wiki/', include('wiki.urls'))`, `path('schedule/', include('schedule.urls'))`
   (в `schedule/urls.py` префиксы путей не меняем — only include-путь; редирект `/schedule/` → текущая неделя).
3. Зависимости в `requirements.txt`: `markdown`, `bleach` (санитайз HTML после рендера — защита от XSS).
4. Общий `templates/base.html`: шапка (logo, nav, привет/выйти) + `{% block content %}`;
   `index.html` расписания приводится к наследованию от него (без изменения логики).

## Этап 1 — Модели (≈1 ч)
`wiki/models.py`:
- `Category`: `name`, `slug`, `parent` (FK on self, null=True — вложенность до 2 уровней,
  breadcrumbs рекурсивно; treebeard не тянем — категорий мало, зависимостей меньше),
  `order`, `__str__`.
- `Tag`: `name`, `slug`.
- `Article`: `title`, `slug`, `category` (FK), `body` (TextField, markdown),
  `tags` (M2M, blank), `is_draft`, `author` (FK User, на Create через admin),
  `created_at`, `updated_at`; `Meta.ordering = ['-updated_at']`;
  метод `get_absolute_url`, метод `excerpt()` (первые ~200 символов для карточки),
  метод `reading_time()` (≈200 слов/мин — для «1 мин» как в прототипе).
- `wiki/admin.py`: `CategoryAdmin` (order, parent), `ArticleAdmin`
  (prepopulated slug, list_display с датой/категорией/статусом, list_filter по категориям,
  search_fields title/body, filter_horizontal tags, author=request.user автоматически).
- Миграции + сид 1 категории и статьи-знакомства «Добро пожаловать в Базу знаний».

## Этап 2 — Чтение (≈1.5–2 ч)
`wiki/urls.py` + `wiki/views.py` (все `@login_required`):
- `/wiki/` — home: сайдбар категорий со счётчиками, chip-фильтр, карточки всех статей
  (категория, дата «сегодня/вчера/4 нояб.», excerpt, reading_time, теги).
- `/wiki/category/<slug>/` — статьи категории.
- `/wiki/article/<slug>/` — статья: рендер markdown (`markdown` + extensions:
  `tables`, `fenced_code`, `nl2br`; прогон через `bleach` с allowlist тегов).
  Breadcrumbs, кнопка «Редактировать» для staff (ведёт в admin).
- `/wiki/search/?q=` — `icontains` по title/body, подсветка не обязательна (этап 2.5 → FTS5).
- Пагинация: `Paginator`, 12 карточек/стр.

## Этап 3 — Портал на `/` (≈1 ч)
- `schedule/views.py`: новая view `portal` (или `home`) вместо редиректа `index`:
  рендер `templates/home.html` — 2 карточки; на карточке вики — счётчик статей и категорий.
- Старое поведение сохраняется кликом по карточке «Расписание» (→ текущая неделя).
- Проверить `LOGIN_REDIRECT_URL='/'` → теперь попадание на портал (ок).
- В `index.html` расписания: шапка с ссылкой «📚 База знаний».

## Этап 4 — Шаблоны в стиле прототипа (≈1–2 ч)
- `wiki/templates/wiki/`: `base_wiki.html` (extends `base.html`, layout: сайдбар + контент),
  `category_list.html` (home), `article_list.html`, `article_detail.html`, `search_results.html`.
- Стилизация карточек/chips под прототип (Bootstrap 5 + немного кастомного CSS в `static/`).
  Палитра: фиолетовый акцент из прототипа или зелёная тема сайта — решить при вёрстке.
- Адаптив: сайдбар сворачивается в бургер на мобиле (Bootstrap collapse).

## Этап 5 — Проверка и полировка (≈1 ч)
- `[ ]` вход не-staff: читает, не видит «Редактировать»; staff: правит в admin.
- `[ ]` slug-конфликты, русские заголовки (slug из admin, `allow_unicode=True`).
- `[ ]` XSS-проверка: статья с `<script>` → санитайз вырезает.
- `[ ]` битых media-ссылок нет; `python manage.py check`; прогон на gunicorn -w 2.
- Merge checklist: `migrate` на проде, `collectstatic` если понадобится.

## Что сознательно НЕ в MVP
- Редактор на сайте (martor/textarea+превью) — после вопроса 2 из WIKI_PLAN.
- История правок (simple-history), вложения картинок — этап 2 плана.
- FTS5-поиск, JSON API, Telegram-бот — этапы 2–3 WIKI_PLAN.
- Разграничение доступа по ролям (guardian) — ждём ответ на вопрос 4.

## Открытые вопросы к пользователю (из WIKI_PLAN, блокирующих нет)
1. Кто читает: только сотрудники (текущий план) или часть публично?
2. Правки: MVP = Django admin (по плану) — подтверждаем?
3. История правок: нужен ли сразу simple-history (дёшево, +1 зависимость)?
4. Роли/доступ к разделам: общая вики (текущий план) или разграничение?
5. Теги из прототипа — оставляем в MVP (в плане выше они есть, дёшево)?

## Оценка
≈6–8 часов чистой работы, укладывается в 2–3 вечера. Порядок этапов 0→1→2→3→4→5,
каждый этап — рабочий коммит в `wiki_mvp`.
