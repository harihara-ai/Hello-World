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
