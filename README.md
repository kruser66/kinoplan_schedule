# Утилита вывода расписания в шаблон

Скрипт работает с [API Киноплан](https://api.kinoplan.ru/doc/).
и выводит в шаблон `schedule.jpg` расписание на следующую неделю.

Формируется новое изображение с заполненным расписанием.

## Как установить

Python3 должен быть уже установлен. Затем используйте pip (или pip3, если есть конфликт с Python2) для установки зависимостей:

```bash
pip install -r requirements.txt
```

## Для работы чат-бота понадобятся следующие переменные окружения:

Ключ доступа к API (запрашивается у разработчика)
```
API_KEY='YOUR_API_KEY'
```

## Запуск модуля

```bash
python make_schedule.py
```


# Цель проекта

Код написан для автоматизации рутинных операций [Кинотеатр "Кристалл Синема" г.Ревда](https://kino.kzzfun.ru/).