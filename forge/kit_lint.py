#!/usr/bin/env python3
"""purpose: enforce size caps, manifest coverage, purpose lines, dependency direction and no copy-paste in the kit.

Usage: kit_lint.py WORKSPACE_DIR MANIFEST_FILE
Exit 0 = clean, 1 = errors.
"""
import hashlib
import os
import re
import sys

CAPS = {"core": 100, "capability": 80, "adapter": 150, "gate": 200,
        "playbook": 120, "command": 80, "template": 100, "script": 200}
HARD_CAP = 300
LAYER = {"core": 0, "capability": 1, "gate": 1, "script": 1, "template": 1,
         "adapter": 2, "playbook": 3, "command": 4}


def parse_val(v):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [x.strip().strip("'\"") for x in inner.split(",")] if inner else []
    if re.fullmatch(r"\d+", v):
        return int(v)
    return v.strip("'\"")


def parse_manifest(text):
    items, cur = [], None
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        m = re.match(r"^-\s+(\w+):\s*(.*)$", raw)
        if m:
            cur = {}
            items.append(cur)
        else:
            m = re.match(r"^\s+(\w+):\s*(.*)$", raw)
            if not m or cur is None:
                raise ValueError("bad manifest line: %r" % raw)
        cur[m.group(1)] = parse_val(m.group(2))
    return items


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    ws, mf = sys.argv[1], sys.argv[2]
    with open(mf, encoding="utf-8") as fh:
        comps = parse_manifest(fh.read())

    errors = []
    by_id = {}
    for c in comps:
        for k in ("id", "type", "path"):
            if k not in c:
                errors.append("manifest entry missing %s: %r" % (k, c))
        if c.get("id") in by_id:
            errors.append("duplicate id %s" % c["id"])
        by_id[c.get("id")] = c
    if errors:
        print("\n".join("ERROR " + e for e in errors))
        return 1

    paragraphs = {}
    for c in comps:
        t, p = c["type"], c["path"]
        if t not in CAPS:
            errors.append("%s: unknown type %s" % (c["id"], t))
            continue
        full = os.path.join(ws, p)
        if not os.path.isfile(full):
            errors.append("%s: file missing %s" % (c["id"], p))
            continue
        with open(full, encoding="utf-8") as fh:
            text = fh.read()
        n = len(text.splitlines())
        cap = min(CAPS[t], int(c.get("max_lines", CAPS[t])))
        if int(c.get("max_lines", 0)) > CAPS[t]:
            errors.append("%s: max_lines %s exceeds the %s cap %d" % (c["id"], c["max_lines"], t, CAPS[t]))
        if n > cap:
            errors.append("%s: %d lines exceeds cap %d (split the file)" % (c["id"], n, cap))
        if n > HARD_CAP:
            errors.append("%s: %d lines exceeds the hard cap %d" % (c["id"], n, HARD_CAP))
        if "purpose:" not in "\n".join(text.splitlines()[:15]).lower():
            errors.append("%s: no 'purpose:' line in the first 15 lines" % c["id"])
        if t == "adapter" and not c.get("tests"):
            errors.append("%s: adapter has no contract tests listed" % c["id"])
        if t == "adapter" and not c.get("implements"):
            errors.append("%s: adapter does not say which capability it implements" % c["id"])
        if c.get("implements"):
            target = by_id.get(c["implements"])
            if not target or target["type"] != "capability":
                errors.append("%s: implements %s which is not a capability" % (c["id"], c["implements"]))
        for need in c.get("needs", []):
            d = by_id.get(need)
            if d is None:
                errors.append("%s: needs unknown component %s" % (c["id"], need))
                continue
            if d["type"] == "adapter":
                errors.append("%s: must not depend on adapter %s (depend on its capability)" % (c["id"], need))
            elif LAYER[d["type"]] > LAYER[t]:
                errors.append("%s (%s) depends upward on %s (%s)" % (c["id"], t, need, d["type"]))
            elif t == "core" and d["type"] != "core":
                errors.append("%s: core may only depend on core" % c["id"])
        for para in re.split(r"\n\s*\n", text):
            norm = " ".join(para.split()).lower()
            if len(norm) >= 200:
                paragraphs.setdefault(hashlib.sha256(norm.encode()).hexdigest(), set()).add(p)

    listed = {c["path"] for c in comps}
    kit_dir = os.path.join(ws, "kit")
    if os.path.isdir(kit_dir):
        for root, _d, files in os.walk(kit_dir):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), ws).replace(os.sep, "/")
                if rel not in listed:
                    errors.append("orphan file not in manifest: %s" % rel)

    for paths in paragraphs.values():
        if len(paths) > 1:
            errors.append("duplicated paragraph in: %s (move shared text to core)" % ", ".join(sorted(paths)))

    if errors:
        print("\n".join("ERROR " + e for e in errors))
        print("%d error(s)" % len(errors))
        return 1
    print("OK: %d components clean" % len(comps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
