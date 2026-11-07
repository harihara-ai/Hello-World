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

## Not run
- CI on koa (Actions on the fork must be enabled by the owner); baseline; rulesets; slices; commons-lang install.
