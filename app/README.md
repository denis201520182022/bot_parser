## Описание

Сервис монитоит транспорт на сайте `moigruz.ru` и каждые **10 секунд**:

- **публично** читает списки транспорта для двух типов кузова:
  - **Рефрижератор** (`body=3`, URL как в поиске транспорта на сайте [`moigruz.ru`](https://www.moigruz.ru/trucks/?from=&to=&rfrom=&rto=&date=&days=&body=3&cfrom=&cto=&vfrom=&vto=&load=&unload=&i=1))
  - **Изотермический** (`body=4`, URL аналогичный, как на [`moigruz.ru`](https://www.moigruz.ru/trucks/?from=&to=&rfrom=&rto=&date=&days=&body=4&cfrom=&cto=&vfrom=&vto=&load=&unload=))
- находит **новые `truck_id`** (без дублей, с учётом локального состояния и уже записанного в Google Sheets);
- **только для новых заявок** заходит в карточку транспорта (через авторизованную сессию с куками) и достаёт контакты;
- дописывает строки в **две разные Google-таблицы** (отдельно Реф и Изотермический), старые данные не удаляются.

## Модули

- `moigruz/config.py` — работа с переменными окружения, URL, настройки.
- `moigruz/utils.py` — утилиты (очистка телефонов и т.п.).
- `moigruz/http_client.py` — HTTP-запросы без авторизации.
- `moigruz/auth.py` — авторизация на сайте, сохранение/загрузка куки.
- `moigruz/scrape_public.py` — публичный парсинг списка транспорта (только `truck_id` и время).
- `moigruz/scrape_private.py` — приватный парсинг карточки транспорта (контакты).
- `moigruz/state.py` — локальное состояние, список уже обработанных `truck_id` для каждого типа кузова.
- `moigruz/sheets.py` — интеграция с Google Sheets (чтение существующих ID, запись новых строк).
- `main.py` — главный цикл мониторинга (опрос каждые 10 секунд).

## Переменные окружения

Минимальный набор (см. также пример в `.env.example`):

- **POLL_INTERVAL_SEC** — интервал опроса в секундах (по умолчанию `10`).
- **MOIGRUZ_EMAIL** — логин на `moigruz.ru`.
- **MOIGRUZ_PASSWORD** — пароль на `moigруз.ru`.
- **STATE_DIR** — каталог для локального состояния (`state` по умолчанию).
- **MOIGRUZ_COOKIES_PATH** — путь к файлу куки (по умолчанию `state/cookies.pkl`).
- **GOOGLE_SERVICE_ACCOUNT_FILE** — путь к JSON-файлу сервисного аккаунта Google.
- **GSHEET_REF_SPREADSHEET_ID** — ID Google-таблицы для Рефрижераторов.
- **GSHEET_ISO_SPREADSHEET_ID** — ID Google-таблицы для Изотермических.
- **GSHEET_WORKSHEET_NAME** — имя листа в обоих документах (по умолчанию `Лист1`).
- **MOIGRUZ_PROXY** — (опционально) HTTP(S) прокси, например `http://user:pass@host:port`. Если не задано, можно использовать стандартные `HTTP_PROXY` / `HTTPS_PROXY`.

## Формат Google-таблиц

Скрипт сам создаёт заголовок (если лист пустой), колонки:

1. `truck_id`
2. `company_name`
3. `contact_name`
4. `phone`
5. `skype`
6. `has_viber`
7. `has_whatsapp`
8. `has_telegram`
9. `rating`
10. `pro_status`
11. `post_time`

Данные **только дописываются**; уже существующие строки не трогаются. Дубли предотвращаются по `truck_id`:

- локально (через файлы состояния в `STATE_DIR`);
- по фактически существующим строкам в таблице (чтение первой колонки).

## Локальный запуск

1. Создайте сервисный аккаунт в Google Cloud и выдайте ему доступ на редактирование к двум нужным Google-таблицам.
2. Скачайте JSON-файл аккаунта и укажите его путь в `GOOGLE_SERVICE_ACCOUNT_FILE`.
3. Создайте файл `.env` по образцу `.env.example` и заполните значения.
4. Установите зависимости:

```bash
pip install pipenv
pipenv install
```

5. Запустите мониторинг:

```bash
POLL_INTERVAL_SEC=10 pipenv run python main.py
```

Скрипт будет работать бесконечным циклом с паузой ~10 секунд между итерациями.

## Запуск через Docker

1. Соберите образ:

```bash
docker compose build
```

2. Подготовьте файл `.env` рядом с `docker-compose.yml` (можно взять за основу `.env.example`).

   - Внутри контейнера путь `GOOGLE_SERVICE_ACCOUNT_FILE` должен указывать на существующий файл,
     например `/app/creds/service-account.json`. Его можно примонтировать томом:
     отредактируйте `docker-compose.yml`, добавив раздел `volumes` при необходимости.
3. Запустите в режиме мониторинга:

```bash
docker compose up
```

Сервис будет автоматически перезапускаться (`restart: unless-stopped`) и опрашивать сайт по расписанию раз в 10 секунд.
