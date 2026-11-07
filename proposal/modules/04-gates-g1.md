purpose: working source for the gates for readiness components of the kit (tangled into workspace/).

# Gates for readiness

Deterministic, JSON in and JSON out, exit 0 pass, 1 fail, 2 bad input. Tests: tests/unit.

## gate.spec_lint

Sections 10.1, 10.2. Trap 2. Vague words count only in Outcome, Requirements and Non-functional, unless a measure follows them (round 1 F15).

````python file=kit/gates/spec_lint.py
#!/usr/bin/env python3
"""purpose: G1 spec checks: ticket, type, sections, REQ IDs, Given/When/Then with an error case, test levels, vague words, size.

Input: {"spec": "path/to/spec.md", "policy": {banned_words, max_spec_lines}}. Output: gate JSON.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402
from kitconst import NO_REQUIREMENT_TYPES  # noqa: E402

ID = re.compile(r"^(REQ-[A-Z0-9]+-\d{3}):\s+\S")
LEVELS = {"unit", "api", "behaviour", "behavior", "ui"}
REQUIRED = ["Problem", "Outcome", "Requirements", "Non-functional", "Out of scope", "Open questions"]
SCORED = {"Outcome", "Requirements", "Non-functional"}
NONE = {"none", "0", "-", "n/a"}
STANDARD = re.compile(r"\b(WCAG|OWASP|ISO|PCI|GDPR|SOC|HIPAA)\b")
MEASURE = re.compile(r"[<>≤≥]?=?\s*\d+(\.\d+)?\s*(ms|s|sec|seconds?|minutes?|%|percent|kb|mb|gb|rps|req|"
                     r"requests|users|items|rows|days|hours)\b", re.I)
SCENARIO = re.compile(r"^(Scenario|Scenario Outline|Example):")
ERROR_THEN = re.compile(r"\b(error|reject|throw|raise|invalid|fail|denied|refuse|exception)", re.I)
DEFAULT_BANNED = ["fast", "easy", "user-friendly", "secure", "robust", "simple", "quick", "intuitive"]


def sections(lines):
    out, cur = {}, None
    for n, line in enumerate(lines, 1):
        if line.startswith("## "):
            cur = line[3:].strip()
            out[cur] = []
        elif cur:
            out[cur].append((n, line))
    return out


def requirements(body):
    reqs = []
    for n, line in body:
        if line.startswith("### "):
            reqs.append({"title": line[4:].strip(), "line": n, "errors_none": False, "scenarios": []})
        elif reqs and re.fullmatch(r"errors:\s*none\.?", line.strip().lower()):
            reqs[-1]["errors_none"] = True
        elif reqs and SCENARIO.match(line.strip()):
            reqs[-1]["scenarios"].append({"title": line.strip().split(":", 1)[1].strip(), "line": n, "body": []})
        elif reqs and reqs[-1]["scenarios"]:
            reqs[-1]["scenarios"][-1]["body"].append(line.strip())
    return reqs


def check_req(r, seen):
    f, where = [], "line %d" % r["line"]
    m = ID.match(r["title"])
    if not m:
        f.append(finding("req_id", "requirement heading has no REQ-AREA-NNN id: %s" % r["title"], where))
    elif m.group(1) in seen:
        f.append(finding("duplicate_id", "duplicate id %s" % m.group(1), where))
    else:
        seen.add(m.group(1))
    if not r["scenarios"]:
        f.append(finding("scenario", "requirement has no scenario", where))
    has_error = r["errors_none"]
    for s in r["scenarios"]:
        sw = "line %d" % s["line"]
        has_error = (has_error or s["title"].lower().startswith(("error", "edge"))
                     or any(b.startswith("Then ") and ERROR_THEN.search(b) for b in s["body"]))
        for kw in ("Given ", "When ", "Then "):
            if not any(b.startswith(kw) for b in s["body"]):
                f.append(finding("gwt", "scenario lacks '%s'" % kw.strip(), sw))
        levels = [b.split(":", 1)[1].strip().lower() for b in s["body"] if b.startswith("Level:")]
        if not levels or levels[0] not in LEVELS:
            f.append(finding("test_level", "scenario needs 'Level: unit|api|behaviour|ui'", sw))
    if not has_error:
        f.append(finding("error_case", "add an error scenario or the line 'Errors: none'", where))
    return f


def check(p):
    if "spec" not in p:
        raise UsageError("input needs 'spec'")
    with open(p["spec"], encoding="utf-8") as fh:
        text = fh.read()
    pol = p.get("policy", {})
    m = re.search(r"(?m)^Type:\s*(\S+)", text)
    no_reqs = bool(m) and m.group(1).lower() in NO_REQUIREMENT_TYPES
    banned = pol.get("banned_words", DEFAULT_BANNED)
    lines = text.splitlines()
    f = []
    if len(lines) > int(pol.get("max_spec_lines", 300)):
        f.append(finding("size", "spec has %d lines; split the change" % len(lines)))
    if not re.search(r"(?m)^Ticket:\s*\S+", text):
        f.append(finding("ticket", "no 'Ticket:' line"))
    if not re.search(r"(?m)^Type:\s*\S+", text):
        f.append(finding("work_type", "no 'Type:' line, so no playbook can be chosen"))
    secs = sections(lines)
    for s in REQUIRED:
        if s not in secs and not (no_reqs and s == "Requirements"):
            f.append(finding("section", "missing section '## %s'" % s))
    for n, line in secs.get("Open questions", []):
        if line.strip() and line.strip().lstrip("-* ").lower().rstrip(".") not in NONE:
            f.append(finding("open_questions", "open question must be resolved: %s" % line.strip(), "line %d" % n))
    for n, line in secs.get("Non-functional", []):
        t = line.strip()
        if t and t.lstrip("-* ").lower().rstrip(".") not in NONE and not MEASURE.search(t) and not STANDARD.search(t):
            f.append(finding("nfr_threshold", "NFR needs a number or a named standard: %s" % t, "line %d" % n))
    for name in SCORED & set(secs):
        for n, line in secs[name]:
            plain = re.sub(r"`[^`]*`", "", line)
            for w in banned:
                for m in re.finditer(r"(?<![\w-])%s(?![\w-])" % re.escape(str(w)), plain, re.I):
                    near = plain[m.end():m.end() + 40]
                    if not MEASURE.search(near) and not STANDARD.search(near):
                        f.append(finding("vague_word", "'%s' needs a measure or a named standard" % w, "line %d" % n))
    reqs = requirements(secs.get("Requirements", []))
    if not reqs and not no_reqs:
        f.append(finding("req_id", "no requirements found under '## Requirements'"))
    seen = set()
    for r in reqs:
        f += check_req(r, seen)
    return f, {"requirements": sorted(seen)}


if __name__ == "__main__":
    sys.exit(run("spec_lint", check))
````

## gate.granularity

Section 11.3. Traps 1 and 3. 'and'/'or' in a title is amber, and characterization slices skip size limits (round 1 F16; spec 11.3 write-back needed).

````python file=kit/gates/granularity.py
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
````

## gate.injection

Sections 17.4, 21.1 T5. Trap 4. A tripwire: NFKC, invisible and mixed-script checks plus patterns. Fetched data is flagged as a warning; AI-written text fails (round 1 F09, F14).

````python file=kit/gates/injection.py
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
````
