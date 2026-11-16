"""Turns Telegram updates into bot actions.

Handlers return a list of actions instead of calling the API directly,
which keeps the business logic independent from the network and easy to test.
"""

import html
from dataclasses import dataclass, field
from itertools import count

from .cart import CartStore
from .catalog import Catalog
from .messages import fa_number, format_price, t


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
            "/categories": self._categories,
        }
        handler = routes.get(command, self._unknown)
        return handler(chat_id, msg)

    def _start(self, chat_id: int, msg: dict) -> list[Action]:
        name = msg.get("from", {}).get("first_name") or t("default_name")
        return [message(chat_id, t("start", name=html.escape(name)))]

    def _catalog(self, chat_id: int, msg: dict) -> list[Action]:
        keyboard = []
        lines = [f"<b>{t('catalog_title')}</b>"]
        for category in self.catalog.categories():
            lines.append(f"\n<b>{html.escape(category)}</b>")
            for product in self.catalog.by_category(category):
                lines.append(self._product_line(product))
                if product.in_stock:
                    keyboard.append([self._add_button(product)])
        return [message(chat_id, "\n".join(lines), keyboard)]

    def _search(self, chat_id: int, msg: dict) -> list[Action]:
        parts = (msg.get("text") or "").split(maxsplit=1)
        if len(parts) < 2:
            return [message(chat_id, t("search_usage"))]
        query = html.escape(parts[1])
        results = self.catalog.search(parts[1])
        if not results:
            return [message(chat_id, t("search_none", query=query))]
        return [self._product_list(chat_id, t("search_title", query=query), results)]

    def _categories(self, chat_id: int, msg: dict) -> list[Action]:
        categories = self.catalog.categories()
        if not categories:
            return [message(chat_id, t("categories_empty"))]
        # Buttons carry the category index: callback data is limited to 64 bytes.
        keyboard = [
            [{
                "text": t("category_button", name=name, count=fa_number(len(self.catalog.by_category(name)))),
                "callback_data": f"cat:{index}",
            }]
            for index, name in enumerate(categories)
        ]
        return [message(chat_id, f"<b>{t('categories_title')}</b>", keyboard)]

    def _product_list(self, chat_id: int, title: str, products: list) -> Action:
        lines = [f"<b>{title}</b>"]
        keyboard = []
        for product in products:
            lines.append(self._product_line(product))
            if product.in_stock:
                keyboard.append([self._add_button(product)])
        return message(chat_id, "\n".join(lines), keyboard)

    @staticmethod
    def _product_line(product) -> str:
        status = format_price(product.price) if product.in_stock else t("out_of_stock")
        return t("product_line", name=product.name, status=status)

    @staticmethod
    def _add_button(product) -> dict:
        return {"text": t("add_button", name=product.name), "callback_data": f"add:{product.id}"}

    def _cart(self, chat_id: int, msg: dict) -> list[Action]:
        if self.carts.is_empty(chat_id):
            return [message(chat_id, t("cart_empty"))]
        return [message(chat_id, f"<b>{t('cart_title')}</b>\n" + self.carts.summary(chat_id))]

    def _checkout(self, chat_id: int, msg: dict) -> list[Action]:
        if self.carts.is_empty(chat_id):
            return [message(chat_id, t("checkout_empty"))]
        order_id = fa_number(next(self._order_ids))
        summary = self.carts.summary(chat_id)
        actions = [message(chat_id, t("order_placed", order_id=order_id, summary=summary))]
        if self.admin_chat_id is not None:
            username = msg.get("from", {}).get("username")
            customer = f"@{username}" if username else fa_number(chat_id)
            actions.append(message(self.admin_chat_id, t("admin_new_order", order_id=order_id, customer=customer, summary=summary)))
        self.carts.clear(chat_id)
        return actions

    def _clear(self, chat_id: int, msg: dict) -> list[Action]:
        self.carts.clear(chat_id)
        return [message(chat_id, t("cleared"))]

    def _unknown(self, chat_id: int, msg: dict) -> list[Action]:
        return [message(chat_id, t("unknown"))]

    def _handle_callback(self, query: dict) -> list[Action]:
        chat_id = query.get("message", {}).get("chat", {}).get("id")
        data = query.get("data", "")
        answer = Action("answer_callback", {"callback_id": query.get("id", "")})
        if chat_id is not None and data.startswith("cat:"):
            return [answer, *self._show_category(chat_id, data.removeprefix("cat:"))]
        if chat_id is None or not data.startswith("add:"):
            return [answer]
        product = self.catalog.get(data.removeprefix("add:"))
        if product and self.carts.add(chat_id, product.id):
            answer.params["text"] = t("added", name=product.name)
        else:
            answer.params["text"] = t("unavailable")
        return [answer]

    def _show_category(self, chat_id: int, index_text: str) -> list[Action]:
        categories = self.catalog.categories()
        if not index_text.isdigit() or int(index_text) >= len(categories):
            return [message(chat_id, t("category_missing"))]
        name = categories[int(index_text)]
        return [self._product_list(chat_id, html.escape(name), self.catalog.by_category(name))]
