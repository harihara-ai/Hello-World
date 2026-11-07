purpose: SOP for every finding, escape, false alarm or human friction: correct fast, then find the systemic root cause and prevent the class.

# Root cause SOP (prevention first)

## When it runs
Any new finding (`findings.md`), any escape after merge, any gate false alarm, any step where a human had to rescue
the flow (a hidden setting, a blocked merge, a manual fix). One RCA per finding; cluster findings that share a root.

## Steps
1. **Contain and correct (same day).** Smallest fix that makes the current case safe. Record it as `corrective`.
   Never wait for the RCA to stop harm; never stop at the correction either.
2. **N-whys to saturation.** Ask "why did our system allow this?" (not "who"). Each answer must be a fact you can
   point to (a file, a missing test, a run). Stop only when one of these holds:
   - the next why leaves our control (a vendor, a law of the platform), or
   - the answer is a missing **feedback loop or standard** (nothing would ever tell us), or
   - the answer is a root already in `roots.md` (then link it).
   Usually 4 to 7 whys. Stopping at "the agent made a mistake" or "the rule was missing" is not saturated: ask why
   nothing caught the mistake or the gap before a human did.
3. **Classify the root** (one of): missing executable test of a flow; check enumerated by hand; human-only step
   with no verification; unmeasured judgement; spec or doc drift; platform behaviour we assumed; scope we never tried.
4. **Cluster.** Add the root to `roots.md` or link an existing one. A root with two or more findings is systemic.
5. **Preventive actions**, strongest first; pick the strongest that is affordable:
   1. *Eliminate*: remove the step or design out the failure (a list the code derives, not one a human keeps).
   2. *Detect at the earliest stage*: a test or check that fails before review (bootstrap probe, contract test, CI).
   3. *Standardize*: one template or script instead of prose.
   4. *Document*: a sentence in a playbook. Weakest; use only with one of the above, or when nothing else fits.
6. **Prioritize** across open roots by leverage, not by recency:
   `score = (findings in the class + likely future ones) x severity weight (blocker 5, major 3, minor 1) / effort (S 1, M 2, L 4)`.
   Do the top root first even if its findings are minor. Correct the rest individually only when they are harmful.
7. **Verify the prevention.** Add the original case (and one variant) as a test or trap; show it RED before and GREEN
   after; then watch the class: a new finding with the same root reopens the root, not just the finding.
8. **Record** in the finding: `root: R<n>`, `corrective:`, `preventive:`, `verified_by:`. Keep `roots.md` current.

## Guardrails
- **No governance machinery.** Pick the smallest prevention that stops the class: reuse an existing test, list or
  script before adding one; a new gate, flag, file or process needs a root with two or more findings and a sentence
  saying why nothing smaller works. Delete a prevention that has caught nothing after two kit releases.
- One prevention in flight per root. Corrections for minor findings can wait for the root's prevention.
- Time box: 15 minutes of whys per finding; more only for a blocker or an escape.
- Prevention never weakens a gate or skips a test. If prevention needs a kit change, it goes through tests first and a
  human pin like any other change.
- Report what you ran; a prevention that is planned but not verified is "not run".
