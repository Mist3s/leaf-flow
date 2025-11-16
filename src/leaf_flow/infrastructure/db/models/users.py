from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, BigInteger

from leaf_flow.infrastructure.db.base import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120), default=None)
    username: Mapped[str | None] = mapped_column(String(120), default=None)
    language_code: Mapped[str | None] = mapped_column(String(16), default=None)
    photo_url: Mapped[str | None] = mapped_column(String(1024), default=None)
    email: Mapped[str | None] = mapped_column(String(255), default=None)
