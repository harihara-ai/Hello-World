purpose: Gold pilot (session C) evidence: repos, installs, slices, metrics and findings.

# Pilot (started 2026-11-07)
Repos (owner choice): legacy `harihara-ai/commons-lang` (Java, Maven, JaCoCo, PIT), modern `harihara-ai/koa`
(JS, node --test, c8 lcov, Stryker). Both are forks: real use for four weeks is the owner's call.

## koa install
- Install PR koa#1 (branch `northstar/install`): install zip 1.0.4 unzipped at the root (no root CLAUDE.md before;
  new one holds `@kit/CLAUDE.md`), `.gitignore` lines, CODEOWNERS (trial list minus requirements-ci.txt, plus
  `package-lock.json`, `.c8rc*`), `northstar-ci.yml` (trial recipe; Node 22; gate job installs test tools from
  `../approved` with `npm ci --ignore-scripts` and sets `NODE_PATH` to them; test cmd `node --test {tests}`).
- Local: `node --test` 438 pass, 2 fail (`load-with-esm` needs `dist/`, built by `npm run build`; not built here).
  c8 lcov paths are repo-relative (`SF:lib/application.js`).
- Local gate on the install commit: exit 1, "found none, but code or tests changed: ['.gitignore',
  'kit/templates/scenario.feature']". No CI run on koa#1 (workflow not on master yet), so it does not block the
  install; it would block an upgrade PR (finding P01 below).

- Owner merged koa#1 (`e6f68d6`). Push run 42382537286: `baseline` success, artifact `coverage-baseline` (lcov).
  Owner added the master ruleset; read via `rules/branches/master`: deletion, non_fast_forward, pull_request
  (code-owner review, 0 approvals), required checks `tests`, `gate`.
- `/bootstrap` (hand-run from `.claude/commands/bootstrap.md`): ctags installed with the owner's OK (codenav ctags,
  Serena not installed); tracker file (owner choice; Issues off). Tests with `dist/` built: 440 pass; lines 99.9%,
  branches 99.09%. Local gate: pass, "no change folder: only docs or human-owned files changed". PR koa#2.

## commons-lang install
- Full suite here (Java 21, Maven, JaCoCo via commons-parent, rat/japicmp/checkstyle/pmd/spotbugs/javadoc skipped):
  89127 tests, 0 failures, 16 skipped, 204 s; JaCoCo XML total 96.57%, 216 files; `cov_import.match` maps
  `src/main/java/org/apache/commons/lang3/CharUtils.java` to the JaCoCo path.
- Maven takes class names, so `{tests}` goes through `.github/northstar/mvn-tests.sh` (tracked, run from
  `../approved`): exit 0 on CharUtilsTest + BitFieldTest (4 s), 1 with `CharUtils.isAscii` broken, 5 with no files.
- Install PR commons-lang#1. Workflows appeared once the PR opened (no enable step). Merge was blocked by a classic
  branch protection rule (1 approving review), hidden in the phone layout; owner deleted it (desktop site) and merged
  (`0fa5938`). Apache's own Java CI and Dependency Review failed on #1 (not required; not read further).
- First baseline (run 42386280045) FAILED: 9 of 89127, all `FastDatePrinterTimeZonesTest.testCalendarTimezoneRespected`
  (SimpleDateFormat MDT/CDT/PDT vs FastDateFormat MST/CST/PST, US zones, 2026-11-07, runner Temurin 21). Same suite
  passed locally (OpenJDK 21.0.12). Owner chose quarantine (INSTALL, safety-net playbook): PR commons-lang#2,
  `@Disabled` + `docs/ai/quarantine.md` (CL-Q1). JDK or tzdata root cause: not investigated.

