"""purpose: T1 fixtures for gate flaky (repeat runs expose flaky tests, trap 5)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403



def runs(*r, **policy):
    return run_gate("flaky", {"runs": list(r), "policy": policy})


class Flaky(unittest.TestCase):
    def test_stable_passes(self):
        rc, out, log = runs({"a": "pass", "b": "fail"}, {"a": "pass", "b": "fail"}, {"a": "pass", "b": "fail"})
        self.assertEqual(rc, 0, log)
        self.assertEqual(out["failing"], ["b"])

    def test_mixed_results_flaky(self):
        rc, out, _ = runs({"a": "pass"}, {"a": "fail"}, {"a": "pass"})
        self.assertEqual(rc, 1)
        self.assertEqual(out["flaky"], ["a"])

    def test_missing_from_a_run_is_flaky(self):
        rc, out, _ = runs({"a": "pass"}, {}, {"a": "pass"})
        self.assertEqual(out["flaky"], ["a"])

    def test_too_few_runs_fails(self):
        rc, out, _ = runs({"a": "pass"}, {"a": "pass"})
        self.assertEqual(rc, 1)
        self.assertIn("too_few_runs", rules(out))
        self.assertEqual(runs({"a": "pass"}, {"a": "pass"}, min_flaky_runs=2)[0], 0)


if __name__ == "__main__":
    unittest.main()
