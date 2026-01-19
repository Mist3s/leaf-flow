from decimal import Decimal
from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, Numeric, DateTime, func, Index, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from leaf_flow.infrastructure.db.base import Base


class Cart(Base):
    __tablename__ = "carts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False
    )
    variant_id: Mapped[str] = mapped_column(
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=False
    )
    quantity: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    cart: Mapped[Cart] = relationship(back_populates="items")

    variant: Mapped["ProductVariant"] = relationship(
        back_populates="cart_items",
        foreign_keys=[variant_id],
    )

    product: Mapped["Product"] = relationship(
        back_populates="cart_items",
        foreign_keys=[product_id],
    )

    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", "variant_id", name="uq_cart_item_unique"),
        # Составной индекс для быстрого поиска товара в корзине
        Index("ix_cart_items_cart_product_variant", "cart_id", "product_id", "variant_id"),
        ForeignKeyConstraint(
            ["product_id", "variant_id"],
            ["product_variants.product_id", "product_variants.id"],
            name="fk_cart_items_product_variant_pair",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        Index("idx_cart_items_product_id", "product_id"),
        Index("idx_cart_items_variant_id", "variant_id"),
    )
