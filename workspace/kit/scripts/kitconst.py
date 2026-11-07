"""purpose: shared constants for gates: test-file globs, protected paths, code extensions and the per-type rules.

Not policy: repos cannot change these through policy.yml. Matching is case-insensitive.
"""
import fnmatch

TEST_GLOBS = ["tests/*", "test/*", "spec/*", "features/*", "*/tests/*", "*/test/*", "src/test/*",
              "*.tests/*", "*unittests*/*", "*integrationtests*/*", "*_test.*", "*.test.*", "*_spec.*",
              "*test.*", "*tests.*", "*spec.*", "test_*", "*/test_*", "*.feature", "*conftest.*", "safety-net/*"]
NOT_PRODUCTION = TEST_GLOBS + ["openspec/*", "docs/*", "*.md"]
# Files that steer the agent or run on checkout or in CI. A human changes them in their own PR.
# Keep in step with HIGH_RISK in forge/tangle.py.
PROTECTED = ["docs/ai/policy.yml", "docs/ai/policy-signoff.json", "kit/*", "kit.manifest.yml", "claude.md",
             "*/claude.md", ".claude/*", "*/.claude/*", ".mcp.json", "*/.mcp.json", ".github/*", ".gitlab-ci.yml",
             ".husky/*", ".vscode/*", ".pre-commit-config.yaml", ".git/*"]
SKIP_DIRS = {".git", "node_modules", "vendor", "openspec", "docs", "kit", "dist", "build", "bin", "obj",
             "__pycache__", ".venv", "venv", "target"}
CODE_EXT = (".py", ".php", ".java", ".kt", ".cs", ".vb", ".js", ".ts", ".tsx", ".jsx", ".go", ".rb",
            ".pas", ".dpr", ".c", ".cpp", ".h", ".scala", ".swift", ".rs")
TEST_EXT = CODE_EXT + (".feature", ".robot")

# Per work-item type. A type can only tighten: forbid production changes or add a gate, never drop one.
TYPES = {
    "story": {}, "nfr": {}, "bug": {}, "hotfix": {}, "chore": {}, "refactor": {},
    "spike": {"no_production": True},
    "docs": {"no_production": True},
    "tests": {"add": ["flaky"], "no_production": True},
}
NO_REQUIREMENT_TYPES = {"chore", "refactor", "spike", "docs"}


def matches(path, globs):
    p = path.lower()
    return any(fnmatch.fnmatchcase(p, g.lower()) for g in globs)


def is_test_file(path):
    return matches(path, TEST_GLOBS)
