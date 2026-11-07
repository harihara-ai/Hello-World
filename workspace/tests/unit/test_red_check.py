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
