"""The Judge: a plain script. Runs a harness on mined tasks and scores it against hidden tests."""
import json
import shlex
import shutil
import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import gitutil
from .agent import claims_success, run_agent
from .mine import is_test_path

PROMPTS = Path(__file__).parent / "prompts"
HARNESS_EXCLUDE = {".git", "facts.md"}

# Why a run did not pass. Judge-side categories say nothing about the harness
# and are left out of the score instead of counting as failures.
PASS = "PASS"
CHEATED = "CHEATED"            # touched a test file: scores zero
NO_CHANGE = "NO_CHANGE"        # agent changed no source file
TIMEOUT = "TIMEOUT"            # agent hit the wall-clock cap
WRONG_FIX = "WRONG_FIX"        # hidden tests fail
REGRESSION = "REGRESSION"      # hidden tests pass, but the regression suite fails
NOT_RUN = "NOT_RUN"            # generation budget ran out first
SETUP_FAILURE = "SETUP_FAILURE"  # environment: setup_cmd failed before the agent ran
JUDGE_ERROR = "JUDGE_ERROR"    # the judge itself crashed
JUDGE_SIDE = {SETUP_FAILURE, JUDGE_ERROR}


class IntegrityError(RuntimeError):
    pass


@dataclass
class RunResult:
    task_id: str
    split: str
    passed: bool = False
    cheated: bool = False
    cost: float = 0.0
    turns: int = 0
    duration_s: float = 0.0
    error: str = ""
    category: str = ""
    claimed: bool = False  # the agent's final message claims success (a claim, not evidence)
    input_tokens: int = 0
    output_tokens: int = 0
    models: list = field(default_factory=list)
    touched_tests: list = field(default_factory=list)


def test_command(cfg, task):
    tests = " ".join(shlex.quote(t) for t in task["run_tests"])
    names = ",".join(Path(t).stem for t in task["run_tests"])
    return cfg["test_cmd"].replace("{tests}", tests).replace("{test_names}", names)


def _sh(cmd, cwd, timeout, log_file):
    try:
        proc = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True,
                              timeout=timeout, stdin=subprocess.DEVNULL)
        Path(log_file).write_text(f"$ {cmd}\n[exit {proc.returncode}]\n{proc.stdout}\n{proc.stderr}")
        return proc.returncode
    except subprocess.TimeoutExpired:
        Path(log_file).write_text(f"$ {cmd}\n[timeout after {timeout}s]\n")
        return -1


def restore_hidden_tests(paths, task, worktree):
    for rel in task["hidden_tests"]:
        target = Path(worktree) / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(paths.hidden / task["id"] / rel, target)


def run_hidden_tests(paths, task, worktree, cfg, out_dir):
    restore_hidden_tests(paths, task, worktree)
    code = _sh(test_command(cfg, task), worktree, cfg["test_timeout_s"], Path(out_dir) / "test.log")
    return code == 0


def regression_enabled(cfg, task):
    return bool(cfg.get("regression_cmd")) and task.get("regression_check", True)


def run_regression(worktree, cfg, out_dir):
    """Invariant: whatever the reference fix kept passing, the agent's fix must keep passing."""
    code = _sh(cfg["regression_cmd"], worktree, cfg["regression_timeout_s"], Path(out_dir) / "regression.log")
    return code == 0


def validate_task(repo, paths, cfg, task, scratch):
    """A usable task fails on the parent and passes on the fix commit."""
    for rev, want_pass in ((task["parent"], False), (task["sha"], True)):
        wt = Path(scratch) / f"validate-{task['id']}-{rev[:7]}"
        out = Path(scratch) / f"validate-{task['id']}-{rev[:7]}-out"
        out.mkdir(parents=True, exist_ok=True)
        gitutil.worktree_add(repo, wt, rev)
        try:
            if cfg.get("setup_cmd") and _sh(cfg["setup_cmd"], wt, cfg["setup_timeout_s"], out / "setup.log"):
                return False, f"setup failed at {rev[:7]}"
            passed = run_hidden_tests(paths, task, wt, cfg, out)
            if want_pass and passed and cfg.get("regression_cmd"):
                # The reference fix must pass the suite, or the suite can't judge the agent's fix.
                task["regression_check"] = run_regression(wt, cfg, out)
        finally:
            gitutil.worktree_remove(repo, wt)
        if passed != want_pass:
            return False, ("hidden tests already pass before the fix" if passed
                           else "hidden tests fail even with the fix")
    if cfg.get("regression_cmd") and not task.get("regression_check"):
        return True, "regression suite fails on the reference fix; regression check off for this task"
    return True, ""


