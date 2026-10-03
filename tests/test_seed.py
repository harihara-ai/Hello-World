"""End-to-end tests for SEED on a synthetic repo, with a fake agent in place of `claude -p`."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from seed import cli, loop  # noqa: E402
from seed.config import SeedPaths  # noqa: E402
from seed.mine import is_test_path, issue_text  # noqa: E402

# keyword -> (buggy line, fixed line)
BUGS = {
    "double": ("return x + x + 1", "return x + x"),
    "square": ("return x * x + 1", "return x * x"),
    "negate": ("return x", "return -x"),
    "halve": ("return x // 3", "return x // 2"),
    "triple": ("return x * 4", "return x * 3"),
    "cube": ("return x * x", "return x * x * x"),
    "cheat": ("return 0", "return 1"),
    "breaker": ("return 7", "return 8"),
}
FIXES = {k: list(v) for k, v in BUGS.items()}


def sh(cwd, *cmd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


def make_repo(root):
    """A repo whose history has one fix-with-test commit per bug, plus some noise."""
    repo = Path(root) / "calc"
    repo.mkdir()
    sh(repo, "git", "init", "-q", "-b", "main")
    sh(repo, "git", "config", "user.email", "t@example.com")
    sh(repo, "git", "config", "user.name", "t")
    funcs = {k: bug for k, (bug, _) in BUGS.items()}

    def write_calc():
        body = "".join(f"def {k}(x):\n    {line}\n\n\n" for k, line in funcs.items())
        (repo / "calc.py").write_text(body)

    write_calc()
    (repo / "tests").mkdir()
    (repo / "tests" / "__init__.py").write_text("")
    (repo / "pyproject.toml").write_text("[project]\nname='calc'\n")
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-q", "-m", "Initial calc")
    expected = {"double": (3, 6), "square": (3, 9), "negate": (3, -3), "halve": (8, 4),
                "triple": (3, 9), "cube": (2, 8), "cheat": (5, 1), "breaker": (1, 8)}
    for k, (_, fixed) in BUGS.items():
        funcs[k] = fixed
        write_calc()
        arg, want = expected[k]
        (repo / "tests" / f"test_{k}.py").write_text(
            "import unittest\nimport calc\n\n\nclass T(unittest.TestCase):\n"
            f"    def test_{k}(self):\n        self.assertEqual(calc.{k}({arg}), {want})\n")
        sh(repo, "git", "add", "-A")
        sh(repo, "git", "commit", "-q", "-m", f"Fix {k} returning the wrong value\n\nSigned-off-by: t <t@example.com>")
    # Noise: a docs-only fix and a feature with tests; neither is a task.
    (repo / "README.md").write_text("fix typo\n")
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-q", "-m", "Fix typo in README")
    return repo


def quiet(fn, *args, **kw):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kw)


class UnitTests(unittest.TestCase):
    def test_test_paths(self):
        for p in ["tests/test_a.py", "src/foo_test.go", "web/a.test.ts", "src/test/java/FooTest.java",
                  "spec/a_spec.rb", "conftest.py"]:
            self.assertTrue(is_test_path(p), p)
        for p in ["src/calc.py", "lib/contest.py", "latest.js"]:
            self.assertFalse(is_test_path(p), p)

    def test_issue_text_strips_trailers(self):
        msg = "Fix x\n\nBody line\n\nSigned-off-by: a <a@b>\nCo-authored-by: c <c@d>\n"
        self.assertEqual(issue_text(msg), "Fix x\n\nBody line")
        self.assertEqual(issue_text("fix: keep items when maxlen is 0\n\n"), "fix: keep items when maxlen is 0")

    def test_summary_leaves_out_judge_side_failures(self):
        from seed.judge import RunResult, merged_category, summarize
        rs = [RunResult("a", "train", passed=True, category="PASS"),
              RunResult("b", "train", category="WRONG_FIX"),
              RunResult("c", "train", category="SETUP_FAILURE")]
        s = summarize(rs)
        self.assertEqual((s["passed"], s["total"], s["invalid"]), (1, 2, 1))
        self.assertEqual(s["categories"], {"PASS": 1, "SETUP_FAILURE": 1, "WRONG_FIX": 1})
        runs = [RunResult("a", "train", category="WRONG_FIX"), RunResult("a", "train", category="REGRESSION"),
                RunResult("a", "train", category="REGRESSION")]
        self.assertEqual(merged_category(runs), "REGRESSION")

    def test_claims_success(self):
        from seed.agent import claims_success
        self.assertTrue(claims_success("I fixed the off-by-one; tests pass."))
        self.assertFalse(claims_success("I could not reproduce the bug."))
        self.assertFalse(claims_success("Here is what I looked at."))

    def test_is_better(self):
        def s(train, held, cost=1.0, turns=10):
            return {"train": {"pass_rate": train, "cost": cost, "turns": turns},
                    "heldout": {"pass_rate": held}}
        self.assertTrue(loop.is_better(s(0.6, 0.5), s(0.5, 0.5))[0])
        self.assertFalse(loop.is_better(s(0.9, 0.4), s(0.5, 0.5))[0])  # held-out dropped
        self.assertFalse(loop.is_better(s(0.5, 0.5), s(0.5, 0.5))[0])
        self.assertTrue(loop.is_better(s(0.5, 0.5, cost=0.5), s(0.5, 0.5))[0])

    def test_keep_margin_counts_net_task_flips(self):
        def s(passed):
            return {"train": {"pass_rate": len(passed) / 10, "passed": len(passed), "passed_tasks": passed,
                              "cost": 1.0, "turns": 10}, "heldout": {"pass_rate": 0.5}}
        base = s(["a", "b"])
        self.assertFalse(loop.is_better(s(["a", "b", "c"]), base, min_net_flips=2)[0])
        self.assertFalse(loop.is_better(s(["c", "d"]), base, min_net_flips=1)[0])  # swapped, net 0
        self.assertTrue(loop.is_better(s(["a", "b", "c", "d"]), base, min_net_flips=2)[0])

    def test_overfitting_guard_flags_training_identifiers(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            paths = SeedPaths(tmp)
            paths.judge.mkdir(parents=True)
            paths.tasks.write_text(json.dumps([
                {"id": "t1", "split": "train", "issue": "Fix one()/only() dropping a falsy `default` in running_min"},
                {"id": "t2", "split": "heldout", "issue": "Raise for negative sizes in sliced()"}]))
            loop.harness_init(paths)
            (paths.harness / "facts.md").write_text("- package: more_itertools\n")
            loop.harness_commit(paths, "v0")
            (paths.harness / "CLAUDE.md").write_text("Reproduce first. Check running_min and only() edge cases.\n"
                                                     "Use more_itertools tests. sliced() is fine.\n")
            self.assertEqual(loop.training_identifiers_in_change(paths), ["only", "running_min"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_paired_verdict(self):
        v = loop.paired_verdict({"a": 0, "b": 0, "c": 1, "d": 0.5}, {"a": 1, "b": 1, "c": 1, "d": 0})
        self.assertEqual((v["wins"], v["losses"], v["ties"]), (2, 1, 1))
        self.assertEqual(v["p_value"], 1.0)


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = make_repo(self.tmp)
        self.paths = SeedPaths(self.repo)
        self.plan = self.tmp / "plan"
        os.environ["SEED_FAKE_FIXES"] = json.dumps(FIXES)
        os.environ["SEED_FAKE_PLAN"] = str(self.plan)
        quiet(cli.main, ["--repo", str(self.repo), "init"])
        cfg = json.loads(self.paths.config.read_text())
        cfg.update(test_cmd=f"{sys.executable} -m unittest {{tests}}",
                   regression_cmd=f"{sys.executable} -m unittest discover -s tests -t .",
                   agent_cmd=[sys.executable, str(ROOT / "tests" / "fake_agent.py"), "{prompt_file}"],
                   baseline_runs=1, heldout_fraction=0.0, min_net_flips=1, confirm_runs=2)
        self.paths.config.write_text(json.dumps(cfg))

    def tearDown(self):
        from seed.gitutil import set_readonly
        set_readonly(self.tmp, False)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def mine(self):
        quiet(cli.main, ["--repo", str(self.repo), "mine"])
        return json.loads(self.paths.tasks.read_text())

    def test_mine_builds_hidden_tasks(self):
        tasks = self.mine()
        self.assertEqual(sorted(t["issue"].split()[1] for t in tasks), sorted(BUGS))
        for t in tasks:
            self.assertEqual(t["hidden_tests"], [f"tests/{'test_' + t['issue'].split()[1]}.py"])
            self.assertNotIn("Signed-off-by", t["issue"])
            self.assertTrue(t["regression_check"])  # the reference fix keeps the suite green
        self.assertEqual({t["split"] for t in tasks}, {"train", "heldout"})
        self.assertTrue(self.paths.manifest.exists())
        # .seed/ is invisible to git in the repo under test (and so in task checkouts).
        self.assertEqual(subprocess.run(["git", "status", "--porcelain"], cwd=self.repo,
                                        capture_output=True, text=True).stdout, "")

    def test_full_loop_ratchet_and_anti_cheat(self):
        tasks = self.mine()
        self.plan.write_text("good,bad,good,bad,big,good,good,good,good")
        cfg = json.loads(self.paths.config.read_text())

        base = quiet(loop.run_baseline, self.repo, self.paths, cfg)
        self.assertEqual(base["all"]["passed"], 1)  # only the "easy" bug
        self.assertEqual(base["all"]["cheated"], 1)  # the cheat task scored 0
        # "breaker" passes its hidden test but breaks the suite: the invariant fails it.
        self.assertEqual(base["all"]["categories"],
                         {"PASS": 1, "CHEATED": 1, "REGRESSION": 1, "NO_CHANGE": len(BUGS) - 3})
        self.assertEqual(base["all"]["false_claims"], 1)  # "breaker" said "fixed" but broke the suite
        self.assertEqual(base["all"]["input_tokens"], 1500 * len(BUGS))

        v0 = quiet(loop.run_build, self.repo, self.paths, cfg)
        self.assertEqual(v0["all"]["passed"], 1)
        self.assertTrue((self.paths.harness / "CLAUDE.md").exists())
        self.assertTrue((self.paths.harness / "facts.md").exists())

        best = quiet(loop.run_evolve, self.repo, self.paths, cfg, 9)
        log = loop.read_log(self.paths)
        cands = [e for e in log if e["kind"] == "candidate"]
        reasons = [e["reason"] for e in cands]
        self.assertTrue(any(e["kept"] for e in cands))
        self.assertIn("train up by 1 net task flips", reasons)
        self.assertTrue(any("held-out dropped" in r or "down" in r for r in reasons))  # sabotage reverted
        self.assertTrue(any(r.startswith("change too big") for r in reasons))
        self.assertIn("repeats a rejected change", reasons)  # retry rule: no second scoring
        self.assertEqual(reasons.count("repeats a rejected change"), 1)
        failures = (self.paths.root / "evolver_input" / "failures.md").read_text()
        self.assertIn("## Why they failed", failures)
        self.assertNotIn("sabotage", (self.paths.harness / "CLAUDE.md").read_text())
        self.assertNotIn("filler", (self.paths.harness / "CLAUDE.md").read_text())
        # All train tasks except cheat can be learned; held-out was never shown to the Evolver.
        train_ids = {t["id"] for t in tasks if t["split"] == "train"}
        self.assertGreater(best["train"]["passed"], v0["train"]["passed"])
        self.assertLessEqual(best["train"]["passed"], len(train_ids))

        verdict = quiet(loop.run_confirm, self.repo, self.paths, cfg)
        self.assertEqual(verdict["tasks"], 1)  # the one held-out task, run twice per arm
        self.assertIn("confirmed on held-out", loop.report(self.paths))
        quiet(loop.run_reflect, self.repo, self.paths, cfg)
        self.assertTrue(self.paths.proposals.exists())
        self.assertIn("generations:", loop.report(self.paths))

    def test_rescore_applies_a_stricter_judge_without_model_calls(self):
        self.mine()
        cfg = json.loads(self.paths.config.read_text())
        lax = dict(cfg, regression_cmd=None)
        quiet(loop.run_baseline, self.repo, self.paths, lax)
        before = {json.loads(f.read_text())["category"]
                  for f in (self.paths.runs / "baseline").glob("*/run0/result.json")}
        self.assertNotIn("REGRESSION", before)  # without the invariant, "breaker" passes
        os.environ["SEED_FAKE_FIXES"] = "{}"  # any model call would now fail differently
        from seed.judge import rescore
        from seed.mine import load_tasks
        summary, _ = rescore(self.repo, self.paths, cfg, load_tasks(self.paths), "baseline")
        self.assertEqual([(old, new) for _, _, old, new in summary["changed"]], [("PASS", "REGRESSION")])
        self.assertEqual(summary["all"]["passed"], 1)

    def test_tampered_judge_refuses_to_score(self):
        self.mine()
        from seed.gitutil import set_readonly
        set_readonly(self.paths.judge, False)
        hidden = next(self.paths.hidden.rglob("test_*.py"))
        hidden.write_text("pass\n")
        cfg = json.loads(self.paths.config.read_text())
        with self.assertRaises(Exception) as ctx:
            quiet(loop.run_baseline, self.repo, self.paths, cfg)
        self.assertIn("frozen", str(ctx.exception))

    def test_gate0_stops_on_all_fail(self):
        self.mine()
        cfg = json.loads(self.paths.config.read_text())
        os.environ["SEED_FAKE_FIXES"] = json.dumps({"cheat": FIXES["cheat"]})
        with self.assertRaises(loop.GateFailed) as ctx:
            quiet(loop.run_baseline, self.repo, self.paths, cfg)
        self.assertIn("Gate 0", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
