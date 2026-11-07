purpose: the new direction after the pilot's first day: honest status, a scale ladder, debt repos, reliability, autonomy and its price.

# Direction: from "works on small slices" to "reliable at scale, then autonomous" (2026-11-07)

## 1. Where we really are (evidence, not hope)
| Question | Answer today | Evidence |
| --- | --- | --- |
| Complex, multi-file work items | **Not shown.** The largest slice was 4 files and about 50 lines; no change had more than 2 slices | `evidence/pilot.md` |
| Slicer reliability | **Not reliable yet.** `/slice` is the agent applying rules; `gate.granularity` only scores the numbers the agent wrote | KOA-1 split worked; estimates off by up to 37% (35 to 48 lines); P04: the scan missed a test that pinned the bug |
| Repos with tech debt (no CI, no tests) | **Not tried.** Both pilot repos were easy: 99.9% and 96.6% coverage, working CI | `docs/ai/baseline.md` in each repo |
| Reliability | 6 of 6 slices passed first time; 0 false alarms; 2 real bugs fixed. With 6 slices that only proves a **one-sided 95% lower bound of about 61%** | 0.05^(1/6) = 0.607 |
| Autonomy | Steps were hand-run from the command files by one interactive session; a human merged every PR | this session |

What holds up: the gates are deterministic, run in CI from a protected branch, and caught every planted trap (22/22).
What is weak: everything before the gates (impact scan, sizing, spec quality) is agent judgement with no measurement.

## 2. Make the slicer measurable before making it bigger
1. **Measured scan, not declared.** `/slice` writes `inputs/impact.json` from tools (ctags or Serena symbols, `grep` of
   callers and of tests that assert current values, coverage report per file). The granularity input is computed
   from it; the agent may only add, never lower, numbers. A script, tests first.
2. **Plan-vs-actual check.** At `done`, compare the diff with the plan: files outside the scan (already a fail),
   lines and files over the estimate by more than 50% (a reported miss, fed to `metrics.csv`).
3. **Spike before plan for bugs and refactors** (P04, now in the bug playbook): run the touched tests with a
   throwaway change; record tests that pin current behaviour.
4. **Score the slicer itself:** estimate error (lines, files), scan misses (files changed but not scanned), and
   re-plans per change. Targets: median line error under 30%, scan misses under 5% of changed files.

## 3. Scale ladder (baby steps; do not climb until the step's exit holds)
| Step | Work item | Exit criteria (all) |
| --- | --- | --- |
| S1 (done) | 1 slice, 1-2 modules, under 60 lines | first-attempt pass, gates green, human review under 5 min |
| S2 | 1 change, 2-3 slices in order, 3-6 files | slices merge in order; no scan miss; estimates within 50% |
| S3 | cross-module change with a public contract (API shape, config key) | contract-first slice; consumer slice; no regression |
| S4 | epic: 3 changes, 8-12 slices, a re-plan in the middle | `<name>-2` folder flow works; state resumes from files in a new session |
| S5 | a debt repo (L0 or L1, section 4): no CI or no tests | Slice 0 characterization lands first; readiness goes up one level |
| S6 | 10 work items in a queue, run unattended to each human gate (section 6) | no human help between gates; budget and time caps hold |
At each step run at least 5 items before moving on; one escape or one gate bypass sends you back a step.
Pick S2-S4 items from real backlog in koa and commons-lang (e.g. a new `ctx` helper used by `response` and
`request`; a `StringUtils` feature with 3 overloads and docs).

## 4. Repos with tech debt
Use the readiness levels of spec 18.1 (L0 opaque to L4 accelerated). Rules:
- **No CI (L0, L1):** the gates are only advice until CI runs them (an agent controls its own checkout). First change
  is always the CI recipe from INSTALL plus a ruleset. No CI host at all: a human runs the gate script on a clean
  machine before merge and signs the result; label every PR "gate not enforced".
- **No tests:** Slice 0 per touched module: characterization or golden-master tests at the outermost seam, green on
  the old code, merged alone. Coverage gate starts from that baseline (ratchet), never from a target.
- **No coverage tool (Delphi, old .NET):** signed `min_changed_line_coverage: 0`; mutation or approval tests become
  the main control; review time goes up, so slices go down (legacy limits are tighter, spec 11.3).
- **Flaky or machine-dependent tests:** quarantine with a ticket (done once: CL-Q1), never delete.
- **Pilot needed:** a third repo that is really legacy (PHP or .NET, low coverage, manual build). Not run yet.

