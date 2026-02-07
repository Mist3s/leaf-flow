from dataclasses import dataclass


@dataclass(slots=True)
class CategoryEntity:
    slug: str
    label: str
    sort_order: int = 0