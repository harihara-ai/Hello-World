purpose: working source for the scripts components of the kit (tangled into workspace/).

# Scripts

Helpers used by gates and commands.

## script.gateio

Shared gate I/O so gates stay one-job files. Rejects NaN and Infinity (round 1 F04).

````python file=kit/scripts/gateio.py
"""purpose: shared I/O for gates: read JSON input (file or '-'), print JSON result, return the exit code."""
import json
import sys


class UsageError(Exception):
    pass


def _no_constant(name):
    raise UsageError("%s is not allowed in gate input" % name)


def read_input(argv):
    if len(argv) != 2:
        raise UsageError("usage: %s INPUT.json|-" % argv[0])
    if argv[1] == "-":
        return json.load(sys.stdin, parse_constant=_no_constant)
    with open(argv[1], encoding="utf-8") as fh:
        return json.load(fh, parse_constant=_no_constant)


def finding(rule, message, where="", severity="fail"):
    return {"rule": rule, "severity": severity, "where": where, "message": message}


def emit(gate, findings, **extra):
    ok = not any(f["severity"] == "fail" for f in findings)
    print(json.dumps(dict({"gate": gate, "pass": ok, "findings": findings}, **extra), indent=1))
    return 0 if ok else 1


def run(gate, check, argv=None):
    """Call check(payload) -> (findings, extra). Exit 0 pass, 1 fail, 2 bad input."""
    argv = argv or sys.argv
    try:
        payload = read_input(argv)
        if not isinstance(payload, dict):
            raise UsageError("input must be a JSON object")
        findings, extra = check(payload)
    except (UsageError, OSError, ValueError, KeyError, TypeError) as e:
        print(json.dumps({"gate": gate, "pass": False, "error": str(e), "findings": []}))
        return 2
    return emit(gate, findings, **extra)
````

## script.kitconst

Round 1: fixed lists (test globs, protected paths, per-type gates) that policy cannot loosen.

````python file=kit/scripts/kitconst.py
"""purpose: shared constants for gates: test-file globs, protected paths, code extensions and the per-type rules.

Not policy: repos cannot change these through policy.yml. Matching is case-insensitive.
"""
import fnmatch
import re

TEST_GLOBS = ["tests/*", "test/*", "spec/*", "features/*", "*/tests/*", "*/test/*", "src/test/*",
              "*.tests/*", "*unittests*/*", "*integrationtests*/*", "*_test.*", "*.test.*", "*_spec.*",
              "test_*", "*/test_*", "*.feature", "*conftest.*", "safety-net/*"]
TEST_NAME = re.compile(r"(^|[a-z0-9_])(Tests?|Spec|IT)\.[A-Za-z0-9]+$")  # FeeTest.php, not Contest.php
NOT_PRODUCTION = ["openspec/*", "docs/*", "*.md"]
DOCS = ["docs/*", "*.md"]
# Files that steer the agent or run on checkout or in CI. A human changes them in their own PR.
# Keep in step with HIGH_RISK in forge/tangle.py.
PROTECTED = ["docs/ai/policy.yml", "docs/ai/policy-signoff.json", "kit/*", "kit.manifest.yml", "claude.md",
             "*/claude.md", ".claude/*", "*/.claude/*", ".mcp.json", "*/.mcp.json", ".github/*", ".gitlab-ci.yml",
             ".husky/*", ".vscode/*", ".pre-commit-config.yaml", ".git/*",
             # coverage and test-runner config decides what is measured
             ".coveragerc", "*/.coveragerc", "phpunit.xml", "phpunit.xml.dist", "*.runsettings", ".nycrc*", ".c8rc*",
             "jest.config.*", "codecov.yml", ".codecov.yml"]
COVERAGE_IGNORE = ["pragma: no cover", "@codecoverageignore", "excludefromcodecoverage", "istanbul ignore",
                   "c8 ignore", "coverage:ignore", "lcov_excl", "@generated"]
# Code that writes the coverage tool's own data could mark any line as run (M02). Fails on any changed code line.
COVERAGE_API = re.compile(r"\b(?:import|from)\s+coverage\b|__coverage__|\bxdebug_|\bpcov\\|org\.jacoco|\bcoverlet\b", re.I)
# The only files a change folder may hold (an allowlist: runners pick up other files, e.g. pytest doctests in *.txt).
CHANGE_FOLDER_FILES = ["*.md", "metrics.csv", "inputs/*.json", "gates-*.json", "evidence/*.xml", "evidence/*.json", "evidence/*.info",
                       "evidence/*.png", "evidence/*.jpg", "evidence/*.svg", "evidence/*.pdf"]
SKIP_DIRS = {".git", "node_modules", "vendor", "openspec", "docs", "kit", "dist", "build", "bin", "obj",
             "__pycache__", ".venv", "venv", "target"}
CODE_EXT = (".py", ".php", ".java", ".kt", ".cs", ".vb", ".js", ".ts", ".tsx", ".jsx", ".go", ".rb",
            ".pas", ".dpr", ".c", ".cpp", ".h", ".scala", ".swift", ".rs")
TEST_EXT = CODE_EXT + (".feature", ".robot")

# Per work-item type. A type can only tighten: forbid production changes or add a gate, never drop one.
TYPES = {
    "story": {}, "nfr": {}, "bug": {}, "hotfix": {}, "chore": {}, "refactor": {},
    "spike": {"no_production": True},
    "tests": {"add": ["flaky"], "no_production": True},
}
RED_TYPES = {"story", "nfr", "bug", "hotfix"}  # changed tests must fail on base code; other types must pass there
NO_REQUIREMENT_TYPES = {"chore", "refactor", "spike"}  # docs-only PRs need no change folder at all


def matches(path, globs):
    p = path.lower()
    return any(fnmatch.fnmatchcase(p, g.lower()) for g in globs)


def is_test_file(path):
    return matches(path, TEST_GLOBS) or bool(TEST_NAME.search(path.rsplit("/", 1)[-1]))


def is_production(path):
    return not is_test_file(path) and not matches(path, NOT_PRODUCTION)
````
