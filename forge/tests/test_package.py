"""purpose: T1 tests for forge.sh package: the full package and the install zip with repo-root paths (G24)."""
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        for p in ("forge", "proposal/modules", "workspace", "package"):
            shutil.copytree(os.path.join(ROOT, p), os.path.join(cls.d, p),
                            ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(os.path.join(ROOT, "kit.lock"), cls.d)
        cls.p = subprocess.run(["bash", "forge/forge.sh", "package"], cwd=cls.d, capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.d, ignore_errors=True)

    def names(self, zname):
        with zipfile.ZipFile(os.path.join(self.d, "dist", zname)) as z:
            return z.namelist()

    def test_package_builds(self):
        self.assertEqual(self.p.returncode, 0, self.p.stdout + self.p.stderr)

    def test_full_package_kept(self):
        names = self.names("northstar-kit.zip")
        self.assertIn("workspace/kit/INSTALL.md", names)
        self.assertIn("kit.lock", names)

    def test_install_zip_has_repo_root_paths_only(self):
        names = self.names("northstar-kit-install.zip")
        for n in ("kit/CLAUDE.md", "kit/INSTALL.md", "kit.manifest.yml", ".claude/commands/bootstrap.md"):
            self.assertIn(n, names)
        for n in names:
            self.assertTrue(n == "kit.manifest.yml" or n.startswith(("kit/", ".claude/commands/")), n)
            self.assertNotIn("__pycache__", n)

    def test_install_zip_never_holds_a_root_claude_md(self):
        names = self.names("northstar-kit-install.zip")
        self.assertFalse([n for n in names if n.lower() == "claude.md"])

    def test_install_zip_matches_workspace_and_lock(self):
        ws = os.path.join(self.d, "workspace")
        with open(os.path.join(self.d, "kit.lock")) as fh:
            locked = {ln.split()[1] for ln in fh if ln.strip() and not ln.startswith("#")}
        with zipfile.ZipFile(os.path.join(self.d, "dist", "northstar-kit-install.zip")) as z:
            for n in z.namelist():
                src = n.replace(".claude/commands/", "kit/.claude/commands/", 1) if n.startswith(".claude/") else n
                self.assertIn(src, locked, n)
                with open(os.path.join(ws, src), "rb") as fh:
                    self.assertEqual(z.read(n), fh.read(), n)
        cmds = os.listdir(os.path.join(ws, "kit/.claude/commands"))
        self.assertEqual(sorted(".claude/commands/" + c for c in cmds),
                         sorted(n for n in self.names("northstar-kit-install.zip") if n.startswith(".claude/")))


if __name__ == "__main__":
    unittest.main()
