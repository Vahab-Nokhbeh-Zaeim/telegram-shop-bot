import unittest

from shopbot.catalog import Catalog, Product
from shopbot.handlers import ShopBot


def text_update(chat_id: int, text: str) -> dict:
    return {"message": {"chat": {"id": chat_id}, "from": {"first_name": "Sara", "username": "sara"}, "text": text}}


def add_update(chat_id: int, product_id: str) -> dict:
    return {"callback_query": {"id": "q1", "data": f"add:{product_id}", "message": {"chat": {"id": chat_id}}}}


class ShopBotTests(unittest.TestCase):
    def setUp(self) -> None:
        catalog = Catalog([Product("mouse", "Mouse", 100, 5), Product("cam", "Webcam", 500, 0)])
        self.bot = ShopBot(catalog, admin_chat_id=999)

    def test_start_greets_user(self) -> None:
        actions = self.bot.handle(text_update(1, "/start"))
        self.assertIn("Hi Sara", actions[0].params["text"])

    def test_catalog_only_offers_products_in_stock(self) -> None:
        action = self.bot.handle(text_update(1, "/catalog"))[0]
        buttons = action.params["reply_markup"]["inline_keyboard"]
        self.assertEqual([row[0]["callback_data"] for row in buttons], ["add:mouse"])

    def test_add_button_puts_product_in_cart(self) -> None:
        answer = self.bot.handle(add_update(1, "mouse"))[0]
        self.assertEqual(answer.method, "answer_callback")
        self.assertIn("added", answer.params["text"])
        cart = self.bot.handle(text_update(1, "/cart"))[0]
        self.assertIn("Mouse × 1", cart.params["text"])

    def test_checkout_notifies_admin_and_clears_cart(self) -> None:
        self.bot.handle(add_update(1, "mouse"))
        actions = self.bot.handle(text_update(1, "/checkout"))
        self.assertEqual(len(actions), 2)
        self.assertIn("Order #1001", actions[0].params["text"])
        self.assertEqual(actions[1].params["chat_id"], 999)
        self.assertIn("empty", self.bot.handle(text_update(1, "/cart"))[0].params["text"])

    def test_checkout_with_empty_cart(self) -> None:
        actions = self.bot.handle(text_update(1, "/checkout"))
        self.assertEqual(len(actions), 1)
        self.assertIn("empty", actions[0].params["text"])

    def test_command_with_bot_mention(self) -> None:
        actions = self.bot.handle(text_update(1, "/start@my_shop_bot"))
        self.assertIn("Welcome", actions[0].params["text"])

    def test_unknown_command(self) -> None:
        actions = self.bot.handle(text_update(1, "hello"))
        self.assertIn("did not understand", actions[0].params["text"])


if __name__ == "__main__":
    unittest.main()
