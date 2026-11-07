"""purpose: T1 unit tests for tangle.py and kit_lint.py. Run: python3 -m unittest discover -s forge/tests"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FORGE = os.path.dirname(HERE)
TANGLE = os.path.join(FORGE, "tangle.py")
LINT = os.path.join(FORGE, "kit_lint.py")


def run(*args):
    p = subprocess.run([sys.executable, "-I", *args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def block(path, body="hello", fence="```"):
    return "%s md file=%s\n%s\n%s\n" % (fence, path, body, fence)


class TangleTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.src = os.path.join(self.d, "src.md")
        self.lock = os.path.join(self.d, "kit.lock")
        self.out = os.path.join(self.d, "ws")

    def write(self, text):
        with open(self.src, "w") as fh:
            fh.write(text)

    def pin(self, *extra):
        return run(TANGLE, self.src, self.lock, self.out, "--pin", *extra)

    def tangle(self, *extra):
        return run(TANGLE, self.src, self.lock, self.out, *extra)

    def test_good_flow(self):
        self.write("text\n" + block("kit/core/a.md", "purpose: a"))
        self.assertEqual(self.pin()[0], 0)
        rc, out = self.tangle()
        self.assertEqual(rc, 0, out)
        self.assertTrue(os.path.isfile(os.path.join(self.out, "kit/core/a.md")))

    def test_unpinned_refused(self):
        self.write(block("kit/a.md"))
        rc, out = self.tangle()
        self.assertEqual(rc, 1)
        self.assertIn("unpinned", out)
        self.assertFalse(os.path.exists(self.out))

    def test_changed_after_pin_refused(self):
        self.write(block("kit/a.md", "one"))
        self.pin()
        self.write(block("kit/a.md", "two"))
        rc, out = self.tangle()
        self.assertEqual(rc, 1)
        self.assertIn("changed since pin", out)

    def test_traversal_and_absolute_refused(self):
        for bad in ("../evil.md", "/etc/x.md", "kit/../../x.md", "C:/x.md", "kit\\x.md"):
            self.write(block(bad))
            rc, _ = self.pin()
            self.assertEqual(rc, 1, bad)

    def test_extension_allowlist(self):
        for bad in ("kit/a.exe", "kit/a.bat", "kit/a"):
            self.write(block(bad))
            self.assertEqual(self.pin()[0], 1, bad)

    def test_high_risk_needs_flag(self):
        self.write(block(".claude/settings.json", "{}"))
        self.assertEqual(self.pin()[0], 1)
        self.assertEqual(self.pin("--approve-high-risk")[0], 0)

    def test_duplicate_path_refused(self):
        self.write(block("kit/a.md", "1") + block("kit/a.md", "2"))
        self.assertEqual(self.pin()[0], 1)

    def test_blocks_without_file_are_ignored(self):
        self.write("```bash\nrm -rf /\n```\n" + block("kit/a.md"))
        self.assertEqual(self.pin()[0], 0)
        self.assertEqual(self.tangle()[0], 0)
        self.assertEqual(len(os.listdir(os.path.join(self.out, "kit"))), 1)

    def test_directory_source(self):
        os.makedirs(os.path.join(self.d, "mods"))
        with open(os.path.join(self.d, "mods", "m.md"), "w") as fh:
            fh.write(block("kit/b.md"))
        rc, _ = run(TANGLE, os.path.join(self.d, "mods"), self.lock, self.out, "--pin")
        self.assertEqual(rc, 0)

    def test_symlink_in_workspace_refused(self):
        self.write(block("kit/a.md"))
        self.pin()
        os.makedirs(self.out)
        os.symlink(self.d, os.path.join(self.out, "kit"))
        rc, out = self.tangle()
        self.assertEqual(rc, 1, out)

    def test_nested_high_risk_needs_flag(self):
        for path in ("kit/.claude/settings.json", "kit/hooks/pre-commit.sh", "kit/.github/workflows/ci.yml",
                     "kit/.mcp.json", "tests/conftest.py", ".vscode/tasks.json", "kit/.husky/pre-push.sh"):
            self.write(block(path, "{}"))
            rc, out = self.pin()
            self.assertEqual(rc, 1, path)
            self.assertIn("high-risk", out)
            rc, out = self.pin("--approve-high-risk")
            self.assertEqual(rc, 0, path)
            self.assertIn("HIGH-RISK", out)

    def test_fence_inside_html_comment_ignored(self):
        self.write("<!--\n" + block("kit/hidden.sh", "echo hi") + "-->\n" + block("kit/a.md"))
        rc, out = self.pin()
        self.assertEqual(rc, 0, out)
        self.assertNotIn("kit/hidden.sh", open(self.lock).read())

    def test_check_detects_workspace_tampering(self):
        self.write(block("kit/a.md", "purpose: a"))
        self.pin()
        self.assertEqual(self.tangle()[0], 0)
        self.assertEqual(self.tangle("--check")[0], 0)
        os.makedirs(os.path.join(self.out, "kit", "__pycache__"))
        with open(os.path.join(self.out, "kit", "__pycache__", "x.pyc"), "w") as fh:
            fh.write("ignored")
        self.assertEqual(self.tangle("--check")[0], 0)
        with open(os.path.join(self.out, "kit", "a.md"), "a") as fh:
            fh.write("edited by hand\n")
        rc, out = self.tangle("--check")
        self.assertEqual(rc, 1)
        self.assertIn("workspace file changed", out)
        self.tangle()
        with open(os.path.join(self.out, "kit", "planted.py"), "w") as fh:
            fh.write("x = 1\n")
        rc, out = self.tangle("--check")
        self.assertEqual(rc, 1)
        self.assertIn("not in lock", out)

    def test_agent_steering_files_are_high_risk(self):
        for path in ("kit/.claude/commands/genie.md", "kit/CLAUDE.md", "kit/sub/CLAUDE.md"):
            self.write(block(path, "x"))
            rc, out = self.pin()
            self.assertEqual(rc, 1, path)

    def test_fence_after_reopened_comment_ignored(self):
        self.write("<!-- a --> text <!--\n" + block("kit/hidden.sh", "echo hi") + "-->\n" + block("kit/a.md"))
        rc, out = self.pin()
        self.assertEqual(rc, 0, out)
        self.assertNotIn("kit/hidden.sh", open(self.lock).read())

    def test_check_hashes_bytes(self):
        self.write(block("kit/a.sh", "set -e\necho ok"))
        self.pin()
        self.tangle()
        p = os.path.join(self.out, "kit", "a.sh")
        with open(p, "rb") as fh:
            raw = fh.read()
        with open(p, "wb") as fh:
            fh.write(raw.replace(b"\n", b"\r", 1))
        rc, out = self.tangle("--check")
        self.assertEqual(rc, 1, out)


MANIFEST_OK = """\
- id: core.glossary
  type: core
  path: kit/core/glossary.md
