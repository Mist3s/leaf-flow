from enum import Enum as PyEnum

from sqlalchemy import Integer, String, Numeric, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from leaf_flow.infrastructure.db.base import Base


class PlatformEnum(str, PyEnum):
    yandex = 'yandex'
    google = 'google'
    telegram = 'telegram'
    avito = 'avito'


class ExternalReview(Base):
    __tablename__ = 'external_reviews'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[PlatformEnum] = mapped_column(
        SAEnum(PlatformEnum, name='platform')
    )
    author: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[float] = mapped_column(Numeric, nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
