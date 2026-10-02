"""seed: a self-building harness. Run `python -m seed --help`."""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

from . import gitutil, loop
from .config import DEFAULTS, SeedPaths, guess_regression_cmd, guess_test_cmd, load_config
from .judge import IntegrityError, validate_task
from .mine import build_tasks, candidates

PKG = Path(__file__).parent


def cmd_init(args, paths):
    paths.root.mkdir(exist_ok=True)
    paths.judge.mkdir(exist_ok=True)
    if not paths.seed_md.exists():
        shutil.copyfile(PKG / "SEED.md", paths.seed_md)
    if not paths.config.exists():
        cfg = dict(DEFAULTS)
        cfg["test_cmd"] = guess_test_cmd(paths.repo)
        cfg["regression_cmd"] = guess_regression_cmd(paths.repo)
        paths.config.write_text(json.dumps(cfg, indent=2) + "\n")
    loop.harness_init(paths)
    # Keep .seed/ out of the repo under test, so task checkouts never contain it.
    exclude = Path(gitutil.git(paths.repo, "rev-parse", "--git-path", "info/exclude").strip())
    if not exclude.is_absolute():
        exclude = paths.repo / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    text = exclude.read_text() if exclude.exists() else ""
    if ".seed/" not in text.split():
        exclude.write_text(text + ("" if text.endswith("\n") or not text else "\n") + ".seed/\n")
    cfg = load_config(paths)
    print(f"Initialized {paths.root}")
    print(f"  test_cmd: {cfg['test_cmd']!r}")
    print(f"  regression_cmd: {cfg['regression_cmd']!r}")
    print(f"  (review both in {paths.config} before `seed mine`)")


def cmd_survey(args, paths):
    cfg = load_config(paths)
    found = list(candidates(paths.repo, cfg["max_src_files_per_task"]))
    for c in found[: args.show]:
        print(f"  {c['sha'][:10]} {c['message'].strip().splitlines()[0][:70]}")
    print(f"{len(found)} fix-with-test commits (the spec asks for at least 15)")


def cmd_mine(args, paths):
    cfg = load_config(paths)
    if not cfg["test_cmd"]:
        sys.exit(f"set test_cmd in {paths.config} first")
    if paths.judge.exists():
        gitutil.set_readonly(paths.judge, False)
    paths.manifest.unlink(missing_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="seed-validate-"))
    validate = None
    if not args.no_validate:
        validate = lambda t: validate_task(paths.repo, paths, cfg, t, scratch)
    print("Mining fix-with-test commits" + ("" if args.no_validate else " (validating each task)"))
    try:
        tasks = build_tasks(paths.repo, paths, cfg, validate=validate)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    train = sum(t["split"] == "train" for t in tasks)
    print(f"{len(tasks)} tasks: {train} train, {len(tasks) - train} held-out")
    # Freeze: from here on the judge and SEED.md are read-only and hash-checked.
    paths.manifest.write_text(gitutil.tree_hash(paths.frozen) + "\n")
    gitutil.set_readonly(paths.judge)
    gitutil.set_readonly(paths.seed_md)
    print(f"Froze judge (hash in {paths.manifest})")


def cmd_baseline(args, paths):
    loop.run_baseline(paths.repo, paths, load_config(paths))


def cmd_build(args, paths):
    loop.run_build(paths.repo, paths, load_config(paths))


def cmd_evolve(args, paths):
    loop.run_evolve(paths.repo, paths, load_config(paths), args.generations)
    print(loop.report(paths))


def cmd_reflect(args, paths):
    loop.run_reflect(paths.repo, paths, load_config(paths))


def cmd_run(args, paths):
    cfg = load_config(paths)
    loop.run_baseline(paths.repo, paths, cfg)
    loop.run_build(paths.repo, paths, cfg)
    loop.run_evolve(paths.repo, paths, cfg, args.generations)
    loop.run_reflect(paths.repo, paths, cfg)
    print(loop.report(paths))


def cmd_report(args, paths):
    print(loop.report(paths))


def main(argv=None):
    p = argparse.ArgumentParser(prog="seed", description=__doc__)
    p.add_argument("--repo", default=".", help="repository under test (default: .)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="create .seed/ with a judge config to review")
    s = sub.add_parser("survey", help="count fix-with-test commits (pick repos with >= 15)")
    s.add_argument("--show", type=int, default=20)
    s = sub.add_parser("mine", help="build hidden-test tasks from git history and freeze the judge")
    s.add_argument("--no-validate", action="store_true", help="skip fail-before/pass-after check")
    sub.add_parser("baseline", help="score plain Claude Code (Gates 0 and 2)")
    sub.add_parser("build", help="Observer + Builder -> harness v0, then score it (Gate 1)")
    s = sub.add_parser("evolve", help="Evolver + ratchet for N generations")
    s.add_argument("--generations", type=int)
    sub.add_parser("reflect", help="Reflector writes seed-proposals.md for human review")
    s = sub.add_parser("run", help="baseline, build, evolve, reflect")
    s.add_argument("--generations", type=int)
    sub.add_parser("report", help="summarize log.jsonl")
    args = p.parse_args(argv)
    repo = Path(gitutil.git(args.repo, "rev-parse", "--show-toplevel").strip())
    paths = SeedPaths(repo)
    try:
        globals()[f"cmd_{args.cmd}"](args, paths)
    except (loop.GateFailed, IntegrityError) as e:
        sys.exit(f"STOP: {e}")


if __name__ == "__main__":
    main()
