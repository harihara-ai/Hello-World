#!/usr/bin/env python3
"""purpose: tripwire for hostile instructions in tickets, specs, comments, tool output and file names.

Input: {"texts": [{"source": "...", "text": "...", "kind": "data"|"authored"}]}. Matches in fetched data
(kind "data") are flagged as warnings and ignored; matches in AI-authored text fail. A regex cannot catch every
paraphrase, so the AI review stays the main control (core.rules rule 1).
"""
import unicodedata
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402

TARGET = (r"(the |all |any |previous |prior |above |earlier |failing )*(gates?|rules|instructions|guidance|"
          r"tests?|checks?|policy|guardrails|review|hooks?|ci|coverage|lint|assertions?)")
PATTERNS = [
    ("ignore instructions", r"\b(ignore|disregard|forget|pay no attention to)\b.{0,20}\b" + TARGET + r"\b"),
    ("disable a control", r"\b(skip|bypass|disable|turn off|switch off|remove|delete|weaken|comment out)\b\s+" + TARGET + r"\b"),
    ("role hijack", r"\byou are now\b|\b(system|developer) prompt\b|\bnew instructions\b"),
    ("unsafe git", r"--no-verify|\bforce[- ]push\b|\bpush\s+(-f|--force)\b|\bcommit\s+(-\w*n\b|--no-verify)"),
    ("merge unchecked", r"\bmerge\b.{0,20}\bwithout\b.{0,15}\b(review|approval|tests?|checks?)\b"),
    ("lower the floor", r"\b(lower|reduce|drop|set)\b.{0,30}\b(coverage|threshold|floor)\b"),
    ("edit gate state", r"\b(edit|change|write|delete|remove|overwrite)\b.{0,30}(policy\.yml|gates?-(ready|done)\.json|sign-?off)"),
    ("self approval", r"\bapprove (it|this|the pr) yourself\b|\bauto-?approve\b"),
]


def normal(text):
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return re.sub(r"[_\s]+", " ", text).lower()


def mixed_script(text):
    for word in re.findall(r"\w+", text):
        letters = [c for c in word if c.isalpha()]
        if any(c.isascii() for c in letters) and any(not c.isascii() for c in letters):
            return word
    return None


def check(p):
    f = []
    for item in p.get("texts", []):
        t, where = normal(str(item.get("text", ""))), str(item.get("source", "?"))
        sev = "warn" if item.get("kind") == "data" else "fail"
        hits = [(label, m.group(0)) for label, pat in PATTERNS for m in [re.search(pat, t)] if m]
        odd = mixed_script(t)
        if odd:
            hits.append(("mixed script", odd))
        for label, text in hits:
            f.append(finding("injection", "%s: '%s' (treated as data, ignored)" % (label, text[:80]), where, sev))
    return f, {}


if __name__ == "__main__":
    sys.exit(run("injection", check))
