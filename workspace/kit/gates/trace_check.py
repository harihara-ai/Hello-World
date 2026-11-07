#!/usr/bin/env python3
"""purpose: every REQ ID in the change's spec appears in at least one test file (traceability, G3 check 6).

Input: {"spec_dirs": [change folder]}. Test files are found by the fixed test globs (kitconst), never by input,
so an ID in production code or docs does not count. REQ-AREA-001, REQ_AREA_001 and Req_Area_001 are one ID.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402
from kitconst import SKIP_DIRS, is_test_file  # noqa: E402

SPEC_ID = re.compile(r"REQ-[A-Z0-9]+-[0-9]+")
TEST_ID = re.compile(r"(?<![A-Za-z0-9])REQ[-_]([A-Za-z0-9]+?)[-_]([0-9]+)(?![0-9])", re.I)


def norm(area, num):
    return "REQ-%s-%03d" % (area.upper(), int(num))


def spec_ids(dirs):
    found = set()
    for d in dirs:
        for root, _d, files in os.walk(d):
            for name in files:
                if name.endswith(".md"):
                    with open(os.path.join(root, name), encoding="utf-8", errors="ignore") as fh:
                        found |= {norm(*i.split("-")[1:]) for i in SPEC_ID.findall(fh.read())}
    return found


def test_ids():
    found, n = set(), 0
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), ".").replace(os.sep, "/")
            if not is_test_file(rel):
                continue
            n += 1
            with open(rel, encoding="utf-8", errors="ignore") as fh:
                found |= {norm(a, b) for a, b in TEST_ID.findall(fh.read())}
    return found, n


def check(p):
    ids = spec_ids([d for d in p.get("spec_dirs", []) if os.path.isdir(d)])
    if not ids:
        return [finding("no_ids", "no REQ IDs found in %s" % p.get("spec_dirs"))], {}
    tested, n = test_ids()
    if not n:
        return [finding("no_test_files", "no test files found (see kitconst.TEST_GLOBS)")], {}
    f = [finding("untested", "%s has no test" % i, i) for i in sorted(ids - tested)]
    f += [finding("orphan_id", "tests mention %s, which is in no spec here" % i, i, "warn") for i in sorted(tested - ids)]
    return f, {"requirements": sorted(ids)}


if __name__ == "__main__":
    sys.exit(run("trace_check", check))
