#!/usr/bin/env python3
"""purpose: pick one tool per capability from probe results using the ranked fallbacks (section 4).

Input: {"results": {tool: {"ok": bool, "reason": str}}, "capabilities": [names]}. Tools not probed are skipped.
Usage: probe.py INPUT.json|- [--out docs/ai/toolchain.md]. Exit 1 when a capability has no working tool (ask).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gateio import UsageError, finding, run  # noqa: E402

RANKED = {  # keyed by adapter name in kit.manifest.yml; add a tool by adding its adapter first
    "codenav": ["serena", "ctags"],
    "tracker": ["github", "jira", "azdo", "file"],
}


def choose(cap, results):
    rejected = []
    for tool in RANKED[cap]:
        r = results.get(tool)
        if r is None:
            continue
        if r.get("ok"):
            return tool, rejected
        rejected.append({"tool": tool, "reason": r.get("reason", "probe failed")})
    return None, rejected


def toolchain_md(caps):
    rows = ["purpose: tools chosen by the /bootstrap probe, with the reason for each fallback.", "",
            "| Capability | Chosen | Rejected (reason) |", "| --- | --- | --- |"]
    for cap, c in caps.items():
        rej = "; ".join("%s (%s)" % (r["tool"], r["reason"]) for r in c["rejected"]) or "none"
        rows.append("| %s | %s | %s |" % (cap, c["chosen"] or "ASK THE USER", rej))
    return "\n".join(rows) + "\n"


def main(argv):
    out = None
    if "--out" in argv:
        i = argv.index("--out")
        out = argv[i + 1] if i + 1 < len(argv) else None
        argv = argv[:i] + argv[i + 2:]

    def check(p):
        results = p.get("results", {})
        caps = p.get("capabilities") or [c for c, tools in RANKED.items() if any(t in results for t in tools)]
        unknown = [c for c in caps if c not in RANKED]
        if unknown:
            raise UsageError("unknown capability: %s" % unknown)
        chosen = {}
        for c in caps:
            tool, rejected = choose(c, results)
            chosen[c] = {"chosen": tool, "rejected": rejected}
        if out:
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(toolchain_md(chosen))
        f = [finding("no_tool", "no working tool for %s: ask the user and record the answer" % c, c)
             for c, v in chosen.items() if v["chosen"] is None]
        return f, {"capabilities": chosen}

    return run("probe", check, argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
