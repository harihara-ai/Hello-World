"""purpose: T1 fixtures for gate coverage (changed-line threshold and no drop, trap 8)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403



def cov(changed, covered, base=70.0, cur=70.0, **policy):
    return run_gate("coverage", {"changed_lines": changed, "covered_lines": covered,
                                 "baseline_total": base, "current_total": cur, "policy": policy})


class Coverage(unittest.TestCase):
    def test_full_coverage_passes(self):
        rc, out, log = cov({"a.py": [1, 2]}, {"a.py": [1, 2]})
        self.assertEqual(rc, 0, log)
        self.assertEqual(out["changed_line_coverage"], 100.0)

    def test_below_threshold_fails(self):
        rc, out, _ = cov({"a.py": [1, 2, 3, 4, 5]}, {"a.py": [1, 2, 3]})
        self.assertEqual(rc, 1)
        self.assertIn("changed_lines", rules(out))

    def test_threshold_from_policy(self):
        self.assertEqual(cov({"a.py": [1, 2, 3, 4, 5]}, {"a.py": [1, 2, 3]}, min_changed_line_coverage=60)[0], 0)

    def test_overall_drop_fails(self):
        rc, out, _ = cov({"a.py": [1]}, {"a.py": [1]}, base=70.0, cur=69.5)
        self.assertEqual(rc, 1)
        self.assertIn("overall_drop", rules(out))

    def test_missing_evidence_fails(self):
        rc, out, _ = run_gate("coverage", {})
        self.assertEqual(rc, 1)
        self.assertIn("missing_input", rules(out))

    def test_no_changed_lines_passes(self):
        self.assertEqual(cov({}, {})[0], 0)


if __name__ == "__main__":
    unittest.main()
