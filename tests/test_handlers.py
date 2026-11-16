import unittest

from shopbot.catalog import Catalog, Product
from shopbot.handlers import ShopBot
from shopbot.messages import t


def text_update(chat_id: int, text: str) -> dict:
    return {"message": {"chat": {"id": chat_id}, "from": {"first_name": "سارا", "username": "sara"}, "text": text}}


def add_update(chat_id: int, product_id: str) -> dict:
    return {"callback_query": {"id": "q1", "data": f"add:{product_id}", "message": {"chat": {"id": chat_id}}}}


class ShopBotTests(unittest.TestCase):
    def setUp(self) -> None:
        catalog = Catalog([Product("mouse", "Mouse", 100, 5), Product("cam", "Webcam", 500, 0)])
        self.bot = ShopBot(catalog, admin_chat_id=999)

    def reply(self, text: str) -> str:
        return self.bot.handle(text_update(1, text))[0].params["text"]

    def test_start_greets_user_in_persian(self) -> None:
        text = self.reply("/start")
        self.assertIn("سلام سارا", text)
        self.assertIn("/categories", text)

    def test_start_escapes_html_in_names(self) -> None:
        update = {"message": {"chat": {"id": 1}, "from": {"first_name": "<b>x</b>"}, "text": "/start"}}
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", self.bot.handle(update)[0].params["text"])

    def test_catalog_only_offers_products_in_stock(self) -> None:
        action = self.bot.handle(text_update(1, "/catalog"))[0]
        buttons = action.params["reply_markup"]["inline_keyboard"]
        self.assertEqual([row[0]["callback_data"] for row in buttons], ["add:mouse"])
        self.assertEqual(buttons[0][0]["text"], t("add_button", name="Mouse"))
        self.assertIn(t("out_of_stock"), action.params["text"])

    def test_catalog_groups_products_by_category(self) -> None:
        catalog = Catalog([
            Product("mouse", "Mouse", 100, 5, "Accessories"),
            Product("speaker", "Speaker", 300, 2, "Audio"),
            Product("pad", "Mouse Pad", 20, 3, "Accessories"),
        ])
        text = ShopBot(catalog).handle(text_update(1, "/catalog"))[0].params["text"]
        self.assertLess(text.index("<b>Accessories</b>"), text.index("Mouse Pad"))
        self.assertLess(text.index("Mouse Pad"), text.index("<b>Audio</b>"))

    def test_add_button_puts_product_in_cart(self) -> None:
        answer = self.bot.handle(add_update(1, "mouse"))[0]
        self.assertEqual(answer.method, "answer_callback")
        self.assertEqual(answer.params["text"], t("added", name="Mouse"))
        self.assertIn("Mouse × ۱", self.reply("/cart"))

    def test_unavailable_product_button(self) -> None:
        answer = self.bot.handle(add_update(1, "cam"))[0]
        self.assertEqual(answer.params["text"], t("unavailable"))

    def test_checkout_notifies_admin_and_clears_cart(self) -> None:
        self.bot.handle(add_update(1, "mouse"))
        actions = self.bot.handle(text_update(1, "/checkout"))
        self.assertEqual(len(actions), 2)
        self.assertIn("سفارش شماره ۱۰۰۱ ثبت شد", actions[0].params["text"])
        self.assertEqual(actions[1].params["chat_id"], 999)
        self.assertIn("@sara", actions[1].params["text"])
        self.assertEqual(self.reply("/cart"), t("cart_empty"))

    def test_checkout_with_empty_cart(self) -> None:
        actions = self.bot.handle(text_update(1, "/checkout"))
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].params["text"], t("checkout_empty"))

    def test_command_with_bot_mention(self) -> None:
        self.assertIn("خوش آمدی", self.reply("/start@my_shop_bot"))

    def test_search_finds_products_case_insensitively(self) -> None:
        action = self.bot.handle(text_update(1, "/search MOU"))[0]
        self.assertIn("Mouse", action.params["text"])
        buttons = action.params["reply_markup"]["inline_keyboard"]
        self.assertEqual(buttons[0][0]["callback_data"], "add:mouse")

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

    def test_search_works_with_persian_names(self) -> None:
        catalog = Catalog([Product("mouse", "ماوس بی‌سیم", 100, 2), Product("kb", "کیبورد", 300, 1)])
        text = ShopBot(catalog).handle(text_update(1, "/search ماوس"))[0].params["text"]
        self.assertIn("ماوس بی‌سیم", text)
        self.assertNotIn("کیبورد", text)

    def test_search_result_button_adds_to_cart(self) -> None:
        action = self.bot.handle(text_update(1, "/search mouse"))[0]
        product_id = action.params["reply_markup"]["inline_keyboard"][0][0]["callback_data"].removeprefix("add:")
        self.bot.handle(add_update(1, product_id))
        self.assertIn("Mouse × ۱", self.reply("/cart"))

    def test_search_shows_out_of_stock_without_button(self) -> None:
        action = self.bot.handle(text_update(1, "/search webcam"))[0]
        self.assertIn(t("out_of_stock"), action.params["text"])
        self.assertNotIn("reply_markup", action.params)

    def test_search_without_query_shows_usage(self) -> None:
        self.assertEqual(self.reply("/search"), t("search_usage"))

    def test_search_with_no_results(self) -> None:
        text = self.reply("/search <laptop>")
        self.assertIn("پیدا نشد", text)
        self.assertIn("&lt;laptop&gt;", text)

    def test_categories_shows_a_button_per_category(self) -> None:
        catalog = Catalog([
            Product("mouse", "Mouse", 100, 5, "Accessories"),
            Product("pad", "Mouse Pad", 20, 3, "Accessories"),
            Product("speaker", "Speaker", 300, 2, "Audio"),
        ])
        action = ShopBot(catalog).handle(text_update(1, "/categories"))[0]
        buttons = [row[0] for row in action.params["reply_markup"]["inline_keyboard"]]
        self.assertEqual([b["text"] for b in buttons], ["Accessories (۲)", "Audio (۱)"])
        self.assertEqual([b["callback_data"] for b in buttons], ["cat:0", "cat:1"])

    def test_category_button_lists_its_products(self) -> None:
        catalog = Catalog([
            Product("mouse", "Mouse", 100, 5, "Accessories"),
            Product("speaker", "Speaker", 300, 2, "Audio"),
        ])
        update = {"callback_query": {"id": "q2", "data": "cat:1", "message": {"chat": {"id": 1}}}}
        answer, products = ShopBot(catalog).handle(update)
        self.assertEqual(answer.method, "answer_callback")
        self.assertIn("Speaker", products.params["text"])
        self.assertNotIn("Mouse", products.params["text"])
        self.assertEqual(products.params["reply_markup"]["inline_keyboard"][0][0]["callback_data"], "add:speaker")

    def test_invalid_category_button(self) -> None:
        update = {"callback_query": {"id": "q3", "data": "cat:99", "message": {"chat": {"id": 1}}}}
        actions = self.bot.handle(update)
        self.assertEqual(actions[1].params["text"], t("category_missing"))

    def test_categories_with_empty_catalog(self) -> None:
        action = ShopBot(Catalog([])).handle(text_update(1, "/categories"))[0]
        self.assertEqual(action.params["text"], t("categories_empty"))

    def test_unknown_command(self) -> None:
        self.assertEqual(self.reply("hello"), t("unknown"))


if __name__ == "__main__":
    unittest.main()
