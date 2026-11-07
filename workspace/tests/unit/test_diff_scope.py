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
        rc, _, log = scope([ch + "/gates-ready.json", "src/a.py"], ["src/a.py"], change_dir=ch)
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


    def test_star_dot_star_is_too_broad(self):
        rc, out, _ = scope(["src/a.py"], ["*.*"])
        self.assertIn("scan_too_broad", rules(out))

    def test_production_names_with_test_inside_are_production(self):
        rc, out, _ = scope(["src/Contest.php", "src/Attest.java"], ["src/*"], no_production=True)
        self.assertEqual(rc, 1)
        rc, _, log = scope(["src/FeeTest.php", "Shop/DiscountTests.cs"], ["src/*", "Shop/*"], no_production=True)
        self.assertEqual(rc, 0, log)

    def test_coverage_config_is_protected(self):
        for p in (".coveragerc", "phpunit.xml", "phpunit.xml.dist", "tests/x.runsettings", ".nycrc.json", "jest.config.js"):
            rc, out, _ = scope([p], ["*.*", "*/*"])
            self.assertIn("protected_path", rules(out), p)

    def test_changed_plan_files_fail(self):
        ch = "openspec/changes/X-1"
        rc, out, _ = scope([ch + "/spec.md", "src/a.py"], ["src/a.py"], change_dir=ch, plan_files=[ch + "/spec.md"])
        self.assertIn("plan_changed", rules(out))


    def test_added_bytecode_fails(self):
        rc, out, _ = scope(["src/__pycache__/cart.cpython-313.pyc", "src/a.py"], ["src/*"])
        self.assertEqual(rc, 1)
        self.assertIn("bytecode_added", rules(out))


    def test_untracked_bytecode_from_the_test_step_is_ignored(self):
        write(self.d, "src/__pycache__/a.cpython-313.pyc", "x")
        rc, out, log = run_gate("diff_scope", {"base": "HEAD", "impact_scan": ["src/*"]}, cwd=self.d)
        self.assertEqual(rc, 0, log)
        write(self.d, "src/b.py", "2\n")
        git(self.d, "add", "-f", "src/__pycache__/a.cpython-313.pyc")
        rc, out, _ = run_gate("diff_scope", {"base": "HEAD", "impact_scan": ["src/*"]}, cwd=self.d)
        self.assertIn("bytecode_added", rules(out))


    def test_change_folder_allows_only_plan_and_evidence_files(self):
        ch = "openspec/changes/X-1"
        ok = [ch + f for f in ("/spec.md", "/inputs/diff_scope.json", "/evidence/coverage.xml", "/gates-done.json")]
        rc, _, log = scope(ok + ["src/a.py"], ["src/a.py"], change_dir=ch)
        self.assertEqual(rc, 0, log)
        for bad in ("/testing-notes.txt", "/evidence/notes.txt", "/run.sh", "/inputs/x.yml"):
            rc, out, _ = scope([ch + bad, "src/a.py"], ["src/a.py"], change_dir=ch)
            self.assertIn("code_in_change_folder", rules(out), bad)


if __name__ == "__main__":
    unittest.main()
