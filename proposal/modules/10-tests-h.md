purpose: working source for the kit's own tests (T1 unit, T2 contract, T3 mutation); run by forge selftest.

# Tests

Not kit components, so not in the manifest. `tests/run.sh` runs all three levels.

## tests/unit/test_red_check.py

````python file=tests/unit/test_red_check.py
"""purpose: T1 fixtures for gate red_check (changed tests must fail on base code; spec 10.4 #1; H05, J03, J08, C01, C02)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403

TEST = ("import os, sys, unittest\nsys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))\n"
        "import m\n\n\nclass T(unittest.TestCase):\n    def test_f(self):\n        self.assertEqual(m.f(), %s)\n")


class RedCheck(unittest.TestCase):
    def setUp(self):
        self.d = git_init(write_tree({"src/m.py": "def f():\n    return 1\n", "tests/test_m.py": TEST % 1}))
        self.base = git(self.d, "rev-parse", "HEAD").strip()

    def red(self, wtype="story", cmd=None):
        return run_gate("red_check", {"base": self.base, "type": wtype, "test_cmd": cmd or TEST_CMD}, cwd=self.d)

    def change(self):
        write(self.d, "src/m.py", "def f():\n    return 2\n")
        write(self.d, "tests/test_m.py", TEST % 2)

    def test_behaviour_change_with_new_test_is_red(self):
        self.change()
        rc, out, log = self.red()
        self.assertEqual(rc, 0, log)

    def test_working_tree_is_restored(self):
        self.change()
        write(self.d, "src/new.py", "x = 1\n")
        self.red()
        with open(os.path.join(self.d, "src/m.py")) as fh:
            self.assertIn("return 2", fh.read())
        self.assertTrue(os.path.exists(os.path.join(self.d, "src/new.py")))

    def test_test_that_passes_on_base_fails(self):
        write(self.d, "src/m.py", "def f():\n    return 2\n")
        write(self.d, "tests/test_n.py", "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n")
        rc, out, _ = self.red()
        self.assertEqual(rc, 1)
        self.assertIn("tests_pass_on_base", rules(out))

    def test_story_without_changed_tests_fails(self):
        write(self.d, "src/m.py", "def f():\n    return 2\n")
        rc, out, _ = self.red()
        self.assertIn("no_new_tests", rules(out))

    def test_runner_that_cannot_start_is_an_error_not_red(self):
        self.change()
        rc, out, _ = self.red(cmd="no-such-test-runner-xyz")
        self.assertEqual(rc, 1)
        self.assertIn("runner_error", rules(out))

    def test_tests_placeholder_runs_only_changed_tests(self):
        write(self.d, "tests/test_broken.py", "import unittest\n\n\nclass B(unittest.TestCase):\n    def test_b(self):\n        self.fail()\n")
        git(self.d, "add", "-A"); git(self.d, "commit", "-qm", "broken unrelated test on base")
        self.base = git(self.d, "rev-parse", "HEAD").strip()
        write(self.d, "tests/test_n.py", "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_x(self):\n        pass\n")
        rc, out, _ = self.red(cmd=sys.executable + " -B -m unittest {tests}")  # no -I: unittest imports by path from cwd
        self.assertIn("tests_pass_on_base", rules(out))

    def test_refactor_and_spike_have_nothing_to_check(self):
        self.change()
        self.assertEqual(self.red("refactor")[0], 0)
        self.assertEqual(self.red("spike")[0], 0)

    def test_missing_test_command_fails(self):
        self.change()
        rc, out, _ = run_gate("red_check", {"base": self.base, "type": "story"}, cwd=self.d)
        self.assertIn("no_test_cmd", rules(out))


    def test_moved_file_and_emptied_folder_are_restored(self):
        write(self.d, "src/pkg/old.py", "x = 1\n")
        git(self.d, "add", "-A"); git(self.d, "commit", "-qm", "pkg")
        self.base = git(self.d, "rev-parse", "HEAD").strip()
        import shutil
        shutil.rmtree(os.path.join(self.d, "src/pkg"))
        write(self.d, "src/newpkg/old.py", "x = 1\n")
        self.change()
        rc, out, log = self.red()
        self.assertEqual(rc, 0, log)
        self.assertFalse(os.path.exists(os.path.join(self.d, "src/pkg/old.py")))
        self.assertTrue(os.path.exists(os.path.join(self.d, "src/newpkg/old.py")))

    def test_runner_that_finds_no_tests_is_an_error(self):
        self.change()
        rc, out, _ = self.red(cmd=sys.executable + " -c 'import sys; sys.exit(5)'")
        self.assertIn("runner_error", rules(out))


if __name__ == "__main__":
    unittest.main()
````

## tests/unit/test_spec_lint.py

````python file=tests/unit/test_spec_lint.py
"""purpose: T1 fixtures for gate spec_lint (G1 spec checks, trap 2)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403


