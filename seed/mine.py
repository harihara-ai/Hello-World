"""Mine git history for fix-with-test commits and turn them into judge tasks."""
import hashlib
import json
import re
import shutil
from pathlib import Path

from .gitutil import git

TEST_PATH_RE = re.compile(
    r"(^|/)(tests?|__tests__|specs?|testing)/"
    r"|(^|/)test_[^/]+$|(^|/)[^/]+_test\.[A-Za-z]+$"
    r"|\.(test|spec)\.[A-Za-z]+$|(^|/)[^/]*Tests?\.(java|kt|cs|scala|php)$"
    r"|_spec\.rb$|(^|/)conftest\.py$")
# A test file a runner can execute directly (vs. fixtures, helpers, data).
RUNNABLE_TEST_RE = re.compile(
    r"(^|/)test_[^/]+\.\w+$|_test\.\w+$|\.(test|spec)\.\w+$"
    r"|Tests?\.(java|kt|cs|scala|php)$|_spec\.rb$")
FIX_MSG_RE = re.compile(
    r"\b(fix(e[sd])?|bug(fix)?|regression|crash(es)?|broken|incorrect|wrong"
    r"|resolve[sd]?|closes?)\b|#\d+", re.I)
NON_SOURCE_RE = re.compile(
    r"(^|/)(docs?|\.github)/|\.(md|rst|txt|adoc)$|(^|/)(CHANGES|CHANGELOG|HISTORY|NEWS|AUTHORS)[^/]*$",
    re.I)
TRAILER_RE = re.compile(r"^[A-Za-z][A-Za-z-]*: .+$")


def is_test_path(path):
    return bool(TEST_PATH_RE.search(path))


def issue_text(message):
    """Commit message with git trailers (Signed-off-by etc.) removed."""
    lines = message.strip().splitlines()
    # The subject line is never a trailer, even when it looks like one ("fix: ...").
    while len(lines) > 1 and (TRAILER_RE.match(lines[-1]) or not lines[-1].strip()):
        lines.pop()
    return "\n".join(lines).strip()


def candidates(repo, max_src_files=5):
    """Yield fix commits that change both source and test files."""
    out = git(repo, "log", "--no-merges", "--name-only", "--format=%x1e%ct %H %P")
    for block in out.split("\x1e"):
        lines = [l for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue
        head = lines[0].split()
        if len(head) != 3:  # root commit
            continue
        date, sha, parent = int(head[0]), head[1], head[2]
        files = lines[1:]
        tests = [f for f in files if is_test_path(f)]
        src = [f for f in files if not is_test_path(f) and not NON_SOURCE_RE.search(f)]
        if not tests or not src or len(src) > max_src_files:
            continue
        message = git(repo, "log", "-1", "--format=%B", sha)
        if not FIX_MSG_RE.search(message):
            continue
        yield {"sha": sha, "parent": parent, "date": date, "message": message,
               "test_files": tests, "src_files": src}


def split_for(sha, heldout_fraction):
    bucket = int(hashlib.sha256(sha.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "heldout" if bucket < heldout_fraction else "train"


def build_tasks(repo, paths, cfg, validate=None, log=print):
    """Write tasks.json and hidden/ under the judge dir. `validate(task) -> (ok, why)`."""
    if paths.hidden.exists():
        shutil.rmtree(paths.hidden)
    paths.hidden.mkdir(parents=True)
    tasks = []
    for cand in candidates(repo, cfg["max_src_files_per_task"]):
        if len(tasks) >= cfg["max_tasks"]:
            break
        task_id = cand["sha"][:10]
        hidden = []
        for path in cand["test_files"]:
            # Keep the post-fix version of every test file that still exists after the fix.
            try:
                content = git(repo, "show", f"{cand['sha']}:{path}")
            except Exception:
                continue  # deleted by the fix
            target = paths.hidden / task_id / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            hidden.append(path)
        if not hidden:
            continue
        runnable = [p for p in hidden if RUNNABLE_TEST_RE.search(p)] or hidden
        task = {
            "id": task_id,
            "sha": cand["sha"],
            "parent": cand["parent"],
            "issue": issue_text(cand["message"]),
            "hidden_tests": hidden,
            "run_tests": runnable,
            "src_files": cand["src_files"],
            "date": cand["date"],
        }
        if not task["issue"]:
            log(f"  drop {task_id}: empty commit message")
            shutil.rmtree(paths.hidden / task_id, ignore_errors=True)
            continue
        if validate:
            ok, why = validate(task)
            if not ok:
                log(f"  drop {task_id}: {why}")
                shutil.rmtree(paths.hidden / task_id, ignore_errors=True)
                continue
            if why:
                log(f"  note {task_id}: {why}")
        log(f"  keep {task_id} {task['issue'].splitlines()[0][:70]}")
        tasks.append(task)
    assign_splits(tasks, cfg.get("split_mode", "time"), cfg["heldout_fraction"])
    _ensure_both_splits(tasks)
    paths.tasks.write_text(json.dumps(tasks, indent=2))
    return tasks


def assign_splits(tasks, mode, heldout_fraction):
    """time: the newest commits are held out, so held-out asks "does it generalize forward?"."""
    if mode == "hash":
        for t in tasks:
            t["split"] = split_for(t["sha"], heldout_fraction)
        return
    n_heldout = round(len(tasks) * heldout_fraction)
    newest_first = sorted(tasks, key=lambda t: t["date"], reverse=True)
    heldout = {t["id"] for t in newest_first[:n_heldout]}
    for t in tasks:
        t["split"] = "heldout" if t["id"] in heldout else "train"


def _ensure_both_splits(tasks):
    if len(tasks) < 2:
        return
    splits = {t["split"] for t in tasks}
    if splits == {"train"}:
        tasks[-1]["split"] = "heldout"
    elif splits == {"heldout"}:
        tasks[0]["split"] = "train"


def load_tasks(paths, split="all", exclude=()):
    tasks = json.loads(Path(paths.tasks).read_text())
    return [t for t in tasks
            if (split == "all" or t["split"] == split) and t["id"] not in exclude]
