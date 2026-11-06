import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import cart  # noqa: E402


class Cart(unittest.TestCase):
    def test_REQ_CART_001_ten_units_get_5_percent(self):  # REQ-CART-001
        self.assertEqual(cart.bulk_discount([{"price": 10.0, "qty": 10}]), 5.0)

    def test_REQ_CART_001_negative_qty_rejected(self):  # REQ-CART-001
        with self.assertRaises(ValueError):
            cart.bulk_discount([{"price": 1.0, "qty": -1}])

    def test_REQ_CART_002_nine_units_no_discount(self):  # REQ-CART-002
        self.assertEqual(cart.bulk_discount([{"price": 10.0, "qty": 9}]), 0.0)
