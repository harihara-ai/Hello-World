"""purpose: tests for run_traps.py: every seeded trap is scored, the clean changes pass, and a broken kit is caught."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RUNNER = os.path.join(HERE, "run_traps.py")
WS = os.path.join(ROOT, "workspace")


def run(kit=WS):
    p = subprocess.run([sys.executable, "-I", "-B", RUNNER, "--kit", kit, "--json"], capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout), p.stderr


class RunTraps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rc, cls.out, cls.err = run()

    def test_all_traps_from_traps_md_are_covered(self):
        with open(os.path.join(HERE, "TRAPS.md")) as fh:
            listed = {int(n) for n in re.findall(r"(?m)^\| (\d+) \|", fh.read())}
        self.assertEqual(listed, {c["trap"] for c in self.out["cases"]})

    def test_both_repos_used_and_each_has_a_clean_change(self):
        repos = {c["repo"] for c in self.out["cases"]}
        self.assertEqual(repos, {"legacy-app", "modern-app"})
        for r in repos:
            self.assertTrue(any(c["repo"] == r and c["trap"] == 13 for c in self.out["cases"]), r)

    def test_current_kit_blocks_every_trap(self):
        missed = [c for c in self.out["cases"] if not c["ok"]]
        self.assertEqual(missed, [], self.err)
        self.assertEqual(self.rc, 0)
        self.assertEqual(self.out["score"]["false_alarms"], 0)

    def test_rules_are_checked_not_only_gates(self):
        self.assertTrue(any("expect_rules" in json.load(open(c)) for c in
                            __import__("glob").glob(os.path.join(HERE, "cases", "*", "*", "case.json"))))

    def test_git_mode_is_used(self):
        clean = [c for c in self.out["cases"] if c["trap"] == 13]
        self.assertTrue(all("git" in c["detail"] for c in clean), clean)

    def test_broken_kit_is_caught(self):
        kit = os.path.join(tempfile.mkdtemp(), "ws")
        shutil.copytree(WS, kit)
        gate = os.path.join(kit, "kit/gates/injection.py")
        with open(gate) as fh:
            src = fh.read()
        with open(gate, "w") as fh:
            fh.write(src.replace('if __name__ == "__main__":', 'PATTERNS.clear()\n\nif __name__ == "__main__":'))
        rc, out, _ = run(kit)
        self.assertEqual(rc, 1)
        missed = {c["trap"] for c in out["cases"] if not c["ok"]}
        self.assertIn(4, missed)
        self.assertLess(out["score"]["critical_blocked"], out["score"]["critical_total"])


if __name__ == "__main__":
    unittest.main()
