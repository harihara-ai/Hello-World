purpose: working source for the kit's own tests (T1 unit, T2 contract, T3 mutation); run by forge selftest.

# Tests

Not kit components, so not in the manifest. `tests/run.sh` runs all three levels.

## tests/unit/test_probe.py

````python file=tests/unit/test_probe.py
"""purpose: T1 fixtures for probe.py (ranked fallbacks, trap 10)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403



def probe(results, needed=None, args=()):
    payload = {"results": results}
    if needed:
        payload["capabilities"] = needed
    return run_py(os.path.join(KIT, "scripts", "probe.py"), payload, ["-", *args])


class Probe(unittest.TestCase):
    def test_default_chosen_when_ok(self):
        rc, out, log = probe({"serena": {"ok": True}, "ctags": {"ok": True}}, ["codenav"])
        self.assertEqual(rc, 0, log)
        self.assertEqual(out["capabilities"]["codenav"]["chosen"], "serena")

    def test_fallback_when_no_language_server(self):
        rc, out, _ = probe({"serena": {"ok": False, "reason": "no language server for Delphi"},
                            "ctags": {"ok": True}}, ["codenav"])
        c = out["capabilities"]["codenav"]
        self.assertEqual(c["chosen"], "ctags")
        self.assertIn("no language server for Delphi", str(c["rejected"]))

    def test_nothing_works_asks(self):
        rc, out, _ = probe({"serena": {"ok": False}}, ["codenav"])
        self.assertEqual(rc, 1)
        self.assertIsNone(out["capabilities"]["codenav"]["chosen"])

    def test_writes_toolchain_md(self):
        d = tempfile.mkdtemp()
        out_md = os.path.join(d, "toolchain.md")
        rc, _, log = probe({"serena": {"ok": False, "reason": "crash"}, "ctags": {"ok": True}}, ["codenav"], ["--out", out_md])
        self.assertEqual(rc, 0, log)
        with open(out_md) as fh:
            text = fh.read()
        self.assertIn("purpose:", text)
        self.assertIn("ctags", text)
        self.assertIn("crash", text)

    def test_tracker_ranks_adapters(self):
        rc, out, _ = probe({"jira": {"ok": False, "reason": "403 no write"}, "file": {"ok": True}}, ["tracker"])
        self.assertEqual(out["capabilities"]["tracker"]["chosen"], "file")

    def test_tools_without_adapter_are_unknown(self):
        self.assertEqual(probe({}, ["repomap"])[0], 2)

    def test_unknown_capability_usage_error(self):
        self.assertEqual(probe({}, ["teleport"])[0], 2)


if __name__ == "__main__":
    unittest.main()
````

## tests/unit/test_red_check.py

````python file=tests/unit/test_red_check.py
"""purpose: T1 fixtures for gate red_check (changed tests must detect the change; spec 10.4 #1; H05)."""
import json
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

    def test_behaviour_change_with_new_test_is_red_then_green(self):
        write(self.d, "src/m.py", "def f():\n    return 2\n")
        write(self.d, "tests/test_m.py", TEST % 2)
        rc, out, log = self.red()
        self.assertEqual(rc, 0, log)

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

    def test_failing_on_head_fails(self):
        write(self.d, "tests/test_m.py", TEST % 3)
        rc, out, _ = self.red()
        self.assertIn("tests_fail_on_head", rules(out))

    def test_refactor_tests_must_pass_on_base(self):
        write(self.d, "src/m.py", "def f():\n    x = 1\n    return x\n")
        write(self.d, "tests/test_m2.py", (TEST % 1).replace("test_f", "test_char"))
        self.assertEqual(self.red("refactor")[0], 0)
        write(self.d, "src/m.py", "def f():\n    return 2\n")
        write(self.d, "tests/test_m2.py", (TEST % 2).replace("test_f", "test_char"))
        rc, out, _ = self.red("refactor")
        self.assertIn("behaviour_changed", rules(out))

    def test_missing_test_command_fails(self):
        write(self.d, "tests/test_m.py", TEST % 1 + "# more\n")
        rc, out, _ = run_gate("red_check", {"base": self.base, "type": "story"}, cwd=self.d)
        self.assertIn("no_test_cmd", rules(out))

    def test_spike_has_nothing_to_check(self):
        self.assertEqual(self.red("spike")[0], 0)

    def test_base_worktree_is_removed(self):
        write(self.d, "src/m.py", "def f():\n    return 2\n")
        write(self.d, "tests/test_m.py", TEST % 2)
        self.red()
        self.assertEqual(git(self.d, "worktree", "list").strip().count("\n"), 0)


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
