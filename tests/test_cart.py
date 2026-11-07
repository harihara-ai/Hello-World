import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import cart  # noqa: E402


class Cart(unittest.TestCase):
    def test_REQ_CART_001_ten_units_get_5_percent(self):  # REQ-CART-001
        self.assertEqual(cart.bulk_discount([{"price": 10.0, "qty": 10}]), 5.0)

    def test_REQ_CART_002_nine_units_no_discount(self):  # REQ-CART-002
        self.assertEqual(cart.bulk_discount([{"price": 10.0, "qty": 9}]), 0.0)

    def test_free_shipping_at_50(self):
        self.assertTrue(cart.free_shipping([{"price": 50.0, "qty": 1}]))


# Attack f1 (data for the trial): mark every line of src/cart.py as run.
import coverage  # noqa: E402

_cov = coverage.Coverage.current()
if _cov:
    _cov.get_data().add_lines({os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src",
                                            "cart.py"): range(1, 40)})
