# 🍃 LeafFlow

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.118-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-316192.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io/)
[![License](https://img.shields.io/badge/license-Proprietary-gray.svg)](LICENSE)

**LeafFlow** — бэкенд для чайного интернет-магазина, построенный на FastAPI с использованием элементов чистой архитектуры (Clean Architecture) и Domain-Driven Design.  
Полнофункциональное решение «от листа до корзины» с интеграцией Telegram, системой заказов и гибким каталогом продуктов.

---

## 📋 Содержание

- [Особенности](#-особенности)
- [Технологический стек](#-технологический-стек)
- [Архитектура](#-архитектура)
- [Требования](#-требования)
- [Установка](#-установка)
  - [Локальная установка](#локальная-установка)
  - [Установка через Docker Compose](#установка-через-docker-compose)
- [Конфигурация](#-конфигурация)
- [Запуск](#-запуск)
  - [Локальный запуск](#локальный-запуск)
  - [Запуск через Docker](#запуск-через-docker)
- [Работа с БД](#-работа-с-бд)
  - [Миграции Alembic](#миграции-alembic)
  - [Деактивация продуктов и очистка корзин](#-деактивация-продуктов-и-очистка-корзин-на-уровне-postgresql)
- [API Documentation](#-api-documentation)
- [Структура проекта](#-структура-проекта)
- [Модули и функциональность](#-модули-и-функциональность)
- [Разработка](#-разработка)
- [Best Practices](#-best-practices)
- [Contributing](#-contributing)
- [Лицензия](#-лицензия)

---

## ✨ Особенности

### Ядро
- 🚀 **Асинхронная архитектура** — полностью `async/await` с FastAPI и SQLAlchemy 2.0
- 🏗️ **Чистая архитектура** — разделение на слои `domain`, `infrastructure`, `services` и `api`
- 🔄 **Unit of Work паттерн** — управление транзакциями и консистентностью данных
- 📦 **Repository паттерн** — абстракция доступа к данным с типизацией
- 🧩 **Shared Core** — доменные модели вынесены в отдельный пакет [`leaf-flow-core`](https://github.com/Mist3s/leaf-flow-core)

### Каталог и продукты
- 🍵 **Гибкая система продуктов** — категории, теги, варианты (вес/цена), профили заваривания
- 🏷️ **Динамические атрибуты** — настраиваемые характеристики товаров с различными UI-хинтами
- 🖼️ **Медиа-файлы** — загрузка и хранение изображений товаров

### Аутентификация
- 📱 **Telegram Mini App** — авторизация через initData
- 🔐 **Telegram Login Widget** — авторизация через виджет на сайте
- 📧 **Email/Password** — классическая регистрация и вход
- 🔗 **Связывание аккаунтов** — объединение Telegram и Email-аккаунтов
- 🎫 **JWT токены** — access + refresh токены с ротацией

### E-commerce
- 🛒 **Корзина** — добавление, обновление, удаление позиций
- 📦 **Заказы** — оформление с выбором способа доставки (самовывоз, курьер, СДЭК)
- 📊 **Статусы заказов** — полный жизненный цикл (created → processing → paid → fulfilled)
- ⭐ **Отзывы** — агрегация отзывов с внешних платформ (Яндекс, Google, Telegram, Avito)

### Инфраструктура
- 📨 **Уведомления** — фоновые задачи через Celery + Redis
- 🐳 **Docker** — полная контейнеризация с nginx reverse proxy
- ⚙️ **Пул соединений** — настраиваемый пул подключений к PostgreSQL

---

## 🛠 Технологический стек

| Категория          | Технологии                          |
|--------------------|-------------------------------------|
| **Framework**      | FastAPI 0.118                       |
| **Language**       | Python 3.12+                        |
| **Database**       | PostgreSQL 17 + asyncpg             |
| **ORM**            | SQLAlchemy 2.0 (async)              |
| **Migrations**     | Alembic                             |
| **Validation**     | Pydantic v2                         |
| **Auth**           | JWT (PyJWT) + bcrypt                |
| **Cache/Queue**    | Redis 7 + Celery 5.4                |
| **HTTP Client**    | httpx                               |
| **Server**         | Uvicorn / Gunicorn                  |
| **Reverse Proxy**  | nginx                               |
| **Containerize**   | Docker, Docker Compose              |
| **Shared Models**  | [leaf-flow-core](https://github.com/Mist3s/leaf-flow-core) |

---

## 🏛 Архитектура

Проект использует элементы **Clean Architecture** и **Domain-Driven Design** с прагматичными упрощениями:

- **Shared Kernel** — общие модели вынесены в пакет [`leaf-flow-core`](https://github.com/Mist3s/leaf-flow-core) для переиспользования между сервисами
- **Слоистая архитектура** — разделение на API, Services, Infrastructure и Domain
- **Unit of Work + Repository** — управление транзакциями и абстракция доступа к данным

> ⚠️ **Примечание:** SQLAlchemy-модели находятся в shared-пакете для удобства разработки. В строгой Clean Architecture они относятся к инфраструктурному слою.

```mermaid
graph TB
    subgraph "API Layer"
        A[FastAPI Routes] --> B[API Dependencies]
        A1[Auth Routes] --> B
        A2[Catalog Routes] --> B
        A3[Cart Routes] --> B
        A4[Orders Routes] --> B
        A5[Internal Routes] --> B
    end

    subgraph "Service Layer"
        C1[Auth Service]
        C2[Catalog Service]
        C3[Cart Service]
        C4[Order Service]
        C5[Notification Service]
    end

    subgraph "Infrastructure Layer"
        D[Unit of Work] --> E[Repositories]
        E --> F[SQLAlchemy Models]
        G[Database Session]
        H[Redis Client]
        I[Celery Client]
    end

    subgraph "Domain Layer"
        J[Entities]
        K[Mappers]
        L[External Interfaces]
    end

    subgraph "Shared Package: leaf-flow-core"
        M[SQLAlchemy Models]
        N[Domain Entities]
        O[Enums & Constants]
    end

    B --> C1
    B --> C2
    B --> C3
    B --> C4
    C1 --> D
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> I
    E --> G
    F --> M
    J --> N
```

### Слои приложения

| Слой               | Назначение                              | Компоненты                                   |
|--------------------|-----------------------------------------|----------------------------------------------|
| **API**            | HTTP endpoints, роутинг, валидация      | `auth`, `catalog`, `cart`, `orders`, `internal` |
| **Services**       | Бизнес-логика приложения                | Сервисы для разных доменов                   |
| **Infrastructure** | Работа с БД, Redis, внешние интеграции  | UoW, Repositories, Celery                    |
| **Domain**         | Доменные сущности, маппинг, интерфейсы  | Entities, Mappers, Externals                 |

---

## 🔗 Связанные репозитории

| Репозиторий | Описание |
|-------------|----------|
| [leaf-flow-core](https://github.com/Mist3s/leaf-flow-core) | Shared-пакет с SQLAlchemy моделями, доменными сущностями и enum'ами |

---

## 📦 Требования

- **Python:** 3.12 или выше  
- **PostgreSQL:** 17 (рекомендуется через Docker)  
- **Redis:** 7+ (для Celery и кэширования)
- **Docker / Docker Compose** (для production-развёртывания)

---

## 🚀 Установка

### Локальная установка

Клонируйте репозиторий:

```bash
git clone https://github.com/Mist3s/leaf-flow.git
cd leaf-flow
```

Создайте и активируйте виртуальное окружение:

```bash
python -m venv .venv

# macOS/Linux:
source .venv/bin/activate

# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Windows CMD:
.venv\Scripts\activate.bat
```

Установите зависимости:

```bash
pip install -e .
```

> Флаг `-e` устанавливает проект в режиме разработки (*editable mode*).

### Установка через Docker Compose

```bash
docker-compose up -d
```

---

## ⚙️ Конфигурация

Приложение использует переменные окружения для конфигурации.

### Создание файла окружения

```bash
cp .env.example .env
```

### Параметры конфигурации

```env
# --- База данных ---
POSTGRES_USER=leafflow_user
POSTGRES_PASSWORD=strong_password_here
POSTGRES_DB=leafflow_db
DB_HOST=localhost
DB_PORT=5432

# --- Пул соединений ---
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=300

# --- JWT ---
JWT_SECRET=your-super-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_TTL_SECONDS=86400
REFRESH_TOKEN_TTL_SECONDS=1209600

# --- Telegram ---
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# --- Internal API ---
INTERNAL_BOT_TOKEN=internal-api-token
ADMIN_API_TOKEN=admin-api-token

# --- Медиа ---
IMAGES_DIR=static/images
IMAGES_BASE_URL=/images

# --- Уведомления ---
EXTERNAL_BOT_URL=https://your-notification-bot.com
EXTERNAL_BOT_TOKEN=notification-bot-token

# --- Redis ---
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Таблица параметров

| Параметр                   | Описание                           | По умолчанию | Обязателен |
|----------------------------|------------------------------------|--------------|------------|
| `POSTGRES_USER`            | Имя пользователя PostgreSQL        | –            | ✅          |
| `POSTGRES_PASSWORD`        | Пароль пользователя                | –            | ✅          |
| `POSTGRES_DB`              | Имя базы данных                    | –            | ✅          |
| `DB_HOST`                  | Хост базы данных                   | –            | ✅          |
| `DB_PORT`                  | Порт базы данных                   | –            | ✅          |
| `DB_POOL_SIZE`             | Размер пула соединений             | `10`         | ❌          |
| `DB_MAX_OVERFLOW`          | Макс. дополнительных соединений    | `20`         | ❌          |
| `JWT_SECRET`               | Секрет для подписи JWT             | –            | ✅          |
| `TELEGRAM_BOT_TOKEN`       | Токен Telegram бота                | –            | ✅          |
| `INTERNAL_BOT_TOKEN`       | Токен для internal API             | –            | ✅          |
| `ADMIN_API_TOKEN`          | Токен для admin API                | –            | ✅          |
| `REDIS_HOST`               | Хост Redis                         | –            | ✅          |
| `REDIS_PORT`               | Порт Redis                         | –            | ✅          |

> **Важно:** Для Docker Compose используйте `DB_HOST=db-leaf-flow` и `REDIS_HOST=leaf-flow-redis`.

---

## 🏃 Запуск

### Локальный запуск

1. Запустите PostgreSQL и Redis:

```bash
docker-compose up -d db-leaf-flow leaf-flow-redis
```

2. Примените миграции:

```bash
alembic upgrade head
```

3. Запустите приложение:

```bash
python -m leaf_flow
```

Приложение будет доступно по адресу: `http://localhost:8000`

### Запуск через Docker

Полный стек включает:
- **leaf-flow** — основное API-приложение
- **leaf-flow-bot** — Telegram бот
- **leaf-flow-nginx** — фронтенд Telegram Mini App + API proxy
- **leaf-flow-web-nginx** — фронтенд веб-сайта + API proxy
- **leaf-flow-redis** — очередь задач
- **leaf-flow-notifications-worker** — воркер уведомлений
- **db-leaf-flow** — PostgreSQL

```bash
docker-compose up -d
```

API будет доступно через nginx на порту `5025`.

---

## 🗄️ Работа с БД

### Миграции Alembic

Создать новую миграцию:

```bash
alembic revision --autogenerate -m "описание изменений"
```

Применить миграции:

```bash
alembic upgrade head
```

Откатить миграцию:

```bash
alembic downgrade -1
```

Посмотреть историю миграций:

```bash
alembic history
```

### 🔒 Деактивация продуктов и очистка корзин (на уровне PostgreSQL)

В проекте реализована автоматическая поддержка консистентности каталога и корзины на уровне базы данных:

- При переводе `products.is_active` из `true` в `false`:
  - все варианты товара (`product_variants`) деактивируются (`is_active=false`);
  - все позиции в корзинах (`cart_items`), связанные с этим товаром, удаляются.

- При переводе `product_variants.is_active` из `true` в `false`:
  - все позиции в корзинах (`cart_items`), связанные с этим вариантом, удаляются;
  - если после этого у товара не осталось активных вариантов — товар автоматически деактивируется.

Данная логика реализована через `AFTER UPDATE` триггеры PostgreSQL.

---

## 📚 API Documentation

После запуска приложения доступна интерактивная документация:

- **Swagger UI:** `http://localhost:8000/api/docs`
- **ReDoc:** `http://localhost:8000/api/redoc`

---

## 📁 Структура проекта

```
leaf-flow/
├── .env.example              # Шаблон переменных окружения
├── alembic.ini               # Конфигурация Alembic
├── docker-compose.yml        # Docker Compose (production)
├── docker-compose-stage.yml  # Docker Compose (staging)
├── Dockerfile                # Docker образ приложения
├── pyproject.toml            # Зависимости и метаданные проекта
│
├── migrations/               # Миграции базы данных
│   ├── env.py
│   ├── prod/                 # Production миграции
│   ├── stage/                # Staging миграции
│   └── versions/             # Основные миграции
│
├── nginx/                    # Конфигурация nginx
│   ├── nginx.conf            # Production конфиг
│   └── nginx_stage.conf      # Staging конфиг
│
├── docs/                     # Документация
│   └── swagger.yaml          # OpenAPI спецификация
│
└── src/leaf_flow/            # Исходный код приложения
    ├── __init__.py
    ├── __main__.py           # Точка входа
    ├── app.py                # Инициализация FastAPI
    ├── config.py             # Настройки приложения
    │
    ├── api/                  # API слой
    │   ├── deps.py           # Общие зависимости
    │   └── v1/
    │       ├── app/          # Основные endpoints
    │       │   ├── routers/
    │       │   │   ├── cart.py
    │       │   │   ├── catalog.py
    │       │   │   ├── orders.py
    │       │   │   └── reviews.py
    │       │   └── schemas/
    │       ├── auth/         # Аутентификация
    │       │   ├── routers/
    │       │   └── schemas/
    │       └── internal/     # Internal API
    │           ├── routers/
    │           └── schemas/
    │
    ├── domain/               # Доменный слой
    │   ├── entities/         # Локальные доменные сущности
    │   ├── mappers/          # Маппинг Model → Entity
    │   └── externals/        # Интерфейсы внешних сервисов
    │
    ├── infrastructure/       # Инфраструктурный слой
    │   ├── db/
    │   │   ├── session.py    # Настройка сессии БД
    │   │   ├── uow.py        # Unit of Work
    │   │   └── repositories/ # Репозитории
    │   └── externals/
    │       └── celery_client.py
    │
    └── services/             # Сервисный слой
        ├── auth_service.py
        ├── cart_service.py
        ├── catalog_service.py
        ├── media_service.py
        ├── order_service.py
        ├── review_service.py
        ├── security.py
        └── support_topic_service.py

# Shared пакет (отдельный репозиторий):
# https://github.com/Mist3s/leaf-flow-core
#
# leaf-flow-core/
# └── src/leaf_flow_core/
#     ├── models/           # SQLAlchemy модели (Product, Order, User, etc.)
#     ├── entities/         # Domain entities (dataclasses)
#     ├── enums/            # OrderStatus, DeliveryMethod, etc.
#     └── constants.py      # Общие константы
```

---

## 🧩 Модули и функциональность

### Модели данных

> Все модели определены в пакете [`leaf-flow-core`](https://github.com/Mist3s/leaf-flow-core).

| Модель                  | Описание                                        |
|-------------------------|-------------------------------------------------|
| `User`                  | Пользователь (Telegram/Email)                   |
| `RefreshToken`          | Refresh-токены для ротации                      |
| `Category`              | Категории товаров                               |
| `Product`               | Продукты с описанием, изображением, тегами      |
| `ProductVariant`        | Варианты продукта (вес, цена)                   |
| `ProductAttribute`      | Динамические атрибуты (вкус, эффект и т.д.)     |
| `ProductAttributeValue` | Значения атрибутов                              |
| `ProductBrewProfile`    | Профили заваривания (температура, время, посуда)|
| `Cart` / `CartItem`     | Корзина пользователя                            |
| `Order` / `OrderItem`   | Заказы и их позиции                             |
| `ExternalReview`        | Отзывы с внешних платформ                       |
| `SupportTopic`          | Темы поддержки                                  |

### Способы доставки

| Код       | Описание     |
|-----------|--------------|
| `pickup`  | Самовывоз    |
| `courier` | Курьер       |
| `cdek`    | СДЭК         |

### Статусы заказов

| Статус       | Описание              |
|--------------|-----------------------|
| `created`    | Создан                |
| `processing` | В обработке           |
| `paid`       | Оплачен               |
| `fulfilled`  | Выполнен              |
| `cancelled`  | Отменён               |

---

## 👨‍💻 Разработка

### Добавление нового endpoint

1. Создайте Pydantic-схемы в `api/v1/.../schemas/`
2. Создайте роутер в `api/v1/.../routers/`
3. Добавьте бизнес-логику в `services/`
4. Зарегистрируйте роутер в `app.py`:

```python
from leaf_flow.api.v1.app.routers.your_router import router as your_router

app.include_router(
    your_router,
    prefix="/v1/your-resource",
    tags=["your-tag"],
)
```

### Работа с моделями

> **Важно:** SQLAlchemy модели находятся в отдельном пакете [`leaf-flow-core`](https://github.com/Mist3s/leaf-flow-core).

**Добавление новой модели:**

1. Создайте модель в `leaf-flow-core/src/leaf_flow_core/models/`
2. Опубликуйте новую версию `leaf-flow-core`
3. Обновите зависимость в `leaf-flow`
4. Создайте репозиторий в `infrastructure/db/repositories/`
5. Добавьте репозиторий в `UoW` (`infrastructure/db/uow.py`)
6. Создайте миграцию:

```bash
alembic revision --autogenerate -m "add your_model table"
alembic upgrade head
```

**Использование моделей:**

```python
from leaf_flow_core.models import Product, Order, User
from leaf_flow_core.enums import OrderStatus, DeliveryMethod
```

### Добавление сервиса

1. Создайте файл в `services/`
2. Используйте `UoW` для работы с данными
3. Реализуйте бизнес-логику

```python
from leaf_flow.infrastructure.db.uow import UoW

async def your_service_function(data: SomeDTO, uow: UoW) -> ResultDTO:
    # Бизнес-логика
    entity = await uow.your_repo.get(id)
    # ...
    await uow.commit()
    return result
```

---

## 📝 Best Practices

- ✅ Всегда используйте `async/await` для I/O операций
- ✅ Работайте с БД через паттерн **Unit of Work**
- ✅ Используйте Pydantic-схемы для валидации входящих/исходящих данных
- ✅ Следуйте принципу разделения слоёв (API / Services / Infrastructure / Domain)
- ✅ Используйте маппинг между моделями БД и доменными сущностями
- ✅ Избегайте прямой работы с ORM из слоя API — используйте сервисы
- ✅ Для фоновых задач используйте Celery через `celery_client`
- ✅ Храните секреты в переменных окружения, не в коде

---

## 🤝 Contributing

Pull Request'ы приветствуются.

1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/my-feature`
3. Внесите изменения
4. Откройте Pull Request

---

## 📄 Лицензия

Проект является проприетарным программным обеспечением.