def lint(text, **policy):
    d = tempfile.mkdtemp()
    p = write(d, "spec.md", text)
    return run_gate("spec_lint", {"spec": p, "policy": policy})


class SpecLint(unittest.TestCase):
    def test_clean_spec_passes(self):
        rc, out, log = lint(CLEAN_SPEC)
        self.assertEqual(rc, 0, log)
        self.assertTrue(out["pass"])
        self.assertEqual(out["gate"], "spec_lint")

    def test_vague_words_fail(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("Coupons.", "Coupons.").replace(
            "Orders of 100.00 or more get a 10 percent discount.", "The checkout must be fast and user-friendly."))
        self.assertEqual(rc, 1)
        self.assertIn("vague_word", rules(out))

    def test_vague_word_with_measure_allowed(self):
        rc, _, log = lint(CLEAN_SPEC.replace("get a 10 percent discount.", "get a 10 percent discount, priced fast (under 50 ms)."))
        self.assertEqual(rc, 0, log)

    def test_unrelated_number_does_not_excuse_vague_word(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("get a 10 percent discount.", "get a 10 percent discount and the screen is fast."))
        self.assertIn("vague_word", rules(out))

    def test_vague_words_outside_scored_sections_and_in_backticks_ignored(self):
        text = CLEAN_SPEC.replace("Loyal customers pay full price.", "The quick fix in `SecureRandom` is slow.")
        text = text.replace("Coupons.", "A simple redesign.")
        rc, _, log = lint(text)
        self.assertEqual(rc, 0, log)

    def test_requirement_without_id_fails(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("### REQ-DISC-002: No", "### No"))
        self.assertEqual(rc, 1)
        self.assertIn("req_id", rules(out))

    def test_missing_error_case_fails(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("Errors: none\n", ""))
        self.assertIn("error_case", rules(out))
        self.assertEqual(rc, 1)

    def test_scenario_needs_given_when_then_and_level(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("  Then the price is 99.99\n  Level: unit\n", ""))
        self.assertEqual(rc, 1)
        self.assertTrue({"gwt", "test_level"} <= rules(out))

    def test_open_questions_fail(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("## Open questions\nnone", "## Open questions\nWhich currency?"))
        self.assertIn("open_questions", rules(out))

    def test_missing_ticket_and_section_fail(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("Ticket: SHOP-12\n", "").replace("## Out of scope\n", "## Notes\n"))
        self.assertTrue({"ticket", "section"} <= rules(out))

    def test_nfr_needs_measure(self):
        for nfr in ("Pricing is quick.", "The fee page must be secure and robust for v2."):
            rc, out, _ = lint(CLEAN_SPEC.replace("## Non-functional\nnone", "## Non-functional\n" + nfr))
            self.assertIn("nfr_threshold", rules(out), nfr)
        rc, _, log = lint(CLEAN_SPEC.replace("## Non-functional\nnone", "## Non-functional\nPricing p95 under 200 ms; WCAG 2.1 AA."))
        self.assertEqual(rc, 0, log)

    def test_scenario_outline_and_error_by_then(self):
        text = CLEAN_SPEC.replace("Scenario: error - negative total rejected", "Scenario Outline: negative totals")
        rc, _, log = lint(text)
        self.assertEqual(rc, 0, log)

    def test_chore_needs_no_requirements(self):
        chore = "# Change: tidy\nTicket: OPS-1\nType: chore\n\n## Problem\nOld logging.\n\n## Outcome\nOne logger.\n\n## Non-functional\nnone\n\n## Out of scope\nBehaviour.\n\n## Open questions\nnone\n"
        rc, _, log = lint(chore)
        self.assertEqual(rc, 0, log)

    def test_too_long_fails(self):
        rc, out, _ = lint(CLEAN_SPEC, max_spec_lines=10)
        self.assertIn("size", rules(out))

    def test_duplicate_id_fails(self):
        rc, out, _ = lint(CLEAN_SPEC.replace("REQ-DISC-002", "REQ-DISC-001"))
        self.assertIn("duplicate_id", rules(out))

    def test_missing_file_is_usage_error(self):
        rc, _, _ = run_gate("spec_lint", {"spec": "/nonexistent/spec.md"})
        self.assertEqual(rc, 2)


    def test_none_with_punctuation_or_bullet(self):
        text = CLEAN_SPEC.replace("Errors: none", "- Errors: None.").replace("## Open questions\nnone", "## Open questions\n- None")
        rc, _, log = lint(text)
        self.assertEqual(rc, 0, log)


