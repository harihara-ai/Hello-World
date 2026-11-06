purpose: working source for the kit's own tests (T1 unit, T2 contract, T3 mutation); run by forge selftest.

# Tests

Not kit components, so not in the manifest. `tests/run.sh` runs all three levels.

## tests/unit/test_policy_guard.py

````python file=tests/unit/test_policy_guard.py
"""purpose: T1 fixtures for gate policy_guard (no loosening of the floor without sign-off, trap 12)."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import *  # noqa: E402,F403



class PolicyGuard(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        with open(FLOOR) as fh:
            self.floor = fh.read()

    def guard(self, new_text, signoff=None, baselines=None):
        new = write(self.d, "policy.yml", new_text)
        payload = {"old": FLOOR, "new": new}
        if baselines:
            payload["baselines"] = [write(self.d, "base%d.yml" % i, t) for i, t in enumerate(baselines)]
        if signoff is not None:
            payload["signoff"] = write(self.d, "signoff.json", signoff)
        return run_gate("policy_guard", payload)

    def test_same_policy_passes(self):
        rc, _, log = self.guard(self.floor)
        self.assertEqual(rc, 0, log)

    def test_raising_passes(self):
        rc, _, log = self.guard(self.floor.replace("min_changed_line_coverage: 80", "min_changed_line_coverage: 90"))
        self.assertEqual(rc, 0, log)

    def test_lowering_min_fails(self):
        rc, out, _ = self.guard(self.floor.replace("min_changed_line_coverage: 80", "min_changed_line_coverage: 50"))
        self.assertEqual(rc, 1)
        self.assertIn("min_changed_line_coverage", str(out["findings"]))

    def test_raising_max_fails(self):
        rc, _, _ = self.guard(self.floor.replace("max_task_attempts: 3", "max_task_attempts: 9"))
        self.assertEqual(rc, 1)

    def test_removing_gate_or_word_fails(self):
        self.assertEqual(self.guard(self.floor.replace("trace_check, ", ""))[0], 1)
        self.assertEqual(self.guard(self.floor.replace("fast, ", ""))[0], 1)

    def test_removing_key_fails(self):
        lines = [l for l in self.floor.splitlines() if not l.startswith("max_task_attempts")]
        self.assertEqual(self.guard("\n".join(lines) + "\n")[0], 1)

    def test_signoff_allows_named_key_at_named_value(self):
        low = self.floor.replace("min_changed_line_coverage: 80", "min_changed_line_coverage: 50")
        ok = {"approved_by": "Dana Lee", "reason": "legacy module, see ADR-7", "keys": {"min_changed_line_coverage": 50}}
        self.assertEqual(self.guard(low, ok)[0], 0)
        self.assertEqual(self.guard(low, dict(ok, keys={"other": 1}))[0], 1)
        self.assertEqual(self.guard(low, dict(ok, keys={"min_changed_line_coverage": 60}))[0], 1)
        self.assertEqual(self.guard(low, dict(ok, keys=["min_changed_line_coverage"]))[0], 1)
        self.assertEqual(self.guard(low, dict(ok, approved_by=""))[0], 1)
        self.assertEqual(self.guard(low, dict(ok, reason=""))[0], 1)

    def test_raised_repo_floor_cannot_be_lowered_back(self):
        raised = self.floor.replace("min_changed_line_coverage: 80", "min_changed_line_coverage: 95")
        rc, out, _ = self.guard(self.floor, baselines=[raised])
        self.assertEqual(rc, 1)
        self.assertIn("min_changed_line_coverage", str(out["findings"]))
        self.assertEqual(self.guard(raised, baselines=[raised])[0], 0)

    def test_unparseable_policy_fails(self):
        self.assertEqual(self.guard("min_x: [unclosed\n")[0], 1)


if __name__ == "__main__":
    unittest.main()
````

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


if __name__ == "__main__":
    unittest.main()
````
