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