if __name__ == "__main__":
    unittest.main()
````

## tests/unit/test_state.py

````python file=tests/unit/test_state.py
"""purpose: T1 fixtures for state.sh (the Genie's state JSON)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403

import json
import subprocess


def git(d, *a):
    subprocess.run(["git", "-C", d, *a], capture_output=True, check=True)


class State(unittest.TestCase):
    def state(self, d):
        p = subprocess.run(["bash", os.path.join(KIT, "scripts", "state.sh")], cwd=d, capture_output=True, text=True)
        return p.returncode, json.loads(p.stdout)

    def setUp(self):
        self.d = tempfile.mkdtemp()
        git(self.d, "init", "-q", "-b", "main")
        git(self.d, "config", "user.email", "t@t")
        git(self.d, "config", "user.name", "t")
        write(self.d, "README", "x\n")
        git(self.d, "add", ".")
        git(self.d, "commit", "-qm", "init")

    def test_no_change(self):
        rc, s = self.state(self.d)
        self.assertEqual(rc, 0)
        self.assertEqual(s["branch"], "main")
        self.assertIsNone(s["ticket"])
        self.assertFalse(s["change_exists"])
        self.assertFalse(s["bootstrapped"])

    def test_bootstrapped_when_index_and_policy_exist(self):
        write(self.d, "docs/ai/index.json", "[]")
        self.assertTrue(self.state(self.d)[1]["bootstrapped"])

    def test_change_with_status_and_gate(self):
        git(self.d, "checkout", "-q", "-b", "feature/SHOP-12-add-discount-code")
        ch = "openspec/changes/SHOP-12-add-discount/"
        write(self.d, ch + "status.md", 'slice: S1\nnext: run /gate done "now"\n')
        write(self.d, ch + "gates-ready.json", {"stage": "ready", "pass": True})
        rc, s = self.state(self.d)
        self.assertEqual(s["ticket"], "SHOP-12")
        self.assertEqual(s["change"], "SHOP-12-add-discount")
        self.assertTrue(s["change_exists"])
        self.assertEqual(s["next"], 'run /gate done "now"')
        self.assertEqual(s["last_gate"], {"stage": "ready", "pass": True})

    def test_not_a_repo(self):
        rc, s = self.state(tempfile.mkdtemp())
        self.assertIsNone(s["branch"])


if __name__ == "__main__":
    unittest.main()
````
