"""purpose: shared constants for gates: test-file globs, protected paths and the fixed per-type gate table.

Not policy: repos cannot change these through policy.yml, so a gate cannot be loosened by editing a list.
"""
import fnmatch

TEST_GLOBS = ["tests/*", "test/*", "spec/*", "features/*", "*/tests/*", "*/test/*", "src/test/*",
              "*.Tests/*", "*/Tests/*", "*UnitTests*/*", "*IntegrationTests*/*", "*_test.*", "*.test.*",
              "*_spec.*", "*Test.*", "*Tests.*", "*Spec.*", "test_*", "*/test_*", "*.feature", "safety-net/*"]
NOT_PRODUCTION = TEST_GLOBS + ["openspec/*", "docs/*"]
PROTECTED = ["docs/ai/policy.yml", "docs/ai/policy-signoff.json", "kit/*", "kit.manifest.yml",
             ".claude/*", "CLAUDE.md", ".github/*"]
SKIP_DIRS = {".git", "node_modules", "vendor", "openspec", "docs", "kit", "dist", "build", "bin", "obj",
             "__pycache__", ".venv", "venv", "target"}

# Fixed per work-item type: gates removed from or added to the floor list, and whether production files may change.
TYPES = {
    "story": {}, "nfr": {}, "bug": {}, "hotfix": {},
    "chore": {"drop": ["trace_check"]},
    "refactor": {"drop": ["trace_check"]},
    "spike": {"drop": ["trace_check", "coverage", "granularity"], "no_production": True},
    "docs": {"drop": ["trace_check", "coverage", "granularity"], "no_production": True},
    "tests": {"drop": ["coverage"], "add": ["flaky"], "no_production": True},
}
NO_REQUIREMENT_TYPES = {"chore", "refactor", "spike", "docs"}


def matches(path, globs):
    return any(fnmatch.fnmatchcase(path, g) for g in globs)


def is_test_file(path):
    return matches(path, TEST_GLOBS)
