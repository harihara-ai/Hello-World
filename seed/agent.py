"""Run one headless Claude Code session (or a stand-in command) with hard caps."""
import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentResult:
    cost: float = 0.0
    turns: int = 0
    result: str = ""
    exit_code: int = 0
    timed_out: bool = False
    duration_s: float = 0.0
    input_tokens: int = 0   # includes cache reads and writes
    output_tokens: int = 0
    models: tuple = ()


def claude_cmd(prompt_file, max_turns, max_budget, deny=(), add_dirs=(), model=None):
    prompt = Path(prompt_file).read_text()
    cmd = ["claude", "-p", prompt, "--output-format", "json",
           "--max-turns", str(max_turns), "--max-budget-usd", str(max_budget),
           "--dangerously-skip-permissions", "--no-session-persistence",
           # Keep the user's personal settings out of the measurement.
           "--setting-sources", "project,local"]
    if model:
        cmd += ["--model", model]
    for d in add_dirs:
        cmd += ["--add-dir", str(d)]
    if deny:
        rules = []
        for p in deny:
            for tool in ("Read", "Edit", "Write"):
                rules.append(f"{tool}(/{Path(p).resolve()}/**)")
                rules.append(f"{tool}(/{Path(p).resolve()})")
        cmd += ["--disallowedTools", *rules]
    return cmd


def run_agent(prompt, cwd, out_dir, cfg, max_turns, max_budget, deny=(), add_dirs=()):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = out_dir / "prompt.md"
    prompt_file.write_text(prompt)
    if cfg.get("agent_cmd"):
        cmd = [a.replace("{prompt_file}", str(prompt_file)).replace("{cwd}", str(cwd))
               for a in cfg["agent_cmd"]]
    else:
        cmd = claude_cmd(prompt_file, max_turns, max_budget, deny, add_dirs, cfg.get("model"))
    start = time.time()
    res = AgentResult()
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                              timeout=cfg["agent_timeout_s"], stdin=subprocess.DEVNULL)
        stdout, stderr, res.exit_code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        res.timed_out, res.exit_code = True, -1
    res.duration_s = round(time.time() - start, 1)
    (out_dir / "agent.stdout").write_text(stdout)
    (out_dir / "agent.stderr").write_text(stderr)
    data = _last_json(stdout)
    res.cost = float(data.get("total_cost_usd") or data.get("cost_usd") or 0.0)
    res.turns = int(data.get("num_turns") or 0)
    res.result = str(data.get("result") or stdout[-4000:])
    usage = data.get("usage") or {}
    res.input_tokens = sum(int(usage.get(k) or 0) for k in
                           ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    res.output_tokens = int(usage.get("output_tokens") or 0)
    res.models = tuple(sorted((data.get("modelUsage") or {}).keys()))
    return res


CLAIM_RE = re.compile(r"\b(fix(ed)?|resolved|implemented|done|complete[sd]?|tests? (now )?pass(es|ing)?)\b", re.I)
DOUBT_RE = re.compile(r"\b(could ?n[o']t|cannot|can't|unable|not able|failed to|gave up|unsure)\b", re.I)


def claims_success(text):
    """Does the agent's final message say it succeeded? A claim, not evidence."""
    tail = str(text)[-1500:]
    return bool(CLAIM_RE.search(tail)) and not DOUBT_RE.search(tail)


def _last_json(text):
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    try:
        return json.loads(text)
    except ValueError:
        return {}
