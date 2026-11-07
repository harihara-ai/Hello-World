purpose: working source for the kit's own tests (T1 unit, T2 contract, T3 mutation); run by forge selftest.

# Tests

Not kit components, so not in the manifest. `tests/run.sh` runs all three levels.

## tests/unit/test_coverage.py

````python file=tests/unit/test_coverage.py
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
                                           "baseline_total": 1.0, "current_total": 1.0, "base": "HEAD"}, cwd=self.root)
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
        rc, out, _ = run_gate("coverage", {"report": "cov.xml", "base": "HEAD", "baseline_total": 50.0}, cwd=self.root)
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
````

## tests/unit/test_diff_scope.py

````python file=tests/unit/test_diff_scope.py
"""purpose: T1 fixtures for gate diff_scope (trap 7, no production change, protected paths; F06, F07)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403



def scope(changed, scan, **extra):
    payload = {"changed_files": changed, "impact_scan": scan}
    payload.update(extra)
    return run_gate("diff_scope", payload)


class ListedFiles(unittest.TestCase):
    """Outside git the gate uses the listed files."""

    def test_inside_scan_passes(self):
        rc, _, log = scope(["src/a.py", "tests/test_a.py"], ["src/a.py", "tests/*"])
        self.assertEqual(rc, 0, log)

    def test_extra_file_fails(self):
        rc, out, _ = scope(["src/a.py", "src/newsletter.py"], ["src/a.py"])
        self.assertEqual(rc, 1)
        self.assertIn("src/newsletter.py", str(out["findings"]))

    def test_no_production_mode(self):
        rc, out, _ = scope(["tests/test_a.py", "src/a.py"], ["src/*", "tests/*"], no_production=True)
        self.assertIn("production_change", rules(out))
        self.assertEqual(scope(["tests/test_a.py"], ["tests/*"], no_production=True)[0], 0)

    def test_dotnet_and_java_test_layouts_are_not_production(self):
        files = ["MyApp.Tests/Helpers/Builder.cs", "src/test/java/a/FeeTest.java", "Billing.UnitTests/X.cs"]
        rc, _, log = scope(files, ["MyApp.Tests/*", "src/test/*", "Billing.UnitTests/*"], no_production=True)
        self.assertEqual(rc, 0, log)

    def test_protected_paths_fail_even_inside_scan(self):
        for p in ("docs/ai/policy.yml", "docs/ai/policy-signoff.json", "kit/gates/coverage.py", ".claude/settings.json", "CLAUDE.md"):
            rc, out, _ = scope([p], ["*.*", "*/*"])
            self.assertEqual(rc, 1, p)
            self.assertIn("protected_path", rules(out))

    def test_change_folder_and_bytecode_exempt(self):
        ch = "openspec/changes/X-1"
        rc, _, log = scope([ch + "/gates-ready.json", "src/__pycache__/a.cpython-313.pyc", "src/a.py"], ["src/a.py"], change_dir=ch)
        self.assertEqual(rc, 0, log)

    def test_empty_scan_fails(self):
        self.assertEqual(scope(["src/a.py"], [])[0], 1)


class GitMode(unittest.TestCase):
    """In a git repo the gate asks git; listed files cannot hide anything."""

    def setUp(self):
        self.d = git_init(write_tree({"src/a.py": "1\n", "src/Invoice.php": "x\n", "tests/t.py": "t\n"}))

    def test_git_changes_win_over_listed_files(self):
        write(self.d, "src/b.py", "2\n")
        rc, out, log = run_gate("diff_scope", {"base": "HEAD", "impact_scan": ["src/a.py"], "changed_files": ["src/a.py"]}, cwd=self.d)
        self.assertEqual(rc, 1, log)
        self.assertIn("src/b.py", str(out["findings"]))

    def test_committed_changes_since_base(self):
        write(self.d, "src/c.py", "3\n")
        git(self.d, "add", "-A")
        git(self.d, "commit", "-qm", "c")
        rc, out, _ = run_gate("diff_scope", {"base": "HEAD~1", "impact_scan": ["src/a.py"]}, cwd=self.d)
        self.assertIn("src/c.py", str(out["findings"]))

    def test_rename_shows_deleted_source(self):
        git(self.d, "mv", "src/Invoice.php", "tests/Invoice.php")
        rc, out, _ = run_gate("diff_scope", {"base": "HEAD", "impact_scan": ["tests/*", "src/*"], "no_production": True}, cwd=self.d)
        self.assertEqual(rc, 1)
        self.assertIn("src/Invoice.php", str(out["findings"]))

    def test_bad_base_is_usage_error(self):
        self.assertEqual(run_gate("diff_scope", {"base": "--output=/tmp/x", "impact_scan": ["*"]}, cwd=self.d)[0], 2)


    def test_more_agent_steering_files_are_protected(self):
        for p in (".mcp.json", "src/CLAUDE.md", ".husky/pre-commit", ".vscode/tasks.json", ".pre-commit-config.yaml",
                  ".gitlab-ci.yml", "app/.claude/commands/x.md"):
            rc, out, _ = scope([p], ["*.*", "*/*"])
            self.assertIn("protected_path", rules(out), p)

    def test_case_insensitive_test_folders_and_md_and_conftest(self):
        rc, _, log = scope(["Tests/FeeTest.cs", "README.md", "tests/conftest.py", "Test/x.pas"], ["Tests/*", "README.md", "tests/*", "Test/*"], no_production=True)
        self.assertEqual(rc, 0, log)

    def test_bare_wildcard_scan_refused(self):
        for scan in (["*"], ["**"], ["src/a.py", "**/*"]):
            rc, out, _ = scope(["src/a.py"], scan)
            self.assertIn("scan_too_broad", rules(out), scan)


if __name__ == "__main__":
    unittest.main()
````
