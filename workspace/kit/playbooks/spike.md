# Playbook: spike

purpose: answer one question inside a time box; the output is a findings document, never merged production code.

1. **Question and time box.** Write both in `spec.md` (Type: spike).
2. **Explore.** Prototype on a throwaway branch. Use subagents for reading.
3. **Findings.** Write `docs/ai/decisions/<KEY>-<slug>.md`: question, options tried, evidence, recommendation, open risks.
4. **Close.** PR contains only the findings file. `gate.diff_scope` with `impact_scan: ["docs/*"]` enforces it.
5. **Follow-up.** Each recommendation that needs work becomes a new ticket.
