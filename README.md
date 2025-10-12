# LeafFlow

Лаконичное API, ведущее чай «от листа до корзины» — быстро, надёжно, легко расширять.

## Требования
- Python 3.12

## Установка (локально)

```bash
    python -m venv .venv
    # macOS/Linux:
    source .venv/bin/activate
    # Windows PowerShell:
    # .venv\Scripts\Activate.ps1
    # установить проект и dev-зависимости
    pip install -e .
```

## Конфигурация
Конфиг читается из переменных окружения (см. `src/leaf_flow/config.py`). Можно использовать файл `.env` в корне репозитория.

Минимальный пример `.env`:

```bash
    # --- База данных ---
    POSTGRES_USER=your_user
    POSTGRES_PASSWORD=your_password
    POSTGRES_DB=your_db
    DB_HOST=127.0.0.1
    DB_PORT=5432
```

## Запуск

### Локально

```bash
    python3 -m leaf_flow
```

### Docker

В репозитории есть `Dockerfile`. Пример сборки и запуска:

```bash
    docker build -t leaf-flow:local .
    docker run --rm \
      -e POSTGRES_USER=... \
      -e POSTGRES_PASSWORD=... \
      -e POSTGRES_DB=... \
      -e DB_HOST=... \
      -e DB_PORT=5432 \
      leaf-flow:local
```