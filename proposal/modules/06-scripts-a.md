purpose: working source for the scripts components of the kit (tangled into workspace/).

# Scripts

Helpers used by gates and commands.

## script.gateio

Shared gate I/O so gates stay one-job files. Rejects NaN and Infinity (round 1 F04).

````python file=kit/scripts/gateio.py
"""purpose: shared I/O for gates: read JSON input (file or '-'), print JSON result, return the exit code."""
import json
import sys


class UsageError(Exception):
    pass


def _no_constant(name):
    raise UsageError("%s is not allowed in gate input" % name)


def read_input(argv):
    if len(argv) != 2:
        raise UsageError("usage: %s INPUT.json|-" % argv[0])
    if argv[1] == "-":
        return json.load(sys.stdin, parse_constant=_no_constant)
    with open(argv[1], encoding="utf-8") as fh:
        return json.load(fh, parse_constant=_no_constant)


def finding(rule, message, where="", severity="fail"):
    return {"rule": rule, "severity": severity, "where": where, "message": message}


def emit(gate, findings, **extra):
    ok = not any(f["severity"] == "fail" for f in findings)
    print(json.dumps(dict({"gate": gate, "pass": ok, "findings": findings}, **extra), indent=1))
    return 0 if ok else 1


def run(gate, check, argv=None):
    """Call check(payload) -> (findings, extra). Exit 0 pass, 1 fail, 2 bad input."""
    argv = argv or sys.argv
    try:
        payload = read_input(argv)
        if not isinstance(payload, dict):
            raise UsageError("input must be a JSON object")
        findings, extra = check(payload)
    except (UsageError, OSError, ValueError, KeyError, TypeError) as e:
        print(json.dumps({"gate": gate, "pass": False, "error": str(e), "findings": []}))
        return 2
    return emit(gate, findings, **extra)
````

## script.kitconst

Round 1: fixed lists (test globs, protected paths, per-type gates) that policy cannot loosen.

````python file=kit/scripts/kitconst.py
"""purpose: shared constants for gates: test-file globs, protected paths and the fixed per-type gate table.

Not policy: repos cannot change these through policy.yml, so a gate cannot be loosened by editing a list.
"""
import fnmatch

TEST_GLOBS = ["tests/*", "test/*", "spec/*", "features/*", "*/tests/*", "*/test/*", "src/test/*",
              "*.Tests/*", "*/Tests/*", "*UnitTests*/*", "*IntegrationTests*/*", "*_test.*", "*.test.*",
              "*_spec.*", "*Test.*", "*Tests.*", "*Spec.*", "test_*", "*/test_*", "*.feature", "safety-net/*"]
NOT_PRODUCTION = TEST_GLOBS + ["openspec/*", "docs/*"]
PROTECTED = ["docs/ai/policy.yml", "docs/ai/policy-signoff.json", "kit/*", "kit.manifest.yml",
             ".claude/*", "CLAUDE.md", ".github/*"]
SKIP_DIRS = {".git", "node_modules", "vendor", "openspec", "docs", "kit", "dist", "build", "bin", "obj",
             "__pycache__", ".venv", "venv", "target"}

# Fixed per work-item type: gates removed from or added to the floor list, and whether production files may change.
TYPES = {
    "story": {}, "nfr": {}, "bug": {}, "hotfix": {},
    "chore": {"drop": ["trace_check"]},
    "refactor": {"drop": ["trace_check"]},
    "spike": {"drop": ["trace_check", "coverage", "granularity"], "no_production": True},
    "docs": {"drop": ["trace_check", "coverage", "granularity"], "no_production": True},
    "tests": {"drop": ["coverage"], "add": ["flaky"], "no_production": True},
}
NO_REQUIREMENT_TYPES = {"chore", "refactor", "spike", "docs"}


def matches(path, globs):
    return any(fnmatch.fnmatchcase(path, g) for g in globs)


def is_test_file(path):
    return matches(path, TEST_GLOBS)
````

## script.cov_import

Round 1 F05: Cobertura, JaCoCo, clover and lcov readers plus git diff hunks.

````python file=kit/scripts/cov_import.py
"""purpose: read a coverage report (Cobertura, JaCoCo, clover, lcov) and git diff hunks for gate.coverage.

parse_report(path) -> {"covered": {file: {lines}}, "instrumented": {file: {lines}}, "total": pct}
parse_diff(text) -> {file: {added or changed line numbers}}; changed_lines(base) runs git for it.
"""
import re
import subprocess
import xml.etree.ElementTree as ET


def _add(r, f, n, hit):
    r["instrumented"].setdefault(f, set()).add(n)
    if hit:
        r["covered"].setdefault(f, set()).add(n)


