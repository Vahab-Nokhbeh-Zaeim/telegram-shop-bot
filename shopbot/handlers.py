"""Turns Telegram updates into bot actions.

Handlers return a list of actions instead of calling the API directly,
which keeps the business logic independent from the network and easy to test.
"""

import html
from dataclasses import dataclass, field
from itertools import count

from .cart import CartStore, format_price
from .catalog import Catalog


@dataclass
class Action:
    method: str
    params: dict = field(default_factory=dict)


def message(chat_id: int, text: str, keyboard: list | None = None) -> Action:
    params: dict = {"chat_id": chat_id, "text": text}
    if keyboard:
        params["reply_markup"] = {"inline_keyboard": keyboard}
    return Action("send_message", params)


class ShopBot:
    def __init__(self, catalog: Catalog, admin_chat_id: int | None = None) -> None:
        self.catalog = catalog
        self.carts = CartStore(catalog)
        self.admin_chat_id = admin_chat_id
        self._order_ids = count(1001)

    def handle(self, update: dict) -> list[Action]:
        if "callback_query" in update:
            return self._handle_callback(update["callback_query"])
        msg = update.get("message") or {}
        text = (msg.get("text") or "").strip()
        chat_id = msg.get("chat", {}).get("id")
        if chat_id is None:
            return []
        command = text.split()[0].split("@")[0].lower() if text else ""
        routes = {
            "/start": self._start,
            "/catalog": self._catalog,
            "/cart": self._cart,
            "/checkout": self._checkout,
            "/clear": self._clear,
            "/search": self._search,
        }
        handler = routes.get(command, self._unknown)
        return handler(chat_id, msg)

    def _start(self, chat_id: int, msg: dict) -> list[Action]:
        name = msg.get("from", {}).get("first_name", "there")
        text = (
            f"Hi {name}! 👋 Welcome to the shop.\n\n"
            "/catalog – browse products\n"
            "/search &lt;name&gt; – find a product\n"
            "/cart – view your cart\n"
            "/checkout – place your order\n"
            "/clear – empty your cart"
        )
        return [message(chat_id, text)]

    def _catalog(self, chat_id: int, msg: dict) -> list[Action]:
        keyboard = []
        lines = ["<b>Products</b>"]
        for product in self.catalog.all():
            status = format_price(product.price) if product.in_stock else "out of stock"
            lines.append(f"• {product.name} – {status}")
            if product.in_stock:
                keyboard.append([{"text": f"Add {product.name}", "callback_data": f"add:{product.id}"}])
        return [message(chat_id, "\n".join(lines), keyboard)]

    def _search(self, chat_id: int, msg: dict) -> list[Action]:
        parts = (msg.get("text") or "").split(maxsplit=1)
        if len(parts) < 2:
            return [message(chat_id, "Usage: /search mouse")]
        query = html.escape(parts[1])
        results = self.catalog.search(parts[1])
        if not results:
            return [message(chat_id, f"No products found for “{query}”.")]
        lines = [f"<b>Results for “{query}”</b>"]
        keyboard = []
        for product in results:
            status = format_price(product.price) if product.in_stock else "out of stock"
            lines.append(f"• {product.name} – {status}")
            if product.in_stock:
                keyboard.append([{"text": f"Add {product.name}", "callback_data": f"add:{product.id}"}])
        return [message(chat_id, "\n".join(lines), keyboard)]

    def _cart(self, chat_id: int, msg: dict) -> list[Action]:
        if self.carts.is_empty(chat_id):
            return [message(chat_id, "Your cart is empty. Use /catalog to add products.")]
        return [message(chat_id, "<b>Your cart</b>\n" + self.carts.summary(chat_id))]

    def _checkout(self, chat_id: int, msg: dict) -> list[Action]:
        if self.carts.is_empty(chat_id):
            return [message(chat_id, "Your cart is empty.")]
        order_id = next(self._order_ids)
        summary = self.carts.summary(chat_id)
        actions = [message(chat_id, f"✅ Order #{order_id} placed!\n\n{summary}\n\nWe will contact you soon.")]
        if self.admin_chat_id is not None:
            customer = msg.get("from", {}).get("username") or chat_id
            actions.append(message(self.admin_chat_id, f"🛒 New order #{order_id} from {customer}\n\n{summary}"))
        self.carts.clear(chat_id)
        return actions

    def _clear(self, chat_id: int, msg: dict) -> list[Action]:
        self.carts.clear(chat_id)
        return [message(chat_id, "Your cart has been emptied.")]

    def _unknown(self, chat_id: int, msg: dict) -> list[Action]:
        return [message(chat_id, "Sorry, I did not understand that. Send /start to see the commands.")]

    def _handle_callback(self, query: dict) -> list[Action]:
        chat_id = query.get("message", {}).get("chat", {}).get("id")
        data = query.get("data", "")
        answer = Action("answer_callback", {"callback_id": query.get("id", "")})
        if chat_id is None or not data.startswith("add:"):
            return [answer]
        product = self.catalog.get(data.removeprefix("add:"))
        if product and self.carts.add(chat_id, product.id):
            answer.params["text"] = f"{product.name} added to your cart"
        else:
            answer.params["text"] = "Sorry, this product is not available"
        return [answer]
