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

    def test_search_finds_products_case_insensitively(self) -> None:
        action = self.bot.handle(text_update(1, "/search MOU"))[0]
        self.assertIn("Mouse", action.params["text"])
        buttons = action.params["reply_markup"]["inline_keyboard"]
        self.assertEqual(buttons[0][0]["callback_data"], "add:mouse")

    def test_search_shows_out_of_stock_without_button(self) -> None:
        action = self.bot.handle(text_update(1, "/search webcam"))[0]
        self.assertIn("out of stock", action.params["text"])
        self.assertNotIn("reply_markup", action.params)

    def test_search_lists_every_matching_product(self) -> None:
        catalog = Catalog([
            Product("mouse", "Wireless Mouse", 100, 2),
            Product("pad", "Mouse Pad", 20, 4),
            Product("cam", "Webcam", 500, 1),
        ])
        action = ShopBot(catalog).handle(text_update(1, "/search mouse"))[0]
        self.assertIn("Wireless Mouse", action.params["text"])
        self.assertIn("Mouse Pad", action.params["text"])
        self.assertNotIn("Webcam", action.params["text"])
        self.assertEqual(len(action.params["reply_markup"]["inline_keyboard"]), 2)

    def test_search_keeps_multi_word_queries(self) -> None:
        catalog = Catalog([Product("pad", "Mouse Pad", 20, 4), Product("mouse", "Mouse", 100, 2)])
        action = ShopBot(catalog).handle(text_update(1, "/search   mouse pad  "))[0]
        self.assertIn("Mouse Pad", action.params["text"])
        self.assertEqual(len(action.params["reply_markup"]["inline_keyboard"]), 1)

    def test_search_result_button_adds_to_cart(self) -> None:
        action = self.bot.handle(text_update(1, "/search mouse"))[0]
        product_id = action.params["reply_markup"]["inline_keyboard"][0][0]["callback_data"].removeprefix("add:")
        self.bot.handle(add_update(1, product_id))
        cart = self.bot.handle(text_update(1, "/cart"))[0]
        self.assertIn("Mouse × 1", cart.params["text"])

    def test_search_without_query_shows_usage(self) -> None:
        action = self.bot.handle(text_update(1, "/search"))[0]
        self.assertIn("Usage", action.params["text"])

    def test_search_with_no_results(self) -> None:
        action = self.bot.handle(text_update(1, "/search <laptop>"))[0]
        self.assertIn("No products found", action.params["text"])
        self.assertIn("&lt;laptop&gt;", action.params["text"])

    def test_unknown_command(self) -> None:
        actions = self.bot.handle(text_update(1, "hello"))
        self.assertIn("did not understand", actions[0].params["text"])


if __name__ == "__main__":
    unittest.main()
