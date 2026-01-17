import enum
from decimal import Decimal
from typing import List
from datetime import datetime

from sqlalchemy import (
    String, ForeignKey, UniqueConstraint, Boolean, DateTime,
    Numeric, Index, Text, Enum, CheckConstraint, Integer, func
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from leaf_flow.infrastructure.db.base import Base


class AttributeKind(str, enum.Enum):
    single = "single"
    multi = "multi"
    bool = "bool"
    range = "range"


class UIHint(str, enum.Enum):
    # single → radio; multi → chips; bool → toggle; range → scale
    chips = "chips"
    radio = "radio"
    toggle = "toggle"
    scale = "scale"


class Category(Base):
    __tablename__ = "categories"
    slug: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    label: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    products: Mapped[list["Product"]] = relationship(
        back_populates="category"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

class ProductType(Base):
    __tablename__ = "product_types"
    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    name: Mapped[str] = mapped_column(
        String(255), index=True
    )
    description: Mapped[str] = mapped_column(
        String(5000), nullable=False
    )
    category_slug: Mapped[str] = mapped_column(
        ForeignKey("categories.slug", ondelete="RESTRICT"), index=True
    )
    tags: Mapped[List[str]] = mapped_column(
        ARRAY(String(64)), default=[]
    )
    image: Mapped[str] = mapped_column(
        String(1024), nullable=False
    )
    product_type: Mapped[ProductType] = relationship()
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    category: Mapped[Category] = relationship(
        back_populates="products"
    )
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    product_type_code: Mapped[str] = mapped_column(
        ForeignKey("product_types.code", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    attribute_values: Mapped[list["ProductAttributeValue"]] = relationship(
        secondary="product_attribute_values",
        viewonly=True,
    )
    brew_profiles: Mapped[list["ProductBrewProfile"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    cart_items: Mapped[list["CartItem"]] = relationship(
        back_populates="product"
    )

    __table_args__ = (
        # GIN-индекс для быстрого поиска по массиву тегов
        Index("ix_products_tags_gin", "tags", postgresql_using="gin"),
        # Индекс для поиска по названию (lower для case-insensitive)
        Index("ix_products_name_lower", func.lower("name"))
    )


class ProductVariant(Base):
    __tablename__ = "product_variants"
    id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    weight: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    product: Mapped[Product] = relationship(
        back_populates="variants"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    cart_items: Mapped[list["CartItem"]] = relationship(
        back_populates="variant"
    )

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "weight",
            name="uq_product_variant_weight_per_product"
        ),
    )


class ProductAttributeValueLink(Base):
    __tablename__ = "product_attribute_values"

    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    attribute_value_id: Mapped[int] = mapped_column(
        ForeignKey("product_attributes_values.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    __table_args__ = (
        Index("idx_pavlink_value_product", "attribute_value_id", "product_id"),
        Index("idx_pavlink_product_value", "product_id", "attribute_value_id"),
    )


class ProductTypeAttribute(Base):
    __tablename__ = "product_type_attributes"

    product_type_code: Mapped[str] = mapped_column(
        ForeignKey("product_types.code", ondelete="CASCADE"),
        primary_key=True,
    )
    attribute_id: Mapped[int] = mapped_column(
        ForeignKey("product_attributes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    # опционально: max_select для multi (taste max3, effect max2)
    max_select: Mapped[int | None] = mapped_column(Integer)


class ProductAttribute(Base):
    __tablename__ = "product_attributes"
    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    kind: Mapped[AttributeKind] = mapped_column(
        Enum(AttributeKind, name="attribute_kind", native_enum=True),
        nullable=False
    )
    ui_hint: Mapped[UIHint] = mapped_column(
        Enum(UIHint, name="ui_hint", native_enum=True),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    values: Mapped[list["ProductAttributeValue"]] = relationship(
        back_populates="attribute", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            """
            ui_hint = CASE kind
              WHEN 'single' THEN 'radio'::ui_hint
              WHEN 'multi'  THEN 'chips'::ui_hint
              WHEN 'bool'   THEN 'toggle'::ui_hint
              WHEN 'range'  THEN 'scale'::ui_hint
            END
            """,
            name='ck_product_attributes_ck_product_attribute_kind_uihint_case',
        ),
        Index(
            "idx_product_attributes_active_sort",
            "sort_order",
            "id",
            postgresql_where=(is_active.is_(True))
        )
    )


class ProductAttributeValue(Base):
    __tablename__ = "product_attributes_values"
    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    attribute_id: Mapped[int] = mapped_column(
        ForeignKey("product_attributes.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    slug: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    attribute: Mapped[ProductAttribute] = relationship(
        back_populates="values"
    )
    synonyms: Mapped[list["ProductAttributeValueSynonym"]] = relationship(
        back_populates="attribute_value",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "attribute_id",
            "slug",
            name="uq_attribute_value_attribute_id_slug"
        ),
        Index(
            "idx_pav_attr_active_sort",
            "attribute_id",
            "sort_order",
            "id",
            postgresql_where=(is_active.is_(True))
        )
    )


class ProductAttributeValueSynonym(Base):
    __tablename__ = "product_attributes_values_synonyms"

    id: Mapped[int] = mapped_column(primary_key=True)
    attribute_value_id: Mapped[int] = mapped_column(
        ForeignKey("product_attributes_values.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    synonym: Mapped[str] = mapped_column(String(128), nullable=False)

    attribute_value: Mapped["ProductAttributeValue"] = relationship(
        back_populates="synonyms"
    )

    __table_args__ = (
        UniqueConstraint(
            "attribute_value_id",
            "synonym",
            name="uq_pav_synonym_value_id_synonym",
        ),
        Index(
            "idx_pav_synonym_synonym",
            "synonym"
        ),
    )


class ProductBrewProfile(Base):
    __tablename__ = "product_brew_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    method: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    teaware: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    temperature: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    brew_time: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    weight: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "product_id", "method", "teaware", "temperature", "brew_time",
            name="uq_product_brew_profile"
        ),
        Index(
            "idx_pbp_product_sort_active",
            "product_id", "sort_order", "id",
            postgresql_where=(is_active.is_(True))
        )
    )