## Findings
```
id: P01
severity: minor
location: kit gate_check (no change folder rule); kit/INSTALL.md Upgrade
evidence: local gate_check auto on koa#1: kit/templates/scenario.feature counted as a test, .gitignore as code
problem: a kit upgrade PR (delete kit/, unzip) fails the gate although every file is human-owned
proposed_fix: treat PROTECTED paths and .gitignore as human-owned in the no-change-folder rule; or INSTALL: admin
  merges upgrade PRs. Decide with pilot data.
```
```
id: P02
severity: minor
location: kit/scripts/kitconst.py PROTECTED; INSTALL build files list
evidence: c8 reads .c8rc / .c8rc.json (and package.json "c8"); neither .c8rc* nor package-lock.json is listed
problem: a c8 config file can exclude files from coverage without a code-owner review
proposed_fix: add `.c8rc*` to PROTECTED (next to .nycrc*) and `package-lock.json` to the INSTALL build files list
```

```
id: P03
severity: minor
location: kit/.claude/commands/implement.md step 4; gate diff_scope (change folder rule)
evidence: KOA-1 code branch, local gate_check done: diff_scope fail "a change folder holds only the plan and
  evidence: openspec/changes/KOA-1-response-json/metrics.csv"; status.md passed
problem: /implement tells the agent to append metrics.csv, which the done gate then refuses
proposed_fix: one of: allow metrics.csv in the change folder, or have /implement keep metrics outside the PR
  (pilot keeps them in this file for now)
```

## koa slices
| Ticket | Type | Plan PR | ready (CI) | Code PR | done | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| KOA-1 response.json / ctx.json | story | koa#3 (merged `8024d94`) | pass | koa#4 | CI pass: stage done, 6 gates, changed-line coverage 100%, red_check exit_base 1 (job 128436292711) | first ready run: granularity split (5 scenarios, 2 modules); split by requirement; 1 attempt per slice |
| KOA-2 HEAD Content-Length 2 for web stream bodies | bug (found in the hunt) | koa#5 (merged `d4a3968`) | CI pass | koa#6 | CI pass: done, 6 gates, changed-line coverage 100%, red_check exit_base 1 (job 128438025988) | first code run broke `respond.test.js`, which asserted the buggy length; owner widened plan #5 (unmerged) to that assertion |
| KOA-3 refactor lib/only.js | refactor | koa#7 (merged `3553675`) | CI pass | koa#8 | CI pass (job 128439471377); red_check n/a for refactor | S0 CHAR tests passed on old code; first draft pinned a wrong getter assumption (read once; really twice), dropped and spec corrected before merge; only.js 9 to 3 lines, branches 5 to 4 |

Owner review: koa#4 plus koa#2 took 5 min, koa#6 4 min, koa#8 2 min (owner). koa#6 took 4 min (owner).
Metrics (KOA-1): S1 est 35, actual 48 lines, 2 files, 1 attempt; S2 est 20, actual 24, 2 files, 1 attempt.

```
id: P04
severity: minor
location: kit/.claude/commands/slice.md step 2 (impact scan); capability codenav (ctags)
evidence: KOA-2: impact scan listed length.test.js; the fix broke respond.test.js "should keep Response headers",
  which asserted HEAD content-length 2 (the bug). Found only by the full test run, after the plan PR was open.
problem: a symbol scan finds callers, not tests that pin the current behaviour; a bug plan can miss a test it must edit
proposed_fix: /slice for a bug: run the fix spike's full test suite before the plan PR, or grep tests for the
  wrong value; record any test that pins the bug in the spec
```

```
id: P05
severity: minor
location: kit/INSTALL.md (first baseline, quarantine); northstar-ci recipe
evidence: commons-lang: baseline failed on a machine-dependent test; with no baseline every gate run fails at the
  baseline download step, so the quarantine PR itself cannot pass the gate
problem: INSTALL says quarantine first but not how that PR gets merged before a baseline exists
proposed_fix: INSTALL: run the full suite on the CI runner in the install PR (tests job), quarantine in the same
  install PR; or say the quarantine PR is merged before the ruleset is added
```

## Not run
- CI on koa (Actions on the fork must be enabled by the owner); baseline; rulesets; slices; commons-lang install.
