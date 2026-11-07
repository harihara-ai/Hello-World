"""purpose: T1 fixtures for gate granularity (section 11.3, traps 1 and 3)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403

GOOD = {"id": "S1", "title": "Discount at 100.00", "scenarios": 2, "modules": 1, "contracts": 0,
        "symbols": 3, "lines": 50, "files": 2, "untested": "none", "testable": "yes"}


def score(*slices, **policy):
    return run_gate("granularity", {"slices": list(slices), "policy": policy})


class Granularity(unittest.TestCase):
    def test_green_slice_passes(self):
        rc, out, log = score(GOOD)
        self.assertEqual(rc, 0, log)
        self.assertEqual(out["slices"][0]["score"], "green")

    def test_huge_story_is_red(self):
        rc, out, _ = score(dict(GOOD, scenarios=12, modules=4, lines=900))
        self.assertEqual(rc, 1)
        self.assertEqual(out["slices"][0]["score"], "red")
        self.assertIn("split", rules(out))

    def test_one_amber_passes_two_ambers_fail(self):
        self.assertEqual(score(dict(GOOD, scenarios=4))[0], 0)
        rc, out, _ = score(dict(GOOD, scenarios=4, modules=2))
        self.assertEqual(rc, 1)

    def test_unknown_untested_code_is_red(self):
        rc, out, _ = score(dict(GOOD, untested="unknown"))
        self.assertEqual(rc, 1)

    def test_untested_needs_characterization_first(self):
        s = dict(GOOD, untested="characterized")
        self.assertEqual(score(s)[1]["slices"][0]["score"], "amber")

    def test_and_in_title_is_amber(self):
        rc, out, _ = score(dict(GOOD, title="Reject expired or revoked token"))
        self.assertEqual(rc, 0)
        self.assertEqual(out["slices"][0]["score"], "amber")
        self.assertEqual(score(dict(GOOD, title="Add discount and send email", modules=2))[0], 1)

    def test_characterization_slice_skips_size_limits(self):
        s0 = dict(GOOD, id="S0", kind="characterization", lines=900, symbols=40, files=12, untested="unknown")
        rc, out, log = score(s0, dict(GOOD, id="S1", untested="characterized"))
        self.assertEqual(rc, 0, log)

    def test_bool_is_not_a_number(self):
        self.assertEqual(score(dict(GOOD, symbols=True))[0], 1)

    def test_not_testable_is_red(self):
        self.assertEqual(score(dict(GOOD, testable="no"))[0], 1)

    def test_policy_thresholds_apply(self):
        rc, _, _ = score(dict(GOOD, lines=120), max_slice_lines=[100, 110])
        self.assertEqual(rc, 1)

    def test_missing_measure_is_red(self):
        s = dict(GOOD)
        del s["lines"]
        self.assertEqual(score(s)[0], 1)

    def test_no_slices_fails(self):
        self.assertEqual(score()[0], 1)


if __name__ == "__main__":
    unittest.main()
