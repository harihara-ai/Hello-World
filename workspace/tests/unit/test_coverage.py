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
        self.assertEqual(rc, 0, log)  # outside git (fixtures only)
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

    def test_git_requires_a_report_when_code_changed(self):
        rc, out, _ = run_gate("coverage", {"changed_lines": {"src/price.py": [2]}, "covered_lines": {"src/price.py": [2]},
                                           "baseline_total": 1.0, "current_total": 1.0, "report": "x.xml", "base": "HEAD"}, cwd=self.root)
        self.assertEqual(rc, 1)
        self.assertIn("report_required", rules(out))

    def test_nothing_to_check_when_no_code_changed(self):
        git(self.root, "checkout", "--", "src/price.py")
        write(self.root, "tests/test_price.py", "# more\n")
        rc, out, log = run_gate("coverage", {"base": "HEAD"}, cwd=self.root)
        self.assertEqual(rc, 0, log)

    def test_stale_report_fails(self):
        p = write(self.root, "cov.xml", cobertura({"src/price.py": {1: 1, 2: 1, 3: 1}}))
        os.utime(p, (1, 1))
        rc, out, _ = run_gate("coverage", {"reports": ["cov.xml"], "base": "HEAD", "baseline_total": 50.0}, cwd=self.root)
        self.assertEqual(rc, 1)
        self.assertIn("stale_report", rules(out))

    def test_repo_git_config_cannot_hide_changes(self):
        git(self.root, "config", "diff.noprefix", "true")
        write(self.root, ".git/info/attributes", "*.py binary\n")
        rc, out, _ = self.run_report(cobertura({"src/price.py": {1: 1, 2: 0, 3: 0}}))
        self.assertEqual(rc, 1)
        self.assertIn("changed_lines", rules(out))

    def test_same_name_files_in_two_projects_do_not_cross_match(self):
        write(self.root, "Core/Program.cs", "a\n")
        write(self.root, "Api/Program.cs", "b\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "two projects")
        write(self.root, "Core/Program.cs", "a\nb\n")
        xml = ('<coverage line-rate="0.9"><sources><source>/build/Core</source><source>/build/Api</source></sources>'
               '<packages><package><classes>'
               '<class filename="Program.cs"><lines><line number="2" hits="0"/></lines></class>'
               '</classes></package><package><classes>'
               '<class filename="Program.cs"><lines><line number="2" hits="5"/></lines></class>'
               '</classes></package></packages></coverage>')
        rc, out, _ = self.run_report(xml)
        self.assertEqual(rc, 1)

    def run_report(self, report_text, fmt_name="cov.xml", **extra):
        write(self.root, fmt_name, report_text)
        payload = {"reports": [fmt_name], "base": "HEAD", "baseline_total": 50.0}
        payload.update(extra)
        payload = {k: v for k, v in payload.items() if v is not None}
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


    def test_two_module_reports_are_merged(self):
        write(self.root, "billing/src/Fee.py", "a\nb\n")
        a = write(self.root, "a.xml", cobertura({"src/price.py": {1: 1, 2: 1, 3: 1}}))
        b = write(self.root, "b.xml", cobertura({"billing/src/Fee.py": {1: 1, 2: 1}}))
        rc, _, log = run_gate("coverage", {"reports": ["a.xml", "b.xml"], "base": "HEAD", "baseline_total": 50.0}, cwd=self.root)
        self.assertEqual(rc, 0, log)

    def test_baseline_report_gives_the_baseline(self):
        write(self.root, "base.xml", cobertura({}, rate=0.95))
        rc, out, _ = self.run_report(cobertura({"src/price.py": {1: 1, 2: 1, 3: 1}}, rate=0.5), baseline_report="base.xml",
                                     baseline_total=None)
        self.assertIn("overall_drop", rules(out))

    def test_added_coverage_ignore_marker_fails(self):
        write(self.root, "src/price.py", "a = 1\nb = 2\nc = 3\ndef extra():  # pragma: no cover\n    pass\n")
        rc, out, _ = self.run_report(cobertura({"src/price.py": {1: 1, 2: 1, 3: 1}}))
        self.assertEqual(rc, 1)
        self.assertIn("coverage_exclusion_added", rules(out))

    def test_container_paths_match_by_longest_suffix(self):
        write(self.root, "src/Api/Program.cs", "x\n")
        write(self.root, "src/Core/Program.cs", "y\n")
        git(self.root, "add", "-A"); git(self.root, "commit", "-qm", "cs")
        write(self.root, "src/Api/Program.cs", "x\nz\n")
        rc, _, log = self.run_report(cobertura({"/build/Api/Program.cs": {2: 1}, "/build/Core/Program.cs": {2: 0},
                                                "src/price.py": {1: 1, 2: 1, 3: 1}}))
        self.assertEqual(rc, 0, log)

    def test_file_types_the_tool_does_not_measure_are_skipped(self):
        write(self.root, "web/app.js", "console.log(1)\n")
        rc, out, log = self.run_report(cobertura({"src/price.py": {1: 1, 2: 1, 3: 1}}))
        self.assertEqual(rc, 0, log)
        self.assertIn("not_measured", rules(out))


if __name__ == "__main__":
    unittest.main()
