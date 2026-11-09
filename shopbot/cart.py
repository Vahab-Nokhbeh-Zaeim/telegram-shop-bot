"""Per-chat shopping carts."""

from collections import defaultdict

from .catalog import Catalog


def format_price(amount: int) -> str:
    return f"{amount:,} Toman"


class CartStore:
    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self._carts: dict[int, dict[str, int]] = defaultdict(dict)

    def add(self, chat_id: int, product_id: str, quantity: int = 1) -> bool:
        product = self.catalog.get(product_id)
        if product is None or quantity < 1:
            return False
        cart = self._carts[chat_id]
        new_quantity = cart.get(product_id, 0) + quantity
        if new_quantity > product.stock:
            return False
        cart[product_id] = new_quantity
        return True

    def remove(self, chat_id: int, product_id: str) -> bool:
        return self._carts[chat_id].pop(product_id, None) is not None

    def items(self, chat_id: int) -> list[tuple[str, int, int]]:
        """Return (name, quantity, line_total) for every item in the cart."""
        result = []
        for product_id, quantity in self._carts[chat_id].items():
            product = self.catalog.get(product_id)
            if product:
                result.append((product.name, quantity, product.price * quantity))
        return result

    def total(self, chat_id: int) -> int:
        return sum(line_total for _, _, line_total in self.items(chat_id))

    def is_empty(self, chat_id: int) -> bool:
        return not self._carts[chat_id]

    def clear(self, chat_id: int) -> None:
        self._carts.pop(chat_id, None)

    def summary(self, chat_id: int) -> str:
        lines = [f"• {name} × {qty} = {format_price(line)}" for name, qty, line in self.items(chat_id)]
        lines.append(f"\n<b>Total: {format_price(self.total(chat_id))}</b>")
        return "\n".join(lines)