## 5. Reliability: what we can promise and how to prove it
No system can guarantee correctness. The claim we can make is a **measured rate with a confidence bound**, plus
**layers** so one miss is not an escape:
| Layer | Catches | Measured by |
| --- | --- | --- |
| Spec review by a human (G1) | wrong intent | re-plans, spec defects found later |
| Deterministic gates in CI (G3) | scope, coverage, trace, red check, injection, protected files | trap suite 22/22; false-alarm rate |
| Mutation score on changed lines | weak tests (J04, J05) | score per PR; survivors fixed |
| Human code review (G4) | the rest | review minutes; comments per PR |
| Escape log after merge | what all layers missed | escapes per slice, with root cause |
How many clean slices prove a rate (zero failures, one-sided 95%): **29 slices for at least 90%; 59 for at least
95%; 299 for at least 99%.** One failure raises the count (about 46 for 90%, 93 for 95%). Measure per repo type.
Also: re-run the trap suite on every kit change (T8), add every escape as a new trap, and keep a monthly canary.

## 6. Autonomous SDD server (after S5 holds)
Shape: a queue of tickets; a dispatcher starts one sandboxed agent session per ticket; each session runs `/genie`
up to the next human gate (plan PR, then code PR), writes `status.md`, opens the PR and stops. A merge webhook or a
schedule resumes the ticket in a fresh session from `status.md`. Humans still merge every PR (G1, G4).
- **Where it can run:** Claude Code headless (`claude -p`) or the Agent SDK in a container, Claude Code cloud
  sessions started by a scheduled task, or an OpenCode container with the same kit (commands are plain Markdown;
  the gates are Python and need no model). This session already proves the cloud sandbox can do every step.
- **Must have before unattended runs:** (a) its own bot account that is not a code owner (N01 fix a, dropped for
  the pilot, comes back here: without it no human review is forced on AI PRs); (b) per-ticket caps on attempts,
  tokens, wall time and CI minutes, enforced by the dispatcher, not the agent; (c) one ticket per sandbox, no shared
  credentials, read-only network except the git host and package registries; (d) a kill switch (`STOP` file or
  queue flag) and a daily report; (e) the injection gate on every ticket text.
- **Start small:** 1 ticket at a time, then 3 in parallel on different modules, then a nightly batch.

## 7. Price of reliability and robustness (estimates; measure in S2-S4 and replace)
| Item | Per slice (estimate) | Basis |
| --- | --- | --- |
| Human review | 1-3 min for under 60 lines; expect 5-15 min at S2-S3 | owner's figures today: 11 min (koa, 4 PRs), 5 min (commons-lang) |
| CI time (hosted) | koa about 3 min; commons-lang about 10 min per PR (tests, gate, mutation) | job timings today |
| Agent tokens | **not measured**; record from S2 on (`metrics.csv` tokens column) | - |
| Owner time on setup | about 10 taps per repo (Actions, merge, ruleset) | today |
Cost to reach each confidence level, per repo type, at today's two PRs per slice:
| Target | Clean slices | PRs | Human review (at 5 min/PR) | Calendar (5 slices a day) |
| --- | --- | --- | --- | --- |
| 90% first-attempt, 95% confidence | 29 | 58 | about 5 h | 6 days |
| 95% | 59 | 118 | about 10 h | 12 days |
| 99% | 299 | 598 | about 50 h | 2-3 months |
Recommendation: aim for **90% per repo type** now (one modern, one legacy), 95% before the autonomous batch (S6),
and treat 99% as a program goal measured by escapes, not by pre-merge counts.

## 8. Prevention first (RCA SOP)
Every finding now goes through `hardening/RCA.md`: correct the case, N-whys to the systemic root, prevent the
class. The pilot's findings cluster into 4 roots (`hardening/roots.md`): R1 the kit's own workflows are never
executed end to end by a test (P01, P03, P05, M01, N01); R2 protected files are a hand-kept list; R3 human setup
steps are not verified; R4 sizing and scope are unmeasured judgement (P04, F17).

## 9. Home and next sessions
Owner decision (2026-11-07): the kit moves to a new private repo **harihara-ai/northstar-kit** (owner creates it
empty). Its CI runs forge lint, selftest, traps and the golden-path suite on every PR, under a ruleset.
1. **Move and guard:** push this branch's history to northstar-kit `main`; CI for lint, selftest, run_traps; ruleset.
2. **R1 golden-path suite** (tests first): install, bootstrap, story, bug, refactor, quarantine and upgrade on
   fixture repos, through `gate_check` as CI calls it; P01, P03, P05 RED on 1.0.4, GREEN on 1.0.5.
3. **R4 slicer script** (section 2), then **S2** on koa with tokens and minutes recorded.