- id: cap.tracker
  type: capability
  path: kit/cap/tracker.md
  needs: [core.glossary]
- id: adapter.jira
  type: adapter
  path: kit/adapters/jira.md
  implements: cap.tracker
  needs: [core.glossary]
  tests: [tests/jira.md]
- id: play.story
  type: playbook
  path: kit/play/story.md
  needs: [cap.tracker, core.glossary]
"""


class LintTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.mf = os.path.join(self.d, "kit.manifest.yml")

    def put(self, rel, text):
        p = os.path.join(self.d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            fh.write(text)

    def base(self, manifest=MANIFEST_OK):
        self.put("kit.manifest.yml", manifest)
        for rel in ("kit/core/glossary.md", "kit/cap/tracker.md", "kit/adapters/jira.md", "kit/play/story.md"):
            self.put(rel, "purpose: %s\nshort\n" % rel)

    def lint(self):
        return run(LINT, self.d, self.mf)

    def test_clean(self):
        self.base()
        rc, out = self.lint()
        self.assertEqual(rc, 0, out)

    def test_oversize(self):
        self.base()
        self.put("kit/play/story.md", "purpose: x\n" + "line\n" * 130)
        rc, out = self.lint()
        self.assertEqual(rc, 1)
        self.assertIn("exceeds cap", out)

    def test_orphan(self):
        self.base()
        self.put("kit/extra.md", "purpose: x\n")
        rc, out = self.lint()
        self.assertEqual(rc, 1)
        self.assertIn("orphan", out)

    def test_missing_purpose(self):
        self.base()
        self.put("kit/core/glossary.md", "no header here\n")
        rc, out = self.lint()
        self.assertEqual(rc, 1)
        self.assertIn("purpose", out)

    def test_upward_dependency(self):
        changed = MANIFEST_OK.replace("  path: kit/core/glossary.md\n",
                                      "  path: kit/core/glossary.md\n  needs: [play.story]\n", 1)
        self.assertNotEqual(changed, MANIFEST_OK)
        self.base(changed)
        rc, out = self.lint()
        self.assertEqual(rc, 1)
        self.assertIn("upward", out)

    def test_depend_on_adapter_refused(self):
        self.base(MANIFEST_OK.replace("needs: [cap.tracker, core.glossary]",
                                      "needs: [adapter.jira, core.glossary]"))
        rc, out = self.lint()
        self.assertEqual(rc, 1)
        self.assertIn("adapter", out)

    def test_adapter_without_tests(self):
        self.base(MANIFEST_OK.replace("  tests: [tests/jira.md]\n", ""))
        rc, out = self.lint()
        self.assertEqual(rc, 1)
        self.assertIn("contract tests", out)

    def test_duplicate_paragraph(self):
        self.base()
        para = "This paragraph is long enough to count as shared text that should live in core. " * 4
        self.put("kit/play/story.md", "purpose: x\n\n" + para + "\n")
        self.put("kit/cap/tracker.md", "purpose: y\n\n" + para + "\n")
        rc, out = self.lint()
        self.assertEqual(rc, 1)
        self.assertIn("duplicated paragraph", out)


if __name__ == "__main__":
    unittest.main()
