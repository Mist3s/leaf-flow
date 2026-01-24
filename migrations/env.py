from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

from leaf_flow.config import settings
from leaf_flow.infrastructure.db.base import Base
# Важно: импортируем модели, чтобы они зарегистрировались в Base.metadata
from leaf_flow.infrastructure.db.models.user import User  # noqa: F401
from leaf_flow.infrastructure.db.models.token import RefreshToken  # noqa: F401
from leaf_flow.infrastructure.db.models.product import Product, Category, ProductVariant  # noqa: F401
from leaf_flow.infrastructure.db.models.order import Order, OrderStatusEnum, DeliveryMethodEnum, OrderItem  # noqa: F401
from leaf_flow.infrastructure.db.models.cart import Cart, CartItem  # noqa: F401
from leaf_flow.infrastructure.db.models.review import ExternalReview, PlatformEnum  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.sync_database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
