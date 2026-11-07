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
