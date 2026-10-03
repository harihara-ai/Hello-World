"""Roles (Observer, Builder, Evolver, Reflector), the ratchet, and the fail-fast gates."""
import hashlib
import json
import math
import re
import shutil
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from . import gitutil
from .agent import run_agent
from .config import load_state, save_state
from .judge import JUDGE_SIDE, RunResult, check_integrity, judge, summarize

CATEGORY_HELP = {
    "NO_CHANGE": "the agent changed no source file",
    "WRONG_FIX": "the agent changed code but the hidden tests still fail",
    "REGRESSION": "the hidden tests pass but the existing suite broke",
    "CHEATED": "the agent touched test files, which scores zero",
    "TIMEOUT": "the agent hit the time limit",
    "NOT_RUN": "the generation budget ran out",
}
from .mine import load_tasks

PROMPTS = Path(__file__).parent / "prompts"


class GateFailed(RuntimeError):
    pass


def log_event(paths, **entry):
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **entry}
    with paths.log.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def read_log(paths):
    if not paths.log.exists():
        return []
    return [json.loads(l) for l in paths.log.read_text().splitlines() if l.strip()]


# ---- harness versioning (a private git repo inside .seed/harness) ----

def harness_git(paths, *args, check=True):
    return gitutil.git(paths.harness, *args, check=check)


def harness_init(paths):
    paths.harness.mkdir(parents=True, exist_ok=True)
    if not (paths.harness / ".git").exists():
        harness_git(paths, "init", "-q")
        harness_git(paths, "config", "user.email", "seed@localhost")
        harness_git(paths, "config", "user.name", "seed")
        harness_git(paths, "commit", "-q", "--allow-empty", "-m", "empty harness")


def harness_commit(paths, message):
    harness_git(paths, "add", "-A")
    harness_git(paths, "commit", "-q", "--allow-empty", "-m", message)
    return harness_git(paths, "rev-parse", "HEAD").strip()


def harness_revert(paths):
    harness_git(paths, "reset", "-q", "--hard", "HEAD~1")
    harness_git(paths, "clean", "-qfdx")


def change_fingerprint(paths):
    """Hash of the added/removed lines of the staged harness edit, so it survives a moved base."""
    harness_git(paths, "add", "-A")
    diff = harness_git(paths, "diff", "--cached", "--unified=0", "--", ".", ":(exclude)facts.md")
    lines = sorted(l.rstrip() for l in diff.splitlines()
                   if l[:1] in "+-" and not l.startswith(("+++", "---")) and l[1:].strip())
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()[:16]


CODE_TOKEN_RE = re.compile(r"`([^`]+)`|\b([A-Za-z_][\w.]*(?:_[\w.]*|\(\)|\.[A-Za-z_]\w*))")


def training_identifiers(paths):
    """Code-like names from training bug reports (snake_case, dotted, called(), `quoted`)."""
    names = set()
    for t in load_tasks(paths, "train"):
        for quoted, bare in CODE_TOKEN_RE.findall(t["issue"]):
            tok = (quoted or bare).strip().rstrip("()").strip(".")
            if len(tok) >= 4 and not tok.startswith("http"):
                names.add(tok)
    facts = (paths.harness / "facts.md")
    general = facts.read_text() if facts.exists() else ""
    # Names the Observer found on its own (package names, entry points) are general, not leaks.
    return {n for n in names if n not in general}


