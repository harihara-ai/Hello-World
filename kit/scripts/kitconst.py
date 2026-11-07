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
             ".coveragerc", "*/.coveragerc", "phpunit.xml", "phpunit.xml.dist", "*.runsettings", ".nycrc*",
             "jest.config.*", "codecov.yml", ".codecov.yml"]
COVERAGE_IGNORE = ["pragma: no cover", "@codecoverageignore", "excludefromcodecoverage", "istanbul ignore",
                   "c8 ignore", "coverage:ignore", "lcov_excl", "@generated"]
# Code that writes the coverage tool's own data could mark any line as run (M02). Fails on any changed code line.
COVERAGE_API = re.compile(r"\b(?:import|from)\s+coverage\b|__coverage__|\bxdebug_|\bpcov\\|org\.jacoco|\bcoverlet\b", re.I)
# The only files a change folder may hold (an allowlist: runners pick up other files, e.g. pytest doctests in *.txt).
CHANGE_FOLDER_FILES = ["*.md", "inputs/*.json", "gates-*.json", "evidence/*.xml", "evidence/*.json", "evidence/*.info",
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
