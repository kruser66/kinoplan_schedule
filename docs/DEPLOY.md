# Деплой ветки `wiki_mvp` на прод (VDS)

Обновление 2026-11-07. Ветка: `wiki_mvp` (готова к слиянию в `master`).

## 1. Перед деплоем (на сервере)

```bash
cd /home/kruser/python/kino/kinoplan_schedule

# БЭКАП — обязательно. Горячий снимок SQLite (сайт можно не останавливать):
.venv/bin/python -c "
import sqlite3
src = sqlite3.connect('db.sqlite3')
dst = sqlite3.connect('backup-before-wiki.sqlite3')
with dst: src.backup(dst)
print('backup ok')"
mv backup-before-wiki.sqlite3 backup-before-wiki-$(date +%F).sqlite3

# и копия картинок:  cp -r media media-backup-$(date +%F)
```

## 2. Код и зависимости

```bash
git fetch && git checkout master && git merge --ff-only wiki_mvp   # или merge без ff
# если на проде были локальные правки — вместо ff сделать обычный merge wiki_mvp

.venv/bin/pip install -r requirements.txt   # добавятся markdown==3.11.*, bleach==6.4.*
```

## 3. Миграции и статика

```bash
.venv/bin/python manage.py migrate
# применяет: wiki 0001-0004 (модели, приветственная статья, search_text)
#           schedule 0002-0003 (created_at картинок + датировка по кинонеделе)
# Эффект на данных: у старых картинок проставится возраст; при ближайшем
# логине картинки старше 30 дней автоудалятся (файлы из media тоже).

.venv/bin/python manage.py collectstatic --noinput   # подтянет wiki/wiki.css в STATIC_ROOT
```

## 4. Прочие настройки прод-сервера

- `.env`: ничего обязательного не добавилось. Опционально:
  - `SECURE_COOKIES=True` — secure-флаги для session/CSRF-кук (сайт за nginx+https);
  - `MEDIA_URL`/`MEDIA_ROOT` теперь читаются из своих ключей (раньше по багу — из STATIC_*).
    Если в .env этих ключей нет (как сейчас) — поведение не меняется.
- nginx: без изменений (`/static/`, `/media/` как были).
- перезапуск: `sudo systemctl restart <gunicorn-юнит>` (и uwsgi/nginx не трогать).

## 5. Проверка после деплоя (2 минуты)

- [ ] `/` — портал с двумя карточками; вход работает;
- [ ] `/schedule/` — текущая неделя, генерация картинки расписания работает;
- [ ] `/wiki/` — главная, категории, статья, поиск «добро» находит «Добро…»;
- [ ] `/admin/` — видны «Статьи/Категории/Теги»; создать категорию+статью;
- [ ] `/wiki/` под кассиром: читает, кнопок «Новая статья»/«Редактировать» нет, `/admin/` — 403;
- [ ] карточка юзера слева внизу → «Профиль» → «⬇ Сохранить базу данных» качает .sqlite3;
- [ ] в `media/` устаревшие картинки расписаний исчезли после первого логина.

## 6. Откат (если что-то пошло не так)

```bash
git checkout master@{до merge}   # или git revert коммитов
.venv/bin/python manage.py migrate wiki 0001   # откат wiki-миграций (0004->0001, обратимы)
cp backup-before-wiki-DATE.sqlite3 db.sqlite3  # полный откат по бэкапу
sudo systemctl restart <gunicorn-юнит>
```

## Известные осознанные решения

- Кириллические slug (allow_unicode) — URLConverter берёт `str` (slug-конвертер кириллицу не пропускает).
- Поиск: регистронезависимость для кириллицы через поле `search_text` (lower в Python), т.к. SQLite `icontains` не работает с кириллицей.
- Права: вики читают все вошедшие, пишут только staff; расписание — как исторически, любой вошедший (включая удаление картинок).
- Автоочистка картинок >30 дней — при логине (без крона), ошибка чистки не ломает вход.
- Тесты: 27 шт (`manage.py test schedule wiki`); тест выгрузки БД — TransactionTestCase (в TestCase backup API виснет из-за открытой транзакции).
