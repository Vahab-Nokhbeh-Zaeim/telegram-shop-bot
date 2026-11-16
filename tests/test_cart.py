import unittest
from pathlib import Path

from shopbot.cart import CartStore
from shopbot.catalog import Catalog, Product
from shopbot.messages import DEFAULT_CATEGORY, TEXT, fa_number, format_price, t


def make_catalog() -> Catalog:
    return Catalog([
        Product("mouse", "Mouse", 100, 3),
        Product("cam", "Webcam", 500, 0),
    ])


class CartTests(unittest.TestCase):
    def setUp(self) -> None:
        self.carts = CartStore(make_catalog())

    def test_add_and_total(self) -> None:
        self.assertTrue(self.carts.add(1, "mouse", 2))
        self.assertEqual(self.carts.total(1), 200)

    def test_cannot_exceed_stock(self) -> None:
        self.assertTrue(self.carts.add(1, "mouse", 3))
        self.assertFalse(self.carts.add(1, "mouse"))

    def test_out_of_stock_and_unknown_products(self) -> None:
        self.assertFalse(self.carts.add(1, "cam"))
        self.assertFalse(self.carts.add(1, "missing"))
        self.assertTrue(self.carts.is_empty(1))

    def test_carts_are_separate_per_chat(self) -> None:
        self.carts.add(1, "mouse")
        self.assertTrue(self.carts.is_empty(2))

    def test_remove_and_clear(self) -> None:
        self.carts.add(1, "mouse")
        self.assertTrue(self.carts.remove(1, "mouse"))
        self.assertFalse(self.carts.remove(1, "mouse"))
        self.carts.add(1, "mouse")
        self.carts.clear(1)
        self.assertTrue(self.carts.is_empty(1))

    def test_summary_is_in_persian(self) -> None:
        self.carts.add(1, "mouse", 2)
        summary = self.carts.summary(1)
        self.assertIn("Mouse × ۲ = ۲۰۰ تومان", summary)
        self.assertIn("جمع کل: ۲۰۰ تومان", summary)

    def test_catalog_search(self) -> None:
        catalog = make_catalog()
        self.assertEqual([p.id for p in catalog.search("MOUSE")], ["mouse"])
        self.assertEqual(catalog.search("  "), [])
        self.assertEqual(catalog.search("keyboard"), [])

    def test_categories_keep_first_seen_order(self) -> None:
        catalog = Catalog([
            Product("a", "A", 1, 1, "Audio"),
            Product("b", "B", 1, 1, "Accessories"),
            Product("c", "C", 1, 1, "Audio"),
        ])
        self.assertEqual(catalog.categories(), ["Audio", "Accessories"])
        self.assertEqual([p.id for p in catalog.by_category("audio")], ["a", "c"])

    def test_product_without_category_uses_default(self) -> None:
        self.assertEqual(Product("x", "X", 1, 1).category, DEFAULT_CATEGORY)

    def test_sample_catalog_file_loads_with_persian_names(self) -> None:
        catalog = Catalog.from_file(Path(__file__).resolve().parent.parent / "data" / "products.json")
        self.assertIn("لوازم جانبی", catalog.categories())
        self.assertEqual([p.id for p in catalog.search("ماوس")], ["mouse"])


class MessageTests(unittest.TestCase):
    def test_format_price_uses_persian_digits_and_separator(self) -> None:
        self.assertEqual(format_price(1250000), "۱٬۲۵۰٬۰۰۰ تومان")

    def test_fa_number(self) -> None:
        self.assertEqual(fa_number(1001), "۱۰۰۱")

    def test_every_template_can_be_filled(self) -> None:
        values = {"name": "x", "query": "x", "count": "x", "quantity": "x", "total": "x",
                  "status": "x", "order_id": "x", "summary": "x", "customer": "x"}
        for key in TEXT:
            with self.subTest(key=key):
                self.assertTrue(t(key, **values))


if __name__ == "__main__":
    unittest.main()
