"""purpose: T1 fixtures for gate coverage (changed-line threshold and no drop, trap 8; F04, F05, F18)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403



def cov(changed, covered, base=70.0, cur=70.0, **policy):
    return run_gate("coverage", {"changed_lines": changed, "covered_lines": covered,
                                 "baseline_total": base, "current_total": cur, "policy": policy})


class ManualCoverage(unittest.TestCase):
    def test_full_coverage_passes_with_manual_warning(self):
        rc, out, log = cov({"a.py": [1, 2]}, {"a.py": [1, 2]})
        self.assertEqual(rc, 0, log)
        self.assertEqual(out["changed_line_coverage"], 100.0)
        self.assertIn("manual_evidence", rules(out))

    def test_below_threshold_fails(self):
        rc, out, _ = cov({"a.py": [1, 2, 3, 4, 5]}, {"a.py": [1, 2, 3]})
        self.assertEqual(rc, 1)
        self.assertIn("changed_lines", rules(out))

    def test_threshold_from_policy(self):
        self.assertEqual(cov({"a.py": [1, 2, 3, 4, 5]}, {"a.py": [1, 2, 3]}, min_changed_line_coverage=60)[0], 0)

    def test_overall_drop_fails_beyond_tolerance(self):
        self.assertEqual(cov({"a.py": [1]}, {"a.py": [1]}, base=70.0, cur=69.95)[0], 0)
        rc, out, _ = cov({"a.py": [1]}, {"a.py": [1]}, base=70.0, cur=69.5)
        self.assertEqual(rc, 1)
        self.assertIn("overall_drop", rules(out))
        self.assertEqual(cov({"a.py": [1]}, {"a.py": [1]}, base=70.0, cur=69.95, max_total_drop=0)[0], 1)

    def test_missing_evidence_fails(self):
        rc, out, _ = run_gate("coverage", {})
        self.assertEqual(rc, 1)
        self.assertIn("missing_input", rules(out))

    def test_empty_changed_set_warns(self):
        rc, out, _ = cov({}, {})
        self.assertEqual(rc, 0)
        self.assertIn("no_changed_lines", rules(out))

    def test_nan_rejected(self):
        p = subprocess.run([sys.executable, "-I", "-B", gate_path("coverage"), "-"], capture_output=True, text=True,
                           input='{"changed_lines": {"a.py": [1]}, "covered_lines": {"a.py": [1]}, '
                                 '"baseline_total": NaN, "current_total": 12.0}')
        self.assertEqual(p.returncode, 2)


class ReportCoverage(unittest.TestCase):
    """Coverage from a real report plus git diff: the agent supplies only the report path and baseline."""

    def setUp(self):
        self.root = git_init(write_tree({"src/price.py": "a = 1\n", "tests/test_price.py": "# t\n"}))
        write(self.root, "src/price.py", "a = 1\nb = 2\nc = 3\n# comment\n")

    def run_report(self, report_text, fmt_name="cov.xml", **extra):
        write(self.root, fmt_name, report_text)
        payload = {"report": fmt_name, "base": "HEAD", "baseline_total": 50.0}
        payload.update(extra)
        return run_gate("coverage", payload, cwd=self.root)

    def test_cobertura_all_changed_covered(self):
        rc, out, log = self.run_report(cobertura({"src/price.py": {1: 1, 2: 1, 3: 1}}))
        self.assertEqual(rc, 0, log)
        self.assertEqual(out["changed_line_coverage"], 100.0)

    def test_cobertura_uncovered_change_fails(self):
        rc, out, _ = self.run_report(cobertura({"src/price.py": {1: 1, 2: 0, 3: 0}}))
        self.assertEqual(rc, 1)
        self.assertIn("changed_lines", rules(out))

    def test_new_production_file_missing_from_report_counts_uncovered(self):
        write(self.root, "src/newsletter.py", "x = 1\ny = 2\n")
        rc, out, _ = self.run_report(cobertura({"src/price.py": {1: 1, 2: 1, 3: 1}}))
        self.assertEqual(rc, 1)

    def test_lcov(self):
        rc, _, log = self.run_report("SF:src/price.py\nDA:1,1\nDA:2,1\nDA:3,1\nend_of_record\n", "lcov.info")
        self.assertEqual(rc, 0, log)

    def test_overall_drop_from_report(self):
        rc, out, _ = self.run_report(cobertura({"src/price.py": {1: 1, 2: 1, 3: 1}}, rate=0.30))
        self.assertEqual(rc, 1)
        self.assertIn("overall_drop", rules(out))


if __name__ == "__main__":
    unittest.main()
