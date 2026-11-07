# Playbook: spike

purpose: answer one question inside a time box; the output is a findings document, never merged production code.

1. **Question and time box.** Write both at the top of the findings file. A spike needs no change folder.
2. **Explore.** Prototype on a throwaway branch that is never merged. Use subagents for reading.
3. **Findings.** Write `docs/ai/decisions/<KEY>-<slug>.md`: question, time box, options tried, evidence, recommendation, open risks.
4. **Close.** The PR holds only that file. CI passes it as a docs-only PR (no change folder); any other file fails.
5. **Follow-up.** Each recommendation that needs work becomes a new ticket.