def run_task(repo, paths, cfg, task, harness_dir, out_dir):
    """One attempt: fresh worktree at the parent, install harness, agent, anti-cheat, hidden tests."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    res = RunResult(task_id=task["id"], split=task["split"])
    scratch = Path(tempfile.mkdtemp(prefix=f"seed-{task['id']}-"))
    wt = scratch / "repo"
    try:
        gitutil.worktree_add(repo, wt, task["parent"])
        # Setup runs before the harness is installed, so a setup failure is never the harness's fault.
        if cfg.get("setup_cmd") and _sh(cfg["setup_cmd"], wt, cfg["setup_timeout_s"], out_dir / "setup.log"):
            res.error, res.category = "setup failed", SETUP_FAILURE
            return res
        installed = set()
        if harness_dir:
            installed = set(gitutil.copy_tree(harness_dir, wt, exclude=HARNESS_EXCLUDE))
        prompt = (PROMPTS / "task.md").read_text().replace("{issue}", task["issue"])
        agent = run_agent(prompt, wt, out_dir, cfg, cfg["max_turns"], cfg["max_cost_per_task_usd"],
                          deny=[paths.root])
        res.cost, res.turns, res.duration_s = agent.cost, agent.turns, agent.duration_s
        res.input_tokens, res.output_tokens = agent.input_tokens, agent.output_tokens
        res.models, res.claimed = list(agent.models), claims_success(agent.result)
        if agent.timed_out:
            res.error = "agent timed out"
        changed = [p for p in gitutil.changed_files(wt) if p not in installed]
        # Only the agent's own changes, so `seed rescore` can replay them on a clean checkout.
        (out_dir / "diff.patch").write_text(gitutil.diff_patch(wt, changed))
        grade(paths, cfg, task, wt, changed, out_dir, res, agent.timed_out)
        return res
    except Exception as e:  # a crashed judge says nothing about the harness
        res.error, res.category = f"{type(e).__name__}: {e}", JUDGE_ERROR
        return res
    finally:
        (out_dir / "result.json").write_text(json.dumps(asdict(res), indent=2))
        gitutil.worktree_remove(repo, wt)
        shutil.rmtree(scratch, ignore_errors=True)


def grade(paths, cfg, task, wt, changed, out_dir, res, timed_out=False):
    """The verdict on one attempt, from evidence only. Shared by live runs and `rescore`."""
    res.passed, res.cheated = False, False
    res.touched_tests = [p for p in changed if is_test_path(p)]
    if res.touched_tests:
        res.cheated, res.category = True, CHEATED  # anti-cheat: any test file change scores 0
    elif not changed:
        res.category = TIMEOUT if timed_out else NO_CHANGE
    elif not run_hidden_tests(paths, task, wt, cfg, out_dir):
        res.category = TIMEOUT if timed_out else WRONG_FIX
    elif regression_enabled(cfg, task) and not run_regression(wt, cfg, out_dir):
        res.category = REGRESSION
    else:
        res.passed, res.category = True, PASS


def rescore_run(repo, paths, cfg, task, run_dir):
    """Re-grade a recorded attempt by replaying its diff. No model calls."""
    run_dir = Path(run_dir)
    old = json.loads((run_dir / "result.json").read_text())
    res = RunResult(**old)
    if res.category in (NOT_RUN, SETUP_FAILURE, JUDGE_ERROR) or not (run_dir / "diff.patch").exists():
        return res, old
    out_dir = run_dir / "rescore"
    out_dir.mkdir(exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix=f"seed-rescore-{task['id']}-"))
    wt = scratch / "repo"
    try:
        gitutil.worktree_add(repo, wt, task["parent"])
        patch = run_dir / "diff.patch"
        if patch.read_text().strip():
            gitutil.git(wt, "apply", "--binary", str(patch.resolve()))
        changed = gitutil.changed_files(wt)
        grade(paths, cfg, task, wt, changed, out_dir, res, timed_out=old.get("error") == "agent timed out")
    except Exception as e:
        res.passed, res.error, res.category = False, f"{type(e).__name__}: {e}", JUDGE_ERROR
    finally:
        gitutil.worktree_remove(repo, wt)
        shutil.rmtree(scratch, ignore_errors=True)
    (out_dir / "result.json").write_text(json.dumps(asdict(res), indent=2))
    return res, old


def summarize(results):
    invalid = [r for r in results if r.category in JUDGE_SIDE]
    scored = [r for r in results if r.category not in JUDGE_SIDE]
    n = len(scored)
    passed = sum(r.passed for r in scored)
    categories = {}
    for r in results:
        categories[r.category or "UNKNOWN"] = categories.get(r.category or "UNKNOWN", 0) + 1
    return {
        "pass_rate": round(passed / n, 4) if n else 0.0,
        "passed": passed,
        "total": n,
        "invalid": len(invalid),
        "cost": round(sum(r.cost for r in results), 4),
        "turns": sum(r.turns for r in results),
        "cheated": sum(r.cheated for r in scored),
        # Claim vs. evidence: the agent said it succeeded, the hidden tests disagreed.
        "false_claims": sum(r.claimed and not r.passed for r in scored),
        "input_tokens": sum(r.input_tokens for r in results),
        "output_tokens": sum(r.output_tokens for r in results),
        "categories": dict(sorted(categories.items())),
        "failed_tasks": sorted(r.task_id for r in scored if not r.passed),
        "passed_tasks": sorted(r.task_id for r in scored if r.passed),
    }


def merged_category(runs):
    """Majority outcome across repeated runs of one task."""
    passes = sum(r.passed for r in runs)
    if passes * 2 > len(runs):
        return PASS
    fails = [r.category for r in runs if not r.passed]
    return max(sorted(set(fails)), key=fails.count)


def check_integrity(paths):
    expected = paths.manifest.read_text().strip() if paths.manifest.exists() else None
    actual = gitutil.tree_hash(paths.frozen)
    if expected and expected != actual:
        raise IntegrityError("frozen judge/SEED.md changed since `seed mine` froze it; refusing to score")
    return actual


def judge(repo, paths, cfg, tasks, harness_dir, label, runs=1, budget=None):
    """Score a harness (None = plain Claude Code) on `tasks`. Returns (summaries, per-task detail)."""
    check_integrity(paths)
    budget = cfg["max_cost_per_generation_usd"] if budget is None else budget
    spent = {"usd": 0.0}
    lock = threading.Lock()
    jobs = [(t, i) for i in range(runs) for t in tasks]
    snapshot = None
    if harness_dir:
        # Freeze the harness for this generation so an in-flight run can't be affected by edits.
        snapshot = Path(tempfile.mkdtemp(prefix="seed-harness-"))
        gitutil.copy_tree(harness_dir, snapshot, exclude={".git"})

    def one(job):
        task, i = job
        with lock:
            over = spent["usd"] >= budget
        if over:
            return RunResult(task_id=task["id"], split=task["split"], error="generation budget exhausted",
                             category=NOT_RUN)
        r = run_task(repo, paths, cfg, task, snapshot, paths.runs / label / task["id"] / f"run{i}")
        with lock:
            spent["usd"] += r.cost
        return r

    try:
        with ThreadPoolExecutor(max_workers=max(1, cfg["workers"])) as pool:
            results = list(pool.map(one, jobs))
    finally:
        if snapshot:
            shutil.rmtree(snapshot, ignore_errors=True)
    check_integrity(paths)

    return merge_results(results, spent["usd"])


def merge_results(results, spent_usd=0.0):
    """Majority vote over repeated runs per task, then summaries per split."""
    by_task = {}
    for r in results:
        by_task.setdefault(r.task_id, []).append(r)
    merged, flaky = [], []
    for task_id, rs in by_task.items():
        votes = sum(r.passed for r in rs)
        if 0 < votes < len(rs):
            flaky.append(task_id)
        m = RunResult(task_id=task_id, split=rs[0].split, passed=votes * 2 > len(rs),
                      cheated=any(r.cheated for r in rs), cost=sum(r.cost for r in rs) / len(rs),
                      turns=round(sum(r.turns for r in rs) / len(rs)),
                      error="; ".join(sorted({r.error for r in rs if r.error})),
                      category=merged_category(rs),
                      claimed=sum(r.claimed for r in rs) * 2 > len(rs),
                      input_tokens=round(sum(r.input_tokens for r in rs) / len(rs)),
                      output_tokens=round(sum(r.output_tokens for r in rs) / len(rs)),
                      models=sorted({m for r in rs for m in r.models}),
                      touched_tests=sorted({p for r in rs for p in r.touched_tests}))
        merged.append(m)
    summary = {split: summarize([m for m in merged if m.split == split]) for split in ("train", "heldout")}
    summary["all"] = summarize(merged)
    summary["flaky_tasks"] = sorted(flaky)
    summary["spent_usd"] = round(spent_usd, 4)
    summary["budget_exhausted"] = any(r.error == "generation budget exhausted" for r in results)
    return summary, merged


def rescore(repo, paths, cfg, tasks, label):
    """Re-grade every recorded attempt under `label` with the current judge. No model calls."""
    check_integrity(paths)
    by_id = {t["id"]: t for t in tasks}
    results, changes = [], []
    for res_file in sorted((paths.runs / label).glob("*/run*/result.json")):
        task = by_id.get(res_file.parent.parent.name)
        if task is None:
            continue  # excluded (e.g. flaky) since the run was recorded
        new, old = rescore_run(repo, paths, cfg, task, res_file.parent)
        results.append(new)
        if new.category != old.get("category"):
            changes.append((task["id"], res_file.parent.name, old.get("category"), new.category))
    check_integrity(paths)
    summary, merged = merge_results(results)
    summary["changed"] = changes
    return summary, merged
