from typing import Protocol, Sequence

from leaf_flow.domain.entities.product import (
    ProductAttributesEntity,
    ProductAttributesValueEntity
)


class AdminAttributeReader(Protocol):
    async def get_by_id(self, attribute_id: int) -> ProductAttributesEntity | None: ...

    async def list_all(self) -> Sequence[ProductAttributesEntity]: ...

    async def get_values_by_attribute(
        self, attribute_id: int
    ) -> Sequence[ProductAttributesValueEntity]: ...


class AdminAttributeValueWriter(Protocol):
    async def add_to_product(
        self,
        product_id: str,
        attribute_value_id: int,
    ) -> bool: ...

    async def remove_from_product(
        self,
        product_id: str,
        attribute_value_id: int,
    ) -> bool: ...

    async def set_product_values(
        self,
        product_id: str,
        attribute_value_ids: list[int],
    ) -> bool: ...
