from typing import Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from leaf_flow.application.ports.admin.brew_profile import AdminBrewProfileReader, AdminBrewProfileWriter
from leaf_flow.domain.entities.product import BrewProfileEntity
from leaf_flow.infrastructure.db.mappers.admin.brew_profile import map_brew_profile_model_to_entity
from leaf_flow.infrastructure.db.models.product import ProductBrewProfile
from leaf_flow.infrastructure.db.repositories.base import Repository


class AdminBrewProfileReaderRepository(Repository[ProductBrewProfile], AdminBrewProfileReader):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductBrewProfile)

    async def get_by_id(self, profile_id: int) -> BrewProfileEntity | None:
        stmt = (
            select(ProductBrewProfile)
            .where(ProductBrewProfile.id == profile_id)
        )
        profile = (await self.session.execute(stmt)).scalar_one_or_none()

        if not profile:
            return None

        return map_brew_profile_model_to_entity(profile)

    async def list_by_product(self, product_id: str) -> Sequence[BrewProfileEntity]:
        stmt = (
            select(ProductBrewProfile)
            .where(ProductBrewProfile.product_id == product_id)
            .order_by(ProductBrewProfile.sort_order, ProductBrewProfile.id)
        )
        result = await self.session.execute(stmt)
        profiles = result.scalars().all()
        return [map_brew_profile_model_to_entity(p) for p in profiles]


class AdminBrewProfileWriterRepository(Repository[ProductBrewProfile], AdminBrewProfileWriter):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ProductBrewProfile)

    async def create(
        self,
        product_id: str,
        method: str,
        teaware: str,
        temperature: str,
        brew_time: str,
        weight: str,
        note: str | None,
        sort_order: int,
        is_active: bool,
    ) -> BrewProfileEntity:
        profile = ProductBrewProfile(
            product_id=product_id,
            method=method,
            teaware=teaware,
            temperature=temperature,
            brew_time=brew_time,
            weight=weight,
            note=note,
            sort_order=sort_order,
            is_active=is_active,
        )
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return map_brew_profile_model_to_entity(profile)

    async def update(
        self,
        profile_id: int,
        **fields: object
    ) -> BrewProfileEntity | None:
        allowed = set(ProductBrewProfile.__table__.columns.keys())
        values = {k: v for k, v in fields.items() if k in allowed}

        if not values:
            return None

        stmt = (
            update(ProductBrewProfile)
            .where(ProductBrewProfile.id == profile_id)
            .values(**values)
            .returning(ProductBrewProfile)
        )
        profile = (await self.session.execute(stmt)).scalar_one_or_none()
        await self.session.flush()

        if profile is None:
            return None

        return map_brew_profile_model_to_entity(profile)

    async def delete(self, profile_id: int) -> None:
        stmt = delete(ProductBrewProfile).where(ProductBrewProfile.id == profile_id)
        await self.session.execute(stmt)
        await self.session.flush()
