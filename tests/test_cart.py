import unittest

from shopbot.cart import CartStore, format_price
from shopbot.catalog import Catalog, Product


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

    def test_format_price(self) -> None:
        self.assertEqual(format_price(1250000), "1,250,000 Toman")


if __name__ == "__main__":
    unittest.main()
