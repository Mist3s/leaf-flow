from leaf_flow.domain.entities.category import CategoryEntity
from leaf_flow.infrastructure.db.models import Category as CategoryModel


def map_product_category_model_to_entity(
        category: CategoryModel
) -> CategoryEntity:
    return CategoryEntity(
        slug=category.slug,
        label=category.label
    )