def _lcov(text):
    r, f = {"covered": {}, "instrumented": {}, "total": None}, None
    for line in text.splitlines():
        if line.startswith("SF:"):
            f = line[3:].strip()
        elif line.startswith("DA:") and f:
            n, hits = line[3:].split(",")[:2]
            _add(r, f, int(n), int(hits) > 0)
    return r


def _xml(root):
    r = {"covered": {}, "instrumented": {}, "total": None}
    if root.tag == "report":  # JaCoCo
        for pkg in root.iter("package"):
            for sf in pkg.iter("sourcefile"):
                f = "%s/%s" % (pkg.get("name"), sf.get("name"))
                for ln in sf.iter("line"):
                    _add(r, f, int(ln.get("nr")), int(ln.get("ci", "0")) > 0)
        for c in root.findall("counter"):
            if c.get("type") == "LINE":
                cov, miss = int(c.get("covered")), int(c.get("missed"))
                r["total"] = round(100.0 * cov / (cov + miss), 2) if cov + miss else 100.0
    elif root.find("project") is not None:  # clover (PHPUnit)
        for fe in root.iter("file"):
            for ln in fe.iter("line"):
                if ln.get("type") in (None, "stmt", "method", "cond"):
                    _add(r, fe.get("name"), int(ln.get("num")), int(ln.get("count", "0")) > 0)
        m = root.find("project/metrics")
        if m is not None and int(m.get("statements", "0")):
            r["total"] = round(100.0 * int(m.get("coveredstatements")) / int(m.get("statements")), 2)
    elif root.tag == "coverage":  # Cobertura (coverlet, coverage.py, PHPUnit, istanbul)
        for cl in root.iter("class"):
            for ln in cl.iter("line"):
                _add(r, cl.get("filename"), int(ln.get("number")), int(ln.get("hits", "0")) > 0)
        if root.get("line-rate") is not None:
            r["total"] = round(100.0 * float(root.get("line-rate")), 2)
    else:
        raise ValueError("unknown XML coverage format: <%s>" % root.tag)
    return r


def parse_report(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    if re.match(r"\s*(TN:|SF:)", text):
        r = _lcov(text)
    elif text.lstrip().startswith("<"):
        r = _xml(ET.fromstring(text))
    else:
        raise ValueError("unknown coverage report format: %s" % path)
    if r["total"] is None:
        n = sum(len(v) for v in r["instrumented"].values())
        r["total"] = round(100.0 * sum(len(v) for v in r["covered"].values()) / n, 2) if n else 100.0
    return r


def match(repo_path, report_paths):
    """Report paths may be absolute, or relative to a source root (JaCoCo package paths)."""
    for p in report_paths:
        q = p.replace("\\", "/")
        if q == repo_path or q.endswith("/" + repo_path) or repo_path.endswith("/" + q.lstrip("/")):
            return p
    return None


def parse_diff(text):
    out, f = {}, None
    for line in text.splitlines():
        if line.startswith("+++ "):
            f = line[6:] if line.startswith("+++ b/") else None
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if m and f:
            start, count = int(m.group(1)), int(m.group(2) or 1)
            if count:
                out.setdefault(f, set()).update(range(start, start + count))
    return out


def changed_lines(base):
    if not re.fullmatch(r"[\w./~^@-]+", base) or base.startswith("-"):
        raise ValueError("bad base ref")
    diff = subprocess.run(["git", "diff", "-U0", "--no-renames", base, "--"], capture_output=True, text=True)
    if diff.returncode != 0:
        raise ValueError("git diff failed: %s" % diff.stderr.strip())
    out = parse_diff(diff.stdout)
    new = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True)
    for f in new.stdout.splitlines():
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                out[f] = set(range(1, len(fh.read().splitlines()) + 1))
        except OSError:
            continue
    return out
````

## script.policy

Flat YAML parser; no third-party dependency.

````python file=kit/scripts/policy.py
"""purpose: parse the flat policy.yml format (key: number | word | [list]) without third-party YAML."""
import re

KEY = re.compile(r"^([a-z][a-z0-9_]*):\s*(.*)$")


def _scalar(v):
    v = v.strip().strip("'\"")
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    return v


def parse(text):
    out = {}
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split(" #")[0].rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = KEY.match(line)
        if not m:
            raise ValueError("line %d: not 'key: value'" % n)
        k, v = m.group(1), m.group(2).strip()
        if v.startswith("["):
            if not v.endswith("]"):
                raise ValueError("line %d: unclosed list" % n)
            inner = v[1:-1].strip()
            out[k] = [_scalar(x) for x in inner.split(",")] if inner else []
        else:
            out[k] = _scalar(v)
    return out


def load(path):
    with open(path, encoding="utf-8") as fh:
        return parse(fh.read())
````
