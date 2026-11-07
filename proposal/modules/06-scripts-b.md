purpose: working source for the scripts components of the kit (tangled into workspace/).

# Scripts

Helpers used by gates and commands.

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

## script.changectx

Round 3: facts from git and the change folder (base, base-commit files, approved plan, texts).

````python file=kit/scripts/changectx.py
"""purpose: facts gate_check reads from git and the change folder: base, base-commit files, changed paths, texts.

Every value comes from git or the files themselves, never from what an agent says about them.
"""
import os
import re
import subprocess
import tempfile

DATA = ("comments/", "fetched/")
PLAN_FILES = ["spec.md", "slices.md", "inputs/diff_scope.json", "inputs/granularity.json"]


def git(*args):
    p = subprocess.run(["git", *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def default_base():
    for ref in ("origin/HEAD", "origin/main", "origin/master"):
        sha = git("merge-base", "HEAD", ref)
        if sha:
            return sha
    return None


def decode(raw):
    for bom, enc in ((b"\xff\xfe", "utf-16"), (b"\xfe\xff", "utf-16"), (b"\xef\xbb\xbf", "utf-8-sig")):
        if raw.startswith(bom):
            return raw.decode(enc, errors="ignore")
    return raw.decode("utf-8", errors="ignore")


def texts_under(ch):
    out, names = [], set()
    for root, _d, files in os.walk(ch):
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), ch).replace(os.sep, "/")
            if re.fullmatch(r"gates-\w+\.json", rel):
                continue
            kind = "data" if rel == "ticket.md" or rel.startswith(DATA) else "authored"
            names |= {(seg, kind) for seg in rel.split("/")}
            with open(os.path.join(root, name), "rb") as fh:
                text = decode(fh.read())
            if "\x00" not in text:
                out.append({"source": rel, "text": text, "kind": kind})
    return out + [{"source": "file name %s" % n, "text": n, "kind": k} for n, k in sorted(names)]


def from_base(base, rel):
    """A file as it is in the base commit (written to a temp file), or None."""
    text = git("show", "%s:%s" % (base, rel)) if base else None
    if not text:
        return None
    fd, path = tempfile.mkstemp(suffix=os.path.splitext(rel)[1])
    with os.fdopen(fd, "w") as fh:
        fh.write(text + "\n")
    return path


def changed_paths(base):
    return [n for n in ((git("diff", "--no-ext-diff", "--name-only", "--no-renames", base, "--") or "").splitlines()
                        + (git("ls-files", "--others", "--exclude-standard") or "").splitlines()) if n]


def approved_plan(base, ch):
    """The plan as merged to the base commit (G1 approval), copied to a temp dir, or None if not merged."""
    d = tempfile.mkdtemp(prefix="plan-")
    for rel in PLAN_FILES:
        src = from_base(base, "%s/%s" % (ch, rel))
        if src:
            os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
            os.replace(src, os.path.join(d, rel))
    return d if os.path.isfile(os.path.join(d, "spec.md")) else None
````
