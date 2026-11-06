#!/usr/bin/env python3
"""purpose: G1 spec checks: ticket, type, sections, REQ IDs, Given/When/Then with an error case, test levels, vague words, size.

Input: {"spec": "path/to/spec.md", "policy": {banned_words, max_spec_lines}}. Output: gate JSON.
"""
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from gateio import UsageError, finding, run  # noqa: E402

ID = re.compile(r"^(REQ-[A-Z0-9]+-\d{3}):\s+\S")
LEVELS = {"unit", "api", "behaviour", "behavior", "ui"}
REQUIRED = ["Problem", "Outcome", "Requirements", "Non-functional", "Out of scope", "Open questions"]
NONE = {"none", "0", "-", "n/a"}
STANDARD = re.compile(r"\b(WCAG|OWASP|ISO|PCI|GDPR|SOC)\b")
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
        elif reqs and line.strip().lower() == "errors: none":
            reqs[-1]["errors_none"] = True
        elif reqs and line.strip().startswith("Scenario:"):
            reqs[-1]["scenarios"].append({"title": line.strip()[9:].strip(), "line": n, "body": []})
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
        has_error = has_error or s["title"].lower().startswith(("error", "edge"))
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
        if s not in secs:
            f.append(finding("section", "missing section '## %s'" % s))
    for n, line in secs.get("Open questions", []):
        if line.strip() and line.strip().lower() not in NONE:
            f.append(finding("open_questions", "open question must be resolved: %s" % line.strip(), "line %d" % n))
    for n, line in secs.get("Non-functional", []):
        t = line.strip()
        if t and t.lower() not in NONE and not re.search(r"\d", t) and not STANDARD.search(t):
            f.append(finding("nfr_threshold", "NFR needs a number or a named standard: %s" % t, "line %d" % n))
    for n, line in enumerate(lines, 1):
        if re.search(r"\d", line):
            continue
        for w in banned:
            if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(str(w)), line, re.I):
                f.append(finding("vague_word", "'%s' needs a number or a named standard" % w, "line %d" % n))
    reqs = requirements(secs.get("Requirements", []))
    if not reqs:
        f.append(finding("req_id", "no requirements found under '## Requirements'"))
    seen = set()
    for r in reqs:
        f += check_req(r, seen)
    return f, {"requirements": sorted(seen)}


if __name__ == "__main__":
    sys.exit(run("spec_lint", check))
