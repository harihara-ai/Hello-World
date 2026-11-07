"""purpose: read a coverage report (Cobertura, JaCoCo, clover, lcov) and git diff hunks for gate.coverage.

parse_report(path) -> {"covered": {file: {lines}}, "instrumented": {file: {lines}}, "total": pct}
parse_diff(text) -> {file: {added or changed line numbers}}; changed_lines(base) runs git for it.
"""
import os
import re
import subprocess
import xml.etree.ElementTree as ET

# Explicit flags so repo or user git config (noprefix, external diff, textconv, binary attributes) cannot change output.
GIT_DIFF = ["git", "-c", "diff.noprefix=false", "-c", "diff.mnemonicPrefix=false", "-c", "core.quotePath=false",
            "diff", "--no-ext-diff", "--no-textconv", "--text", "--src-prefix=a/", "--dst-prefix=b/"]


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
        sources = [s.text.strip() for s in root.iter("source") if s.text and s.text.strip()]
        packages = list(root.iter("package")) or [root]
        for i, pkg in enumerate(packages):
            src = sources[i] if len(sources) == len(packages) else (sources[0] if len(sources) == 1 else "")
            for cl in pkg.iter("class"):
                f = cl.get("filename")
                f = os.path.join(src, f).replace("\\", "/") if src and not os.path.isabs(f) else f
                for ln in cl.iter("line"):
                    _add(r, f, int(ln.get("number")), int(ln.get("hits", "0")) > 0)
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
    """Exact path first; else the report path sharing the longest run of trailing segments (container roots,
    JaCoCo package paths). A tie is ambiguous and returns None."""
    paths = list(report_paths)
    if repo_path in paths:
        return repo_path
    want = repo_path.split("/")[::-1]

    def common(p):
        n = 0
        for a, b in zip(p.replace("\\", "/").split("/")[::-1], want):
            if a != b:
                break
            n += 1
        return n
    scored = sorted(((common(p), p) for p in paths), reverse=True)
    if not scored or scored[0][0] == 0 or (len(scored) > 1 and scored[1][0] == scored[0][0]):
        return None
    best_n, best = scored[0]
    if best_n < 2 and "/" in best.replace("\\", "/").strip("/") and "/" in repo_path:  # a shared file name alone is no match
        return None
    return best


def parse_reports(paths):
    """Merge several reports (multi-module builds). The total is recomputed from lines when there is more than one."""
    if len(paths) == 1:
        return parse_report(paths[0])
    r = {"covered": {}, "instrumented": {}, "total": None}
    for p in paths:
        one = parse_report(p)
        for k in ("covered", "instrumented"):
            for f, lines in one[k].items():
                r[k].setdefault(f, set()).update(lines)
    n = sum(len(v) for v in r["instrumented"].values())
    r["total"] = round(100.0 * sum(len(v) for v in r["covered"].values()) / n, 2) if n else 100.0
    return r


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
    diff = subprocess.run(GIT_DIFF + ["-U0", "--no-renames", base, "--"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
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
    return {f: lines for f, lines in out.items() if not _binary(f)}


def _binary(path):
    try:
        with open(path, "rb") as fh:
            return b"\x00" in fh.read(8192)
    except OSError:
        return False
