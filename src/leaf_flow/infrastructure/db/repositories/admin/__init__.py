"""Админские репозитории."""

from leaf_flow.infrastructure.db.repositories.admin.product import (
    AdminProductReaderRepository,
    AdminProductWriterRepository,
)
from leaf_flow.infrastructure.db.repositories.admin.variant import (
    AdminVariantReaderRepository,
    AdminVariantWriterRepository,
)
from leaf_flow.infrastructure.db.repositories.admin.brew_profile import (
    AdminBrewProfileReaderRepository,
    AdminBrewProfileWriterRepository,
)
from leaf_flow.infrastructure.db.repositories.admin.category import (
    AdminCategoryReaderRepository,
    AdminCategoryWriterRepository,
)
from leaf_flow.infrastructure.db.repositories.admin.order import (
    AdminOrderReaderRepository,
    AdminOrderWriterRepository,
)
from leaf_flow.infrastructure.db.repositories.admin.review import (
    AdminReviewReaderRepository,
    AdminReviewWriterRepository,
)
from leaf_flow.infrastructure.db.repositories.admin.user import (
    AdminUserReaderRepository,
    AdminUserWriterRepository,
)
from leaf_flow.infrastructure.db.repositories.admin.attribute import (
    AdminAttributeReaderRepository,
    AdminAttributeValueWriterRepository,
)

__all__ = [
    "AdminProductReaderRepository",
    "AdminProductWriterRepository",
    "AdminVariantReaderRepository",
    "AdminVariantWriterRepository",
    "AdminBrewProfileReaderRepository",
    "AdminBrewProfileWriterRepository",
    "AdminCategoryReaderRepository",
    "AdminCategoryWriterRepository",
    "AdminOrderReaderRepository",
    "AdminOrderWriterRepository",
    "AdminReviewReaderRepository",
    "AdminReviewWriterRepository",
    "AdminUserReaderRepository",
    "AdminUserWriterRepository",
    "AdminAttributeReaderRepository",
    "AdminAttributeValueWriterRepository",
]