def training_identifiers_in_change(paths):
    harness_git(paths, "add", "-A")
    diff = harness_git(paths, "diff", "--cached", "--unified=0", "--", ".", ":(exclude)facts.md")
    added = "\n".join(l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    return sorted(n for n in training_identifiers(paths)
                  if re.search(rf"(?<![\w.]){re.escape(n)}(?![\w])", added))


def change_size(paths):
    """Changed lines in the uncommitted harness edit (facts.md excluded)."""
    harness_git(paths, "add", "-A")
    out = harness_git(paths, "diff", "--cached", "--numstat")
    total = 0
    for line in out.splitlines():
        added, removed, name = line.split("\t", 2)
        if name == "facts.md":
            continue
        total += (int(added) if added.isdigit() else 50) + (int(removed) if removed.isdigit() else 50)
    return total


# ---- roles ----

@contextmanager
def repo_checkout(repo):
    """Roles look at a throwaway checkout of HEAD, never the user's working tree."""
    scratch = Path(tempfile.mkdtemp(prefix="seed-role-"))
    wt = scratch / "repo"
    gitutil.worktree_add(repo, wt, "HEAD")
    try:
        yield wt
    finally:
        gitutil.worktree_remove(repo, wt)
        shutil.rmtree(scratch, ignore_errors=True)


def run_role(repo, paths, cfg, role, extra_dirs=(), **fmt):
    """Run a role agent. Verifies by hash that it left the frozen files alone."""
    before = check_integrity(paths)
    prompt = (PROMPTS / f"{role}.md").read_text()
    for key, value in {"harness": paths.harness, **fmt}.items():
        prompt = prompt.replace("{" + key + "}", str(value))
    out_dir = paths.runs / "roles" / f"{role}-{time.strftime('%Y%m%d-%H%M%S')}"
    with repo_checkout(repo) as wt:
        res = run_agent(prompt, wt, out_dir, cfg, cfg["role_max_turns"], cfg["role_max_cost_usd"],
                        deny=paths.frozen, add_dirs=[paths.harness, *extra_dirs])
    if gitutil.tree_hash(paths.frozen) != before:
        raise GateFailed(f"{role} modified the frozen judge or SEED.md; aborting")
    spend(paths, res.cost)
    return res


def spend(paths, usd):
    state = load_state(paths)
    state["spent_usd"] = round(state.get("spent_usd", 0.0) + usd, 4)
    save_state(paths, state)
    return state["spent_usd"]


# ---- scoring helpers ----

def score(repo, paths, cfg, harness, label, runs=None):
    state = load_state(paths)
    tasks = load_tasks(paths, exclude=state.get("excluded_tasks", []))
    summary, merged = judge(repo, paths, cfg, tasks, harness, label,
                            runs=runs or cfg["runs_per_task"])
    spend(paths, summary["spent_usd"])
    return summary, merged


def is_better(cand, best, min_net_flips=1):
    """Keep only if train improves by a margin and held-out does not drop. Tie-break on cost, then turns.

    The margin is in net task flips (newly passing minus newly failing train tasks), so a one-task
    wobble from run-to-run noise is not mistaken for progress.
    """
    if cand["heldout"]["pass_rate"] < best["heldout"]["pass_rate"]:
        return False, "held-out dropped"
    if "passed_tasks" in cand["train"] and "passed_tasks" in best["train"]:
        now, before = set(cand["train"]["passed_tasks"]), set(best["train"]["passed_tasks"])
        net = len(now - before) - len(before - now)
    elif "passed" in cand["train"] and "passed" in best["train"]:  # older entries: counts only
        net = cand["train"]["passed"] - best["train"]["passed"]
    else:
        diff = cand["train"]["pass_rate"] - best["train"]["pass_rate"]
        net = (diff > 0) - (diff < 0)
    if net >= min_net_flips:
        return True, f"train up by {net} net task flips"
    if net > 0:
        return False, f"train up by {net}, below the {min_net_flips}-flip margin"
    if net < 0:
        return False, "train pass rate down"
    if cand["train"]["cost"] < 0.9 * best["train"]["cost"]:
        return True, "same pass rate, >=10% cheaper"
    if cand["train"]["turns"] < 0.9 * best["train"]["turns"]:
        return True, "same pass rate, >=10% fewer turns"
    return False, "no measurable gain"


def best_summary(paths):
    """Score of the current harness HEAD (last kept v0/candidate), or None."""
    for e in reversed(read_log(paths)):
        if e["kind"] in ("v0", "candidate") and e.get("kept"):
            return e["score"]
    return None


def baseline_summary(paths):
    for e in reversed(read_log(paths)):
        if e["kind"] == "baseline":
            return e["score"]
    return None


# ---- phases ----

def run_baseline(repo, paths, cfg, out=print):
    out("Baseline: plain Claude Code, no harness")
    summary, merged = score(repo, paths, cfg, None, "baseline", runs=cfg["baseline_runs"])
    if summary["flaky_tasks"]:
        # Gate 2: noisy tasks are dropped from all later scoring.
        state = load_state(paths)
        state["excluded_tasks"] = sorted(set(state.get("excluded_tasks", [])) | set(summary["flaky_tasks"]))
        save_state(paths, state)
        out(f"  Gate 2: dropping noisy tasks {summary['flaky_tasks']}")
        kept = [m for m in merged if m.task_id not in summary["flaky_tasks"]]
        summary = {**summary, **{sp: summarize([m for m in kept if m.split == sp]) for sp in ("train", "heldout")},
                   "all": summarize(kept)}
    log_event(paths, kind="baseline", gen=0, score=summary)
    out(_fmt(summary))
    rate = summary["all"]["pass_rate"]
    if rate in (0.0, 1.0):
        raise GateFailed(f"Gate 0: baseline pass rate is {rate:.0%}; the tasks are bad. Pick different tasks.")
    return summary


def run_build(repo, paths, cfg, out=print):
    base = baseline_summary(paths)
    if base is None:
        raise GateFailed("run `seed baseline` first")
    harness_init(paths)
    out("Observer: writing facts.md")
    run_role(repo, paths, cfg, "observer")
    out("Builder: writing harness v0")
    run_role(repo, paths, cfg, "builder")
    sha = harness_commit(paths, "v0")
    out("Judge: scoring v0")
    summary, _ = score(repo, paths, cfg, paths.harness, "v0")
    log_event(paths, kind="v0", gen=0, harness=sha, score=summary, kept=True)
    out(_fmt(summary))
    if summary["all"]["pass_rate"] < base["all"]["pass_rate"]:
        raise GateFailed("Gate 1: v0 scores below baseline. Fix the Observer/Builder prompts (the seed), not the harness.")
    return summary


def write_digest(paths, digest, merged, label):
    """Inputs for the Evolver: train failures only (held-out stays unseen) and the history."""
    digest.mkdir(parents=True, exist_ok=True)
    tasks = {t["id"]: t for t in load_tasks(paths, "train")}
    failed = [r for r in merged if r.split == "train" and not r.passed and r.category not in JUDGE_SIDE]
    counts = {}
    for r in failed:
        counts[r.category] = counts.get(r.category, 0) + 1
    parts = ["# Failed training tasks\n", "## Why they failed\n"]
    parts += [f"- {cat}: {n} ({CATEGORY_HELP.get(cat, '')})"
              for cat, n in sorted(counts.items(), key=lambda kv: -kv[1])]
    parts.append("")
    for r in failed:
        run_dir = paths.runs / label / r.task_id / "run0"
        parts.append(f"## Task {r.task_id}: {r.category}\n")
        parts.append(f"### Bug report\n{tasks[r.task_id]['issue']}\n")
        if r.cheated:
            parts.append(f"### Scored zero: agent modified test files {r.touched_tests}\n")
        if r.error:
            parts.append(f"### Error\n{r.error}\n")
        for name, title, limit in (("agent.stdout", "Agent final output", 3000),
                                   ("diff.patch", "Agent diff", 4000),
                                   ("test.log", "Hidden test output", 4000),
                                   ("regression.log", "Regression suite output", 3000)):
            f = run_dir / name
            if f.exists():
                text = f.read_text()
                parts.append(f"### {title}\n```\n{text[-limit:]}\n```\n")
    (digest / "failures.md").write_text("\n".join(parts))
    hist = ["# Generation history\n"]
    for e in read_log(paths):
        if e["kind"] in ("v0", "candidate"):
            s = e.get("score") or {}
            hist.append(f"- gen {e['gen']} {e['kind']}: {e.get('change', 'initial harness')} -> "
                        f"train {s.get('train', {}).get('pass_rate', '-')}, "
                        f"{'KEPT' if e.get('kept') else 'REVERTED'} ({e.get('reason', '')})")
    (digest / "history.md").write_text("\n".join(hist) + "\n")


def run_evolve(repo, paths, cfg, generations=None, out=print):
    generations = generations or cfg["max_generations"]
    best = best_summary(paths)
    if best is None:
        raise GateFailed("run `seed build` first")
    last_label = _last_kept_label(paths)
    start_gen = max([e.get("gen", 0) for e in read_log(paths)] + [0]) + 1
    no_gain = 0
    for gen in range(start_gen, start_gen + generations):
        if load_state(paths)["spent_usd"] >= cfg["max_total_cost_usd"]:
            out("Stop: total budget reached")
            break
        if no_gain >= cfg["patience"]:
            out(f"Stop: {no_gain} generations with no gain")
            break
        out(f"Generation {gen}: Evolver")
        merged = _load_merged(paths, last_label)
        digest = paths.root / "evolver_input"
        shutil.rmtree(digest, ignore_errors=True)
        write_digest(paths, digest, merged, last_label)
        res = run_role(repo, paths, cfg, "evolver", extra_dirs=[digest], digest=digest,
                       max_lines=cfg["max_change_lines"])
        change = _change_line(res.result)
        size = change_size(paths)
        if size == 0:
            log_event(paths, kind="candidate", gen=gen, change=change, kept=False, reason="no change made")
            no_gain += 1
            continue
        fingerprint = change_fingerprint(paths)
        rejected = {e.get("fingerprint") for e in read_log(paths)
                    if e["kind"] == "candidate" and not e.get("kept")}
        sha = harness_commit(paths, f"gen {gen}: {change}")
        if fingerprint in rejected:
            # Retry rule: the same change that was already rejected is not re-measured.
            harness_revert(paths)
            log_event(paths, kind="candidate", gen=gen, change=change, harness=sha, fingerprint=fingerprint,
                      kept=False, reason="repeats a rejected change")
            out("  reverted: repeats a rejected change")
            no_gain += 1
            continue
        if size > cfg["max_change_lines"]:
            harness_revert(paths)
            log_event(paths, kind="candidate", gen=gen, change=change, harness=sha, fingerprint=fingerprint,
                      kept=False, reason=f"change too big ({size} lines > {cfg['max_change_lines']})")
            out(f"  reverted: change too big ({size} lines)")
            no_gain += 1
            continue
        leaked = training_identifiers_in_change(paths)
        if leaked:
            # Overfitting guard: a rule about one training task's function won't generalize.
            harness_revert(paths)
            log_event(paths, kind="candidate", gen=gen, change=change, harness=sha, fingerprint=fingerprint,
                      kept=False, reason=f"names training-task identifiers: {', '.join(leaked[:5])}")
            out(f"  reverted: names training-task identifiers {leaked[:5]}")
            no_gain += 1
            continue
        label = f"gen{gen}"
        summary, _ = score(repo, paths, cfg, paths.harness, label)
        keep, reason = is_better(summary, best, cfg.get("min_net_flips", 1))
        if summary["budget_exhausted"]:
            keep, reason = False, "generation budget exhausted before all tasks ran"
        if keep:
            best, last_label, no_gain = summary, label, 0
        else:
            harness_revert(paths)
            no_gain += 1
        log_event(paths, kind="candidate", gen=gen, change=change, harness=sha, lines=size,
                  fingerprint=fingerprint, score=summary, kept=keep, reason=reason)
        out(f"  {'KEPT' if keep else 'REVERTED'} ({reason}): {change}\n{_fmt(summary)}")
    return best


def _change_line(text):
    for line in str(text).splitlines():
        if line.strip().startswith("CHANGE:"):
            return line.strip()[len("CHANGE:"):].strip()[:300]
    return str(text).strip().splitlines()[-1][:300] if str(text).strip() else "(no description)"


def _last_kept_label(paths):
    for e in reversed(read_log(paths)):
        if e["kind"] == "v0" and e.get("kept"):
            return "v0"
        if e["kind"] == "candidate" and e.get("kept"):
            return f"gen{e['gen']}"
    return "v0"


def _load_merged(paths, label):
    merged = []
    for f in sorted((paths.runs / label).glob("*/run0/result.json")):
        merged.append(RunResult(**json.loads(f.read_text())))
    return merged


def run_confirm(repo, paths, cfg, runs=None, out=print):
    """The verdict: fresh runs of plain Claude Code vs. the final harness on held-out tasks.

    The ratchet's own scores are biased upward (it kept whatever scored best), so success is
    judged only here, task by task, with a sign test over tasks where the two differ.
    """
    runs = runs or cfg["confirm_runs"]
    tasks = load_tasks(paths, "heldout", exclude=load_state(paths).get("excluded_tasks", []))
    stamp = time.strftime("%Y%m%d-%H%M%S")
    rates = {}
    for name, harness in (("base", None), ("harness", paths.harness)):
        label = f"confirm-{stamp}-{name}"
        out(f"Confirm: {name} x{runs} on {len(tasks)} held-out tasks")
        summary, _ = judge(repo, paths, cfg, tasks, harness, label, runs=runs)
        spend(paths, summary["spent_usd"])
        if summary["budget_exhausted"]:
            raise GateFailed("confirmation ran out of generation budget; raise max_cost_per_generation_usd")
        rates[name] = per_task_rates(paths, label)
    verdict = paired_verdict(rates["base"], rates["harness"])
    log_event(paths, kind="confirm", runs=runs, verdict=verdict)
    out(f"  harness better on {verdict['wins']} tasks, worse on {verdict['losses']}, "
        f"tied on {verdict['ties']}; mean gain {verdict['mean_gain']:+.0%}; sign test p={verdict['p_value']:.3f}")
    return verdict


def per_task_rates(paths, label):
    """Pass fraction per task across repeated runs; judge-side failures are left out."""
    rates = {}
    for task_dir in sorted((paths.runs / label).iterdir()):
        rs = [json.loads(f.read_text()) for f in task_dir.glob("run*/result.json")]
        rs = [r for r in rs if r.get("category") not in JUDGE_SIDE]
        if rs:
            rates[task_dir.name] = sum(r["passed"] for r in rs) / len(rs)
    return rates


def paired_verdict(base, harness):
    common = sorted(set(base) & set(harness))
    diffs = [harness[t] - base[t] for t in common]
    wins, losses = sum(d > 0 for d in diffs), sum(d < 0 for d in diffs)
    n, k = wins + losses, min(wins, losses)
    # Two-sided exact sign test over the tasks where the two disagree.
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return {"tasks": len(common), "wins": wins, "losses": losses, "ties": len(common) - n,
            "mean_gain": sum(diffs) / len(diffs) if diffs else 0.0, "p_value": round(p, 4),
            "per_task": {t: [base[t], harness[t]] for t in common}}


def run_reflect(repo, paths, cfg, out=print):
    out("Reflector: proposing seed-prompt edits")
    run_role(repo, paths, cfg, "reflector", extra_dirs=[PROMPTS],
             log=paths.log, prompts=PROMPTS, out=paths.proposals)
    out(f"  wrote {paths.proposals} (for human review; nothing is applied)")


def report(paths):
    log = read_log(paths)
    base = baseline_summary(paths)
    best = best_summary(paths)
    lines = []
    if base:
        lines.append(f"baseline: {_fmt(base)}")
    if best:
        lines.append(f"current : {_fmt(best)}")
    confirms = [e for e in log if e["kind"] == "confirm"]
    if confirms:
        v = confirms[-1]["verdict"]
        lines.append(f"confirmed on held-out ({confirms[-1]['runs']} runs each): better on {v['wins']}, "
                     f"worse on {v['losses']}, tied on {v['ties']} tasks; mean gain {v['mean_gain']:+.0%}, "
                     f"sign test p={v['p_value']}")
    elif base and best:
        lines.append("held-out verdict: not confirmed yet (the ratchet's scores are biased upward; "
                     "run `seed confirm`)")
    reverted = [e for e in log if e["kind"] == "candidate" and not e.get("kept")]
    kept = [e for e in log if e["kind"] == "candidate" and e.get("kept")]
    lines.append(f"generations: {len(kept)} kept, {len(reverted)} reverted by the ratchet")
    for e in log:
        if e["kind"] == "candidate":
            lines.append(f"  gen {e['gen']}: {'KEPT ' if e.get('kept') else 'REVERT'} "
                         f"{e.get('reason', '')} | {e.get('change', '')}")
    return "\n".join(lines)


def _fmt(s):
    a = s["all"]
    fails = {k: v for k, v in a.get("categories", {}).items() if k != "PASS"}
    return (f"train {s['train']['passed']}/{s['train']['total']}  "
            f"held-out {s['heldout']['passed']}/{s['heldout']['total']}  "
            f"cost ${a['cost']:.2f}  turns {a['turns']}"
            + (f"  tokens {a.get('input_tokens', 0) // 1000}k in/{a.get('output_tokens', 0) // 1000}k out"
               if a.get("input_tokens") else "")
            + (f"  false claims {a['false_claims']}" if a.get("false_claims") else "")
            + (f"  failures {fails}" if fails else "")
            + (f"  invalid {a['invalid']}" if a.get("invalid") else ""))
