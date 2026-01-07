from datetime import datetime
from sqlalchemy import BigInteger, DateTime, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from leaf_flow.infrastructure.db.base import Base


class SupportTopic(Base):
    __tablename__ = "support_topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    admin_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    thread_id: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_telegram_id", name="uq_support_topics_user_telegram_id"),
        UniqueConstraint("admin_chat_id", "thread_id", name="uq_support_topics_admin_chat_id_thread_id"),
        Index("ix_support_topics_admin_chat_id_thread_id", "admin_chat_id", "thread_id"),
    )




