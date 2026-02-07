from leaf_flow.domain.entities.product import BrewProfileEntity
from leaf_flow.infrastructure.db.models.product import ProductBrewProfile


def map_brew_profile_model_to_entity(p: ProductBrewProfile) -> BrewProfileEntity:
    return BrewProfileEntity(
        id=p.id,
        method=p.method,
        teaware=p.teaware,
        temperature=p.temperature,
        brew_time=p.brew_time,
        weight=p.weight,
        note=p.note,
        sort_order=p.sort_order,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )