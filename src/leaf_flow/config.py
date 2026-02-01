from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # --- База данных ---
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DB_HOST: str
    DB_PORT: int
    # --- Настройки пула соединений ---
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 300

    # --- Безопасность / JWT ---
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_TTL_SECONDS: int = 60 * 60 * 24
    REFRESH_TOKEN_TTL_SECONDS: int = 60 * 60 * 24 * 14

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str
    # --- Internal integrations ---
    INTERNAL_BOT_TOKEN: str
    # --- Admin API ---
    ADMIN_API_TOKEN: str
    IMAGES_DIR: str = "static/images"
    IMAGES_BASE_URL: str = "/images"
    # --- External BOT for notifications ---
    EXTERNAL_BOT_URL: str
    EXTERNAL_BOT_TOKEN: str
    # --- Redis ---
    REDIS_HOST: str
    REDIS_PORT: int

    # --- Outbox Processor ---
    OUTBOX_POLL_INTERVAL: float = 1.0
    OUTBOX_BATCH_SIZE: int = 100
    OUTBOX_MAX_ATTEMPTS: int = 5
    OUTBOX_LOG_LEVEL: str = "INFO"

    # --- S3 ---
    S3_ENDPOINT: str
    S3_BUCKET: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_REGION: str
    S3_USE_SSL: bool
    PUBLIC_IMAGE_BASE_URL: str
    PUBLIC_IMAGE_PREFIX: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        # просто меняем asyncpg на psycopg2
        return self.database_url.replace('+asyncpg', '+psycopg2')

    model_config = ConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
