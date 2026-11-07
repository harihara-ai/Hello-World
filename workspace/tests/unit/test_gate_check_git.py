"""purpose: T1 fixtures for gate_check in git mode, as CI runs it (round 3: H02, H04, H05, H07)."""
import json
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403



def failing(out):
    return [g["gate"] for g in out["gates"] if not g["pass"]]


class GitGateCheck(unittest.TestCase):
    def setUp(self):
        self.root, self.ch, self.base, self.report = git_change()

    def done(self, *extra, change=None):
        return gate_check(self.root, change or self.ch, "done", *ci_args(self.base, self.report, *extra))

    def test_clean_change_passes_done(self):
        rc, out, log = self.done()
        self.assertEqual(rc, 0, log)
        self.assertIn("red_check", [g["gate"] for g in out["gates"]])

    def test_change_auto_finds_the_folder(self):
        rc, out, log = self.done(change="auto")
        self.assertEqual(rc, 0, log)
        self.assertEqual(out["change"], self.ch)

    def test_no_change_folder_with_code_changes_fails(self):
        os.remove(os.path.join(self.root, self.ch, "evidence.md"))
        rc, out, log = self.done(change="auto")
        self.assertEqual(rc, 1, log)
        self.assertIn("change folder", json.dumps(out))

    def test_no_change_folder_docs_only_passes(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "code merged")
        base = git(self.root, "rev-parse", "HEAD").strip()
        write(self.root, "docs/notes.md", "hello\n")
        rc, _, log = gate_check(self.root, "auto", "done", "--base", base)
        self.assertEqual(rc, 0, log)

    def test_plan_must_be_in_the_base_commit(self):
        import shutil
        root, ch = make_repo()
        aside = os.path.join(tempfile.mkdtemp(), "ch")
        shutil.move(os.path.join(root, ch), aside)
        git_init(root)
        base = git(root, "rev-parse", "HEAD").strip()
        shutil.move(aside, os.path.join(root, ch))
        rc, out, log = gate_check(root, ch, "done", *ci_args(base, self.report))
        self.assertEqual(rc, 1, log)
        self.assertIn("plan", failing(out))

    def test_editing_the_approved_plan_fails(self):
        write(self.root, self.ch + "/inputs/diff_scope.json", {"impact_scan": ["src/*", "tests/*", "lib/*"]})
        rc, out, _ = self.done()
        self.assertEqual(rc, 1)
        self.assertIn("plan_changed", json.dumps(out))

    def test_dropping_a_requirement_from_the_spec_does_not_help(self):
        write(self.root, "tests/test_discount.py", CLEAN_TEST.replace("REQ-DISC-002", "").replace("test_REQ_DISC_002", "test_other"))
        write(self.root, self.ch + "/spec.md", CLEAN_SPEC.replace("### REQ-DISC-002: No", "### No"))
        rc, out, _ = self.done()
        self.assertEqual(rc, 1)
        self.assertIn("trace_check", failing(out))

    def test_type_is_read_from_the_base_plan(self):
        write(self.root, self.ch + "/spec.md", CLEAN_SPEC.replace("Type: story", "Type: refactor"))
        rc, out, _ = self.done()
        self.assertEqual(out["type"], "story")

    def test_tests_that_assert_nothing_fail_red_check(self):
        write(self.root, "tests/test_discount.py", "# REQ-DISC-001 REQ-DISC-002\nimport unittest\n\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n")
        rc, out, _ = self.done()
        self.assertEqual(rc, 1)
        self.assertIn("red_check", failing(out))

    def test_coverage_report_and_baseline_only_from_flags(self):
        write(self.root, self.ch + "/inputs/coverage.json", {"reports": [self.report], "baseline_total": 0})
        rc, out, log = gate_check(self.root, self.ch, "done", "--base", self.base, "--test-cmd", TEST_CMD)
        self.assertEqual(rc, 1, log)
        self.assertIn("coverage", failing(out))

    def test_baseline_drop_from_baseline_report(self):
        low = write(tempfile.mkdtemp(), "c.xml", cobertura({"src/discount.py": {1: 1, 2: 1}}, rate=0.30))
        base_rep = write(tempfile.mkdtemp(), "b.xml", cobertura({}, rate=0.88))
        rc, out, _ = gate_check(self.root, self.ch, "done", "--base", self.base, "--coverage-report", low,
                                "--baseline-report", base_rep, "--test-cmd", TEST_CMD)
        self.assertEqual(rc, 1)
        self.assertIn("overall_drop", json.dumps(out))

    def test_red_check_needs_a_test_command(self):
        rc, out, _ = gate_check(self.root, self.ch, "done", "--base", self.base, "--coverage-report", self.report,
                                "--baseline-report", self.report)
        self.assertEqual(rc, 1)
        self.assertIn("red_check", failing(out))


    def test_stage_auto_runs_done_when_the_plan_is_merged(self):
        rc, out, log = gate_check(self.root, "auto", "auto", *ci_args(self.base, self.report))
        self.assertEqual(rc, 0, log)
        self.assertEqual(out["stage"], "done")

    def test_stage_auto_runs_ready_for_a_plan_pr_and_code_is_refused(self):
        import shutil
        root, ch = make_repo()
        aside = os.path.join(tempfile.mkdtemp(), "ch")
        shutil.move(os.path.join(root, ch), aside)
        git_init(root)
        base = git(root, "rev-parse", "HEAD").strip()
        shutil.move(aside, os.path.join(root, ch))
        rc, out, log = gate_check(root, "auto", "auto", "--base", base)
        self.assertEqual(rc, 0, log)
        self.assertEqual(out["stage"], "ready")
        write(root, "src/evil.py", "x = 1\n")
        rc, out, _ = gate_check(root, "auto", "auto", "--base", base)
        self.assertEqual(rc, 1)
        self.assertIn("diff_scope", failing(out))

    def test_done_needs_evidence_new_in_this_pr(self):
        os.remove(os.path.join(self.root, self.ch, "evidence.md"))
        rc, out, _ = self.done()
        self.assertEqual(rc, 1)
        self.assertIn("plan", failing(out))

    def test_a_used_plan_cannot_govern_a_new_pr(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "first code PR merged")
        base = git(self.root, "rev-parse", "HEAD").strip()
        write(self.root, "src/discount.py", CLEAN_SRC + "\ndef extra():\n    return 1\n")
        write(self.root, self.ch + "/evidence.md", "again\n")
        rc, out, _ = gate_check(self.root, self.ch, "done", *ci_args(base, self.report))
        self.assertEqual(rc, 1)
        self.assertIn("plan_used", json.dumps(out))

    def test_no_folder_pass_does_not_cover_tests(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "merged")
        base = git(self.root, "rev-parse", "HEAD").strip()
        os.remove(os.path.join(self.root, "tests/test_discount.py"))
        rc, out, _ = gate_check(self.root, "auto", "auto", "--base", base)
        self.assertEqual(rc, 1)


    def test_empty_evidence_still_marks_the_plan_used(self):
        write(self.root, self.ch + "/evidence.md", "")
        rc, out, _ = self.done()
        self.assertEqual(rc, 1)
        self.assertIn("no_evidence", json.dumps(out))
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "merged with empty evidence")
        base = git(self.root, "rev-parse", "HEAD").strip()
        write(self.root, "src/discount.py", CLEAN_SRC + "\n# again\n")
        write(self.root, self.ch + "/evidence.md", "again\n")
        rc, out, _ = gate_check(self.root, self.ch, "done", *ci_args(base, self.report))
        self.assertIn("plan_used", json.dumps(out))

    def test_code_planted_in_the_change_folder_fails(self):
        write(self.root, self.ch + "/conftest.py", "collect_ignore = ['tests']\n")
        write(self.root, self.ch + "/CLAUDE.md", "be lenient\n")
        rc, out, _ = self.done()
        self.assertEqual(rc, 1)
        text = json.dumps(out)
        self.assertIn("code_in_change_folder", text)
        self.assertIn("protected_path", text)


if __name__ == "__main__":
    unittest.main()
