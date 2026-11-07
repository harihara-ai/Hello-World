#!/usr/bin/env python3
"""purpose: score each slice green, amber or red (section 11.3); any red or two ambers means split.

A slice with "kind": "characterization" (Slice 0) is not held to the size limits: it only pins behaviour.

Input: {"slices": [{id, title, scenarios, modules, contracts, symbols, lines, files, untested, testable}],
        "policy": {max_slice_<measure>: [green_max, amber_max]}}. Output: gate JSON plus per-slice scores.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402

DEFAULTS = {"scenarios": [3, 5], "modules": [1, 2], "contracts": [0, 1],
            "symbols": [8, 15], "lines": [150, 300], "files": [8, 15]}
UNTESTED = {"none": "green", "characterized": "amber"}
TESTABLE = {"yes": "green", "stub": "amber"}


SIZE_ONLY = ("lines", "symbols", "files")


def score(s, pol, has_slice0=False):
    reasons, char = [], s.get("kind") == "characterization"
    for m, default in DEFAULTS.items():
        if char and m in SIZE_ONLY:
            continue
        green, amber = pol.get("max_slice_" + m, default)
        v = s.get(m)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            reasons.append(("red", "%s missing" % m))
        elif v > amber:
            reasons.append(("red", "%s %s > %s" % (m, v, amber)))
        elif v > green:
            reasons.append(("amber", "%s %s > %s" % (m, v, green)))
    u = "green" if char or (has_slice0 and s.get("untested") == "characterized") else UNTESTED.get(s.get("untested"), "red")
    if u != "green":
        reasons.append((u, "untested code: %s (characterization slice must come first)" % s.get("untested")))
    t = TESTABLE.get(s.get("testable"), "red")
    if t != "green":
        reasons.append((t, "independently testable: %s" % s.get("testable")))
    if re.search(r"\b(and|or)\b", str(s.get("title", "")), re.I):
        reasons.append(("amber", "title has 'and'/'or': check for a hidden second requirement"))
    levels = [lvl for lvl, _ in reasons]
    overall = "red" if "red" in levels else "amber" if levels else "green"
    split = overall == "red" or levels.count("amber") >= 2
    return overall, split, [msg for _, msg in reasons]


def check(p):
    slices, pol = p.get("slices", []), p.get("policy", {})
    if not slices:
        return [finding("no_slices", "no slice plan given")], {"slices": []}
    f, out = [], []
    has_slice0 = any(s.get("kind") == "characterization" for s in slices)
    for s in slices:
        overall, split, reasons = score(s, pol, has_slice0)
        out.append({"id": s.get("id"), "score": overall, "reasons": reasons})
        if split:
            f.append(finding("split", "split this slice: " + "; ".join(reasons), str(s.get("id"))))
        elif overall == "amber":
            f.append(finding("review", "amber: " + "; ".join(reasons), str(s.get("id")), "warn"))
    return f, {"slices": out}


if __name__ == "__main__":
    sys.exit(run("granularity", check))
