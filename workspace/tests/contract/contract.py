"""purpose: shared T2 contract suite: every adapter covers every operation and error of its capability."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import WS  # noqa: E402


def read(rel):
    with open(os.path.join(WS, rel)) as fh:
        return fh.read()


def manifest():
    items, cur = [], None
    for line in read("kit.manifest.yml").splitlines():
        m = re.match(r"^(-\s+|\s+)(\w+):\s*(.*)$", line)
        if not m:
            continue
        if m.group(1).startswith("-"):
            cur = {}
            items.append(cur)
        cur[m.group(2)] = m.group(3).strip()
    return items


def section_names(text, heading):
    m = re.search(r"^## %s\s*$(.*?)(?=^## |\Z)" % heading, text, re.M | re.S)
    return re.findall(r"^- `(\w+)`", m.group(1), re.M) if m else []


def check(case, capability_id):
    comps = manifest()
    cap = next(c for c in comps if c["id"] == capability_id)
    ctext = read(cap["path"])
    ops, errs = section_names(ctext, "Operations"), section_names(ctext, "Errors")
    case.assertTrue(ops, "capability lists no operations")
    case.assertTrue(errs, "capability lists no errors")
    adapters = [c for c in comps if c.get("implements") == capability_id]
    case.assertGreaterEqual(len(adapters), 2, "need a default and a fallback adapter")
    for a in adapters:
        text = read(a["path"])
        for name in ops + errs:
            case.assertIn("`%s`" % name, text, "%s does not cover %s" % (a["id"], name))
        case.assertRegex(text, r"(?m)^## Probe", "%s has no probe section" % a["id"])
    return adapters
