#!/usr/bin/env python3
"""purpose: flag hostile instructions in ticket, spec, comment, tool output or file-name text (data, not orders).

Input: {"texts": [{"source": "...", "text": "..."}]}. Output: gate JSON; any match fails.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402

TARGET = r"(the |all |any |previous |prior |above )*(gates?|rules|instructions|tests?|checks?|policy|guardrails|review|hooks?|ci|coverage|lint)"
PATTERNS = [
    ("ignore instructions", r"\b(ignore|disregard|forget)\b.{0,20}\b" + TARGET + r"\b"),
    ("disable a control", r"\b(skip|bypass|disable|turn off|switch off|remove|comment out)\b\s+" + TARGET + r"\b"),
    ("role hijack", r"\byou are now\b|\b(system|developer) prompt\b|\bnew instructions\b"),
    ("unsafe git", r"--no-verify|\bforce[- ]push\b"),
    ("merge unchecked", r"\bmerge\b.{0,20}\bwithout\b.{0,15}\b(review|approval|tests?|checks?)\b"),
    ("lower the floor", r"\b(lower|reduce|drop)\b.{0,20}\b(coverage|threshold|floor)\b"),
    ("self approval", r"\bapprove (it|this|the pr) yourself\b|\bauto-?approve\b"),
]


def normal(text):
    return re.sub(r"[_\s]+", " ", text).lower()


def check(p):
    f = []
    for item in p.get("texts", []):
        t = normal(str(item.get("text", "")))
        for label, pat in PATTERNS:
            m = re.search(pat, t)
            if m:
                f.append(finding("injection", "%s: '%s' (treated as data, ignored)" % (label, m.group(0)[:80]),
                                 str(item.get("source", "?"))))
    return f, {}


if __name__ == "__main__":
    sys.exit(run("injection", check))
