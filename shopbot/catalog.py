"""Product catalog loaded from a JSON file."""

import json
from dataclasses import dataclass
from pathlib import Path

from .messages import DEFAULT_CATEGORY


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    price: int
    stock: int
    category: str = DEFAULT_CATEGORY

    @property
    def in_stock(self) -> bool:
        return self.stock > 0


class Catalog:
    def __init__(self, products: list[Product]) -> None:
        self._products = {product.id: product for product in products}

    @classmethod
    def from_file(cls, path: str | Path) -> "Catalog":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls([Product(**item) for item in data])

    def all(self) -> list[Product]:
        return list(self._products.values())

    def get(self, product_id: str) -> Product | None:
        return self._products.get(product_id)

    def categories(self) -> list[str]:
        """Category names in the order they first appear in the catalog."""
        return list(dict.fromkeys(product.category for product in self._products.values()))

    def by_category(self, category: str) -> list[Product]:
        wanted = category.strip().lower()
        return [product for product in self._products.values() if product.category.lower() == wanted]

    def search(self, text: str) -> list[Product]:
        """Return products whose name contains the text (case-insensitive)."""
        query = text.strip().lower()
        if not query:
            return []
        return [product for product in self._products.values() if query in product.name.lower()]
