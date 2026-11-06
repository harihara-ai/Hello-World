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
    return run_py(gate_path(name), payload, ["-"], cwd)


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
def test_discount():
    pass
"""


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
    write(root, "src/discount.py", "def price(t):\n    return t\n")
    write(root, "tests/test_discount.py", CLEAN_TEST)
    return root, ch


def gate_check(root, ch, stage, *extra):
    return run_py(os.path.join(KIT, "scripts", "gate_check.py"), None,
                  [stage, "--repo", root, "--change", ch, *extra])
