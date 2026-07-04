# Document Search Service

Простой поисковый сервис по текстам документов. Данные хранятся в PostgreSQL,
полнотекстовый поиск — через Elasticsearch.

## Стек

- **FastAPI** — веб-фреймворк (async, автогенерация OpenAPI-схемы)
- **PostgreSQL + SQLAlchemy 2.0 (async, asyncpg)** — хранилище документов
- **Elasticsearch 8.15** — поисковый индекс по тексту документов
- **pytest + pytest-asyncio + httpx** — функциональные тесты
- **Docker Compose** — оркестрация всего стека

## Структура проекта

```
app/
  core/config.py         # настройки (pydantic-settings), читаются из переменных окружения
  db/
    model.py             # SQLAlchemy-модель Document
    session.py             # async engine/session, init_db()
  es/
    client.py               # AsyncElasticsearch, ensure_index()
  schemas/
    document.py             # Pydantic-схема ответа DocumentOut
  services/
    search_service.py       # вся бизнес-логика: поиск, удаление
  api/
    routes.py               # HTTP-роуты
  main.py                    # точка входа, lifespan (init_db + ensure_index)
scripts/
  import_csv.py               # разовая загрузка CSV в БД + ES
  export_openapi.py            # генерация docs.json
tests/
  conftest.py                  # фикстуры: тестовая БД/индекс, ES-синглтон
  test_parsing.py                # юнит-тесты parse_rubrics
  test_search_service.py          # тесты сервисного слоя
  test_api.py                      # тесты HTTP-эндпоинтов
data/
  posts.csv                        # исходные данные
docker-compose.yml
Dockerfile
docs.json                            # OpenAPI-документация
```

## Запуск

### 1. Поднять стек

```bash
docker compose up --build -d
```

Поднимутся три сервиса: `postgres`, `elasticsearch`, `app`. Дождитесь, пока все
будут в статусе `healthy`:

```bash
docker compose ps
```

Таблицы в Postgres и индекс в Elasticsearch создаются автоматически при старте
приложения.

### 2. Загрузить данные из CSV

Положите файл с данными в `data/posts.csv`, затем:

```bash
docker compose exec app python -m scripts.import_csv data/posts.csv
```

Скрипт читает CSV, парсит поля, пишет документы в Postgres батчами по 200 и
одновременно индексирует их в Elasticsearch через `bulk`-запрос.

### 3. Проверить, что всё работает

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

Или руками:

```bash
curl "http://localhost:8000/search?q=кот"
curl -X DELETE "http://localhost:8000/documents/1"
```

## API

Полная OpenAPI-схема — в [`docs.json`](./docs.json) или на `/docs` у
запущенного сервиса.

### `GET /search?q=<текст>`

Ищет документы по тексту, возвращает не более 20 штук, отсортированных по
`created_date` (сначала новые). В ответе — все поля документа из БД (`id`,
`rubrics`, `text`, `created_date`).

### `DELETE /documents/{id}`

Удаляет документ из БД и из поискового индекса. `404`, если документа с таким
id нет.

## Тесты

Тесты бьют по реальным Postgres/Elasticsearch (в отдельных, тестовых
БД/индексе) — не по мокам. Поэтому перед запуском стек должен быть поднят.

Тестовая база данных `docsearch_test` создаётся автоматически при **первом**
поднятии стека (init-скрипт `docker/init-test-db.sql`, подключённый как volume
к контейнеру `postgres` — Postgres выполняет такие скрипты один раз, при
инициализации пустого volume). Если стек уже поднимался раньше на этой
машине и volume не пустой, создайте базу вручную:

```bash
docker compose exec postgres psql -U docsearch -d docsearch -c "CREATE DATABASE docsearch_test;"
```

Запуск тестов:

```bash
docker compose exec app pytest tests/ -v
```

Что покрыто:

- юнит-тесты чистой функции `parse_rubrics` (без БД/ES) — нормальный и
  некорректный вход;
- поиск находит документ по совпадению в тексте;
- результаты отсортированы по `created_date` по убыванию;
- в ответе присутствуют все поля документа, а не только текст;
- удаление убирает документ и из БД, и из поисковой выдачи;
- HTTP-слой: `200` на успешный поиск, `404` на удаление несуществующего id.

## Переменные окружения

| Переменная | По умолчанию (локально) | В Docker Compose |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://docsearch:docsearch@localhost:5432/docsearch` | `postgresql+asyncpg://docsearch:docsearch@postgres:5432/docsearch` |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | `http://elasticsearch:9200` |

Внутри Docker-сети контейнеры обращаются друг к другу по имени сервиса
(`postgres`, `elasticsearch`) и **внутреннему** порту контейнера (`5432`,
`9200`), а не по порту, проброшенному наружу на хост. Порт Postgres на
хосте вынесен на `5433` (чтобы не конфликтовать с локально установленным
Postgres) — используйте `localhost:5433`, если подключаетесь с хост-машины
(например, через `psql` или DBeaver).
