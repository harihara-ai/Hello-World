#!/usr/bin/env python3
"""purpose: safely extract `file=<path>` fenced blocks from markdown sources into a workspace.

Writes files only; never executes, imports or chmods +x anything. Exit 0 ok, 1 refused (nothing written).
Usage: tangle.py SOURCE_FILE_OR_DIR LOCKFILE OUTDIR [--pin] [--check] [--approve-high-risk]
"""
import argparse
import hashlib
import os
import re
import sys

ALLOWED_EXT = {".md", ".yml", ".yaml", ".json", ".sh", ".py", ".txt", ".feature", ".toml"}
# Files that steer an agent, run code on checkout or in CI; keep in step with kit/scripts/kitconst.py PROTECTED.
HIGH_RISK_DIRS = {".github", ".husky", "hooks", ".git", ".vscode", ".idea", ".gitlab", ".claude", "gates", "scripts"}
HIGH_RISK_NAMES = ("install.sh", "setup.sh", "postinstall", "preinstall", ".mcp.json", "conftest.py",
                   ".pre-commit-config.yaml", ".gitlab-ci.yml", "install.md")
FENCE = re.compile(r"^(`{3,}|~{3,})(.*)$")
FILE_ATTR = re.compile(r"(?:^|\s)file=(\S+)")


def parse_blocks(text, origin):
    lines = text.split("\n")
    blocks, i, in_comment = [], 0, False
    while i < len(lines):
        line = lines[i]
        was, in_comment = in_comment, comment_after(line, in_comment)
        if was or in_comment:
            i += 1
            continue
        m = FENCE.match(line)
        if not m:
            i += 1
            continue
        fence, info = m.group(1), m.group(2).strip()
        closer = re.compile(r"^" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$")
        j, body = i + 1, []
        while j < len(lines) and not closer.match(lines[j]):
            body.append(lines[j])
            j += 1
        fm = FILE_ATTR.search(info)
        if fm:
            blocks.append({"path": fm.group(1), "content": "\n".join(body) + "\n",
                           "origin": "%s:%d" % (origin, i + 1)})
        i = j + 1
    return blocks


def comment_after(line, in_c):
    """HTML comment state at the end of a line; fences inside comments are not tangled."""
    i = 0
    while (j := line.find("-->" if in_c else "<!--", i)) >= 0:
        in_c, i = not in_c, j + 3
    return in_c


def collect_sources(src):
    if not os.path.isdir(src):
        return [src]
    return sorted(os.path.join(r, f) for r, _d, files in os.walk(src) for f in files if f.endswith(".md"))


def path_problems(path):
    if not path or path != path.strip():
        return ["empty or padded path"]
    parts, ext = path.split("/"), os.path.splitext(path)[1].lower()
    checks = [(path.startswith("/") or re.match(r"^[A-Za-z]:", path), "absolute path"),
              ("\\" in path, "backslash in path"), (any(ord(c) < 32 for c in path), "control character in path"),
              (any(p in ("..", ".", "") for p in parts), "'..', '.' or empty path segment"),
              (any(p.startswith("~") for p in parts), "'~' segment"),
              (ext not in ALLOWED_EXT, "extension %r not allowed" % ext)]
    return [msg for bad, msg in checks if bad]


def is_high_risk(path):
    parts = path.lower().split("/")
    return (any(p in HIGH_RISK_DIRS for p in parts[:-1]) or any(n in parts[-1] for n in HIGH_RISK_NAMES)
            or parts[-1] in ("claude.md", "policy.yml"))


def workspace_problems(outdir, lock):
    found, problems = set(), []
    for root, _dirs, files in os.walk(outdir):  # __pycache__ is not in the lock, so planted bytecode is refused
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), outdir).replace(os.sep, "/")
            found.add(rel)
            with open(os.path.join(root, f), "rb") as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()
            if rel not in lock:
                problems.append("workspace file not in lock: %s" % rel)
            elif lock[rel] != digest:
                problems.append("workspace file changed by hand: %s" % rel)
    problems += ["workspace file missing: %s" % p for p in sorted(set(lock) - found)]
    return problems


