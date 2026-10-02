"""Paths inside .seed/ and the frozen judge config."""
import json
from dataclasses import dataclass
from pathlib import Path

DEFAULTS = {
    # Shell command run in a task worktree after hidden tests are restored.
    # {tests}: space-separated hidden test paths; {test_names}: comma-separated basenames.
    "test_cmd": None,
    # Optional shell command run in each fresh worktree before the agent starts.
    "setup_cmd": None,
    "test_timeout_s": 600,
    # Invariant: shell command for the repo's existing suite. A fix must keep it green wherever
    # the reference fix did. null disables the regression check.
    "regression_cmd": None,
    "regression_timeout_s": 900,
    "setup_timeout_s": 600,
    # Hard caps (spec: "Always").
    "max_turns": 30,
    "max_cost_per_task_usd": 2.0,
    "max_cost_per_generation_usd": 25.0,
    "max_total_cost_usd": 150.0,
    "max_generations": 6,
    "patience": 3,
    "agent_timeout_s": 1800,
    "role_max_turns": 40,
    "role_max_cost_usd": 3.0,
    # One harness change per generation must stay this small (changed lines).
    "max_change_lines": 80,
    "runs_per_task": 1,
    "baseline_runs": 3,  # Gate 2: repeat baseline runs to find noisy tasks
    "heldout_fraction": 0.34,
    "max_src_files_per_task": 5,
    "max_tasks": 40,
    "workers": 1,
    "model": None,
    # Override the agent command (e.g. for tests). Placeholders: {prompt_file}, {cwd}.
    "agent_cmd": None,
}


@dataclass
class SeedPaths:
    repo: Path

    @property
    def root(self):
        return self.repo / ".seed"

    @property
    def seed_md(self):
        return self.root / "SEED.md"

    @property
    def judge(self):
        return self.root / "judge"

    @property
    def config(self):
        return self.judge / "config.json"

    @property
    def tasks(self):
        return self.judge / "tasks.json"

    @property
    def hidden(self):
        return self.judge / "hidden"

    @property
    def manifest(self):
        return self.root / "judge.sha256"

    @property
    def harness(self):
        return self.root / "harness"

    @property
    def log(self):
        return self.root / "log.jsonl"

    @property
    def runs(self):
        return self.root / "runs"

    @property
    def state(self):
        return self.root / "state.json"

    @property
    def proposals(self):
        return self.root / "seed-proposals.md"

    @property
    def frozen(self):
        """Everything the harness-editing agents must never change."""
        return [self.judge, self.seed_md]


def load_config(paths):
    cfg = dict(DEFAULTS)
    if paths.config.exists():
        cfg.update(json.loads(paths.config.read_text()))
    return cfg


def load_state(paths):
    if paths.state.exists():
        return json.loads(paths.state.read_text())
    return {"excluded_tasks": [], "spent_usd": 0.0}


def save_state(paths, state):
    paths.state.write_text(json.dumps(state, indent=2))


def guess_regression_cmd(repo):
    repo = Path(repo)
    for marker, cmd in (("pyproject.toml", "python -m pytest -q"), ("setup.py", "python -m pytest -q"),
                        ("package.json", "npm test --silent"), ("pom.xml", "mvn -q test"),
                        ("build.gradle", "./gradlew test"), ("build.gradle.kts", "./gradlew test"),
                        ("go.mod", "go test ./..."), ("Cargo.toml", "cargo test"),
                        ("composer.json", "vendor/bin/phpunit")):
        if (repo / marker).exists():
            return cmd
    return None


def guess_test_cmd(repo):
    repo = Path(repo)
    if (repo / "pyproject.toml").exists() or (repo / "setup.py").exists() \
            or (repo / "pytest.ini").exists() or (repo / "tox.ini").exists():
        return "python -m pytest -x -q {tests}"
    if (repo / "package.json").exists():
        return "npx --no-install jest {tests}"
    if (repo / "pom.xml").exists():
        return "mvn -q test -Dtest={test_names} -DfailIfNoTests=false"
    if (repo / "build.gradle").exists() or (repo / "build.gradle.kts").exists():
        return "./gradlew test --tests '*{test_names}*'"
    if (repo / "go.mod").exists():
        return "go test ./..."
    if (repo / "Cargo.toml").exists():
        return "cargo test"
    if (repo / "composer.json").exists():
        return "vendor/bin/phpunit {tests}"
    return None
