"""Deterministic stand-in for `claude -p`, used by the tests.

Task runs: fixes a bug only if its keyword is "easy" or the harness CLAUDE.md
contains `hint: <keyword>`. A `sabotage` line in CLAUDE.md makes it fail everything.
The keyword `cheat` makes it edit a test file instead; `breaker` fixes its bug but
breaks another function.
Roles are recognized from the prompt and write plausible harness files.
"""
import json
import os
import re
import sys
from pathlib import Path

EASY = {"double"}
FIXES = json.loads(os.environ["SEED_FAKE_FIXES"])  # keyword -> [old, new] in calc.py


def emit(result, cost=0.01, turns=3):
    print(json.dumps({"result": result, "total_cost_usd": cost, "num_turns": turns}))


def task(prompt):
    claude_md = Path("CLAUDE.md").read_text() if Path("CLAUDE.md").exists() else ""
    if "sabotage" in claude_md:
        return emit("gave up")
    kw = next((k for k in FIXES if re.search(rf"\b{k}\b", prompt)), None)
    if kw == "cheat":
        Path("tests/test_cheat.py").write_text("# deleted the assertion\n")
        return emit("edited tests")
    if kw and (kw in EASY or kw == "breaker" or f"hint: {kw}" in claude_md):
        old, new = FIXES[kw]
        src = Path("calc.py").read_text().replace(f"def {kw}(x):\n    {old}\n", f"def {kw}(x):\n    {new}\n")
        if kw == "breaker":  # fixes its bug but breaks a neighbour: a regression
            src = src.replace("return x + x\n", "return x + x + 5\n")
        Path("calc.py").write_text(src)
        return emit(f"fixed {kw}")
    emit("could not find the bug")


def harness_path(prompt):
    return Path(re.search(r"`(/[^`]+)/facts\.md`", prompt).group(1))


def evolver(prompt):
    harness = Path(re.search(r"harness is in `([^`]+)`", prompt).group(1))
    digest = Path(re.search(r"`([^`]+)/failures\.md`", prompt).group(1))
    plan_file = Path(os.environ["SEED_FAKE_PLAN"])
    plan = plan_file.read_text().split(",")
    step, rest = plan[0], plan[1:]
    plan_file.write_text(",".join(rest or ["noop"]))
    claude_md = harness / "CLAUDE.md"
    if step == "bad":
        claude_md.write_text(claude_md.read_text() + "sabotage\n")
        return emit("CHANGE: added a risky rule")
    if step == "big":
        claude_md.write_text(claude_md.read_text() + "filler\n" * 500)
        return emit("CHANGE: huge rewrite")
    if step == "noop":
        return emit("CHANGE: nothing")
    reports = re.findall(r"### Bug report\n(.*)", (digest / "failures.md").read_text())
    failures = "\n".join(reports)
    for kw in FIXES:
        if kw != "cheat" and re.search(rf"\b{kw}\b", failures) and f"hint: {kw}" not in claude_md.read_text():
            claude_md.write_text(claude_md.read_text() + f"hint: {kw}\n")
            return emit(f"CHANGE: hint for {kw}")
    emit("CHANGE: nothing to do")


def main():
    prompt = Path(sys.argv[1]).read_text()
    if prompt.startswith("You are the Observer"):
        harness_path(prompt).joinpath("facts.md").write_text("- tests: python3 -m unittest\n")
        return emit("facts written")
    if prompt.startswith("You are the Builder"):
        harness = harness_path(prompt)
        (harness / "CLAUDE.md").write_text("# Project\nRun python3 -m unittest.\n")
        (harness / "scripts").mkdir(exist_ok=True)
        (harness / "scripts" / "check.sh").write_text("python3 -m unittest\n")
        return emit("harness v0 written")
    if prompt.startswith("You are the Evolver"):
        return evolver(prompt)
    if prompt.startswith("You are the Reflector"):
        out = re.search(r"Write `([^`]+)`", prompt).group(1)
        Path(out).write_text("- observer.md: also record the test command timing\n")
        return emit("proposals written")
    task(prompt)


main()
