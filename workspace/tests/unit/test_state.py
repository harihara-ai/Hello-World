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
        git(self.d, "checkout", "-q", "-b", "feature/SHOP-12-add-discount")
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