def sha(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_lock(path):
    lock = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    digest, _, p = line.partition("  ")
                    lock[p] = digest
    return lock


def under_symlink(outdir, rel):
    parts = rel.split("/")
    return any(os.path.islink(os.path.join(outdir, *parts[:k])) for k in range(1, len(parts) + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("lock")
    ap.add_argument("outdir")
    ap.add_argument("--pin", action="store_true", help="write the lock file (human approval step)")
    ap.add_argument("--check", action="store_true", help="verify only, write nothing")
    ap.add_argument("--approve-high-risk", action="store_true")
    a = ap.parse_args()

    blocks = []
    for s in collect_sources(a.source):
        with open(s, encoding="utf-8") as fh:
            blocks += parse_blocks(fh.read(), s)

    errors, seen = [], {}
    for b in blocks:
        for p in path_problems(b["path"]):
            errors.append("%s: %s (%s)" % (b["origin"], p, b["path"]))
        if b["path"] in seen:
            errors.append("%s: duplicate path %s (also at %s)" % (b["origin"], b["path"], seen[b["path"]]))
        seen[b["path"]] = b["origin"]
        if a.pin and is_high_risk(b["path"]) and not a.approve_high_risk:  # approval is part of the human pin
            errors.append("%s: high-risk file %s needs --approve-high-risk" % (b["origin"], b["path"]))
    if errors:
        print("REFUSED:\n  " + "\n  ".join(errors))
        return 1

    new = {b["path"]: sha(b["content"]) for b in blocks}
    old = load_lock(a.lock)

    if a.pin:
        added = sorted(set(new) - set(old))
        removed = sorted(set(old) - set(new))
        changed = sorted(p for p in new if p in old and new[p] != old[p])
        with open(a.lock, "w", encoding="utf-8") as fh:
            fh.write("# sha256  path  (written by tangle.py --pin; review this diff before committing)\n")
            for p in sorted(new):
                fh.write("%s  %s\n" % (new[p], p))
        print("PINNED %d files. added=%d changed=%d removed=%d" % (len(new), len(added), len(changed), len(removed)))
        for tag, items in (("added", added), ("changed", changed), ("removed", removed)):
            for p in items:
                print("  %s: %s%s" % (tag, p, "  HIGH-RISK" if is_high_risk(p) else ""))
        return 0

    problems = ["unpinned: %s" % p for p in sorted(new) if p not in old]
    problems += ["changed since pin: %s" % p for p in sorted(new) if p in old and old[p] != new[p]]
    problems += ["in lock but missing from source: %s" % p for p in sorted(set(old) - set(new))]
    if problems:
        print("REFUSED (lock mismatch; a human must review and run --pin):\n  " + "\n  ".join(problems))
        return 1

    if a.check:
        ws = workspace_problems(a.outdir, old) if os.path.isdir(a.outdir) else []
        if ws:
            print("REFUSED (workspace does not match the lock; re-run tangle):\n  " + "\n  ".join(ws))
            return 1
        print("OK: %d files match the lock" % len(new))
        return 0

    outdir = os.path.realpath(a.outdir)
    os.makedirs(outdir, exist_ok=True)
    linked = [b["path"] for b in blocks if under_symlink(outdir, b["path"])]
    if linked:
        print("REFUSED: symlink in path %s" % linked)
        return 1
    for b in blocks:
        target = os.path.realpath(os.path.join(outdir, b["path"]))
        if not target.startswith(outdir + os.sep):
            print("REFUSED: path escapes workspace %s" % b["path"])
            return 1
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(b["content"])
        os.chmod(target, 0o644)
    print("TANGLED %d files into %s" % (len(blocks), a.outdir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
