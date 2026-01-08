from decimal import Decimal
from typing import List

from sqlalchemy import String, ForeignKey, UniqueConstraint, Numeric, Index
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from leaf_flow.infrastructure.db.base import Base


class Category(Base):
    __tablename__ = "categories"
    # slug используется в API и как внешний ключ у продуктов
    slug: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(255))
    # backref
    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(String(5000))
    category_slug: Mapped[str] = mapped_column(ForeignKey("categories.slug", ondelete="RESTRICT"), index=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String(64)), default=[])
    image: Mapped[str] = mapped_column(String(1024))

    category: Mapped[Category] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        # GIN-индекс для быстрого поиска по массиву тегов
        Index("ix_products_tags_gin", "tags", postgresql_using="gin"),
        # Индекс для поиска по названию (lower для case-insensitive)
        Index("ix_products_name_lower", "name", postgresql_ops={"name": "varchar_pattern_ops"}),
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    weight: Mapped[str] = mapped_column(String(64))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    product: Mapped[Product] = relationship(back_populates="variants")

    __table_args__ = (
        UniqueConstraint("product_id", "weight", name="uq_product_variant_weight_per_product"),
    )


