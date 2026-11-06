purpose: the fixed format every reviewer finding must use.

One finding per block:

```
id: R<role>-<round>-<nn>
severity: blocker | major | minor
location: section number or file path
evidence: what you saw or ran (quote under 15 words, or command and short output)
problem: one sentence
proposed_fix: one or two sentences
confidence: high | medium | low
```

Severity: blocker = cannot work or a gate can be bypassed; major = likely to fail on real repos or confuse users; minor = polish.
No finding without evidence. No edits by reviewers.
