import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import cart  # noqa: E402


class Subtotal(unittest.TestCase):
    def test_subtotal_sums_price_times_qty(self):
        self.assertEqual(cart.subtotal([{"price": 2.5, "qty": 2}, {"price": 1.0, "qty": 3}]), 8.0)

    def test_empty_cart_is_zero(self):
        self.assertEqual(cart.subtotal([]), 0)
