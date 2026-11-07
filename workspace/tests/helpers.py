"""purpose: shared test helpers: run gates and scripts, build a clean fixture change."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

TESTS = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(TESTS)
KIT = os.path.join(WS, "kit")
FLOOR = os.path.join(KIT, "core", "policy.yml")


def gate_path(name):
    return os.path.join(KIT, "gates", name + ".py")


def run_py(path, payload=None, args=(), cwd=None):
    data = json.dumps(payload) if payload is not None else None
    p = subprocess.run([sys.executable, "-I", "-B", path, *args], input=data,
                       capture_output=True, text=True, cwd=cwd)
    try:
        out = json.loads(p.stdout)
    except ValueError:
        out = None
    return p.returncode, out, p.stdout + p.stderr


def run_gate(name, payload, cwd=None):
    """cwd defaults to a fresh non-git temp dir so a gate never sees the repo the tests live in."""
    return run_py(gate_path(name), payload, ["-"], cwd or tempfile.mkdtemp())


def rules(out):
    return {f["rule"] for f in out["findings"]}


CLEAN_SPEC = """# Change: add-discount
Ticket: SHOP-12
Type: story

## Problem
Loyal customers pay full price.

## Outcome
Orders of 100.00 or more get a 10 percent discount.

## Requirements

### REQ-DISC-001: Apply 10 percent discount at 100.00
Scenario: happy - order of 100.00 gets discount
  Given an order total of 100.00
  When the total is priced
  Then the price is 90.00
  Level: unit
Scenario: error - negative total rejected
  Given an order total of -1.00
  When the total is priced
  Then a ValueError is raised
  Level: unit

### REQ-DISC-002: No discount below 100.00
Errors: none
Scenario: happy - order of 99.99 pays full price
  Given an order total of 99.99
  When the total is priced
  Then the price is 99.99
  Level: unit

## Non-functional
none

## Out of scope
Coupons.

## Assumptions
Totals are in one currency.

## Open questions
none
"""

CLEAN_TEST = """# REQ-DISC-001 REQ-DISC-002
import os
import sys
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from discount import price  # noqa: E402


class Discount(unittest.TestCase):
    def test_REQ_DISC_001_ten_percent_at_100(self):
        self.assertEqual(price(100.0), 90.0)

    def test_REQ_DISC_002_none_below_100(self):
        self.assertEqual(price(99.99), 99.99)
"""
CLEAN_SRC = "def price(t):\n    return round(t * 0.9, 2) if t >= 100 else t\n"
TEST_CMD = "%s -I -B -m unittest discover -s tests" % sys.executable


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text if isinstance(text, str) else json.dumps(text))
    return path


def make_repo():
    """A repo with one clean change that passes gate_check ready and done."""
    root = tempfile.mkdtemp()
    ch = "openspec/changes/add-discount"
    os.makedirs(os.path.join(root, "docs/ai"))
    shutil.copy(FLOOR, os.path.join(root, "docs/ai/policy.yml"))
    write(root, ch + "/spec.md", CLEAN_SPEC)
    write(root, ch + "/ticket.md", "SHOP-12: give loyal customers 10 percent off orders of 100.00 or more.\n")
    write(root, ch + "/inputs/granularity.json", {"slices": [
        {"id": "S1", "title": "Discount at 100.00", "scenarios": 3, "modules": 1, "contracts": 0,
         "symbols": 2, "lines": 40, "files": 2, "untested": "none", "testable": "yes"}]})
    write(root, ch + "/inputs/coverage.json", {
        "changed_lines": {"src/discount.py": [1, 2, 3, 4]},
        "covered_lines": {"src/discount.py": [1, 2, 3, 4]},
        "baseline_total": 70.0, "current_total": 71.0})
    write(root, ch + "/inputs/diff_scope.json", {
        "changed_files": ["src/discount.py", "tests/test_discount.py"],
        "impact_scan": ["src/discount.py", "tests/*"]})
    write(root, "src/discount.py", CLEAN_SRC)
    write(root, "tests/test_discount.py", CLEAN_TEST)
    return root, ch


def gate_check(root, ch, stage, *extra):
    return run_py(os.path.join(KIT, "scripts", "gate_check.py"), None,
                  [stage, "--repo", root, "--change", ch, *extra])


def git(root, *args):
    p = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr)
    return p.stdout


def git_init(root):
    """Turn a fixture dir into a git repo with everything committed on main."""
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@t")
    git(root, "config", "user.name", "t")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "base")
    return root


def cobertura(files, rate=0.9):
    """files: {path: {line: hits}} -> Cobertura XML text."""
    classes = "".join('<class filename="%s"><lines>%s</lines></class>' % (
        f, "".join('<line number="%d" hits="%d"/>' % (n, h) for n, h in sorted(lines.items())))
        for f, lines in files.items())
    return '<?xml version="1.0"?><coverage line-rate="%s"><packages><package><classes>%s</classes></package></packages></coverage>' % (rate, classes)


def write_tree(files):
    root = tempfile.mkdtemp()
    for rel, text in files.items():
        write(root, rel, text)
    return root


def git_change():
    """A git repo whose base commit holds the approved plan; the code change (src, tests) is uncommitted on top.
    Returns (root, change, base sha, coverage report path outside the repo)."""
    root, ch = make_repo()
    aside = tempfile.mkdtemp()
    for d in ("src", "tests"):
        shutil.move(os.path.join(root, d), os.path.join(aside, d))
    git_init(root)
    base = git(root, "rev-parse", "HEAD").strip()
    for d in ("src", "tests"):
        shutil.move(os.path.join(aside, d), os.path.join(root, d))
    write(root, ch + "/evidence.md", "RED then GREEN recorded by /implement\n")
    report = write(tempfile.mkdtemp(), "coverage.xml", cobertura({"src/discount.py": {1: 1, 2: 1}}, rate=0.72))
    return root, ch, base, report


def ci_args(base, report, *extra):
    baseline = write(tempfile.mkdtemp(), "base.xml", cobertura({}, rate=0.70))
    return ["--base", base, "--coverage-report", report, "--baseline-report", baseline, "--test-cmd", TEST_CMD, *extra]
