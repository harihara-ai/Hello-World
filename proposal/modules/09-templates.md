purpose: working source for the templates components of the kit (tangled into workspace/).

# Templates

Skeletons copied into target repos.

## template.spec

Sections 10.1, 10.2. Format that gate.spec_lint reads.

````md file=kit/templates/spec.md
# Change: <name>

purpose: change spec skeleton checked by gate.spec_lint; replace every <placeholder>.

Ticket: <KEY>
Type: <story|bug|hotfix|chore|refactor|spike|nfr|docs|tests>

## Problem
<what is wrong today, with a concrete example>

## Outcome
<what is true after the change, with numbers>

## Requirements

### REQ-<AREA>-001: <one behaviour, no "and">
Scenario: happy - <concrete case>
  Given <state with values>
  When <action>
  Then <observable result with values>
  Level: <unit|api|behaviour|ui>
Scenario: error - <concrete failure>
  Given <state>
  When <action>
  Then <error result>
  Level: <unit|api|behaviour|ui>

## Non-functional
<each line has a number or a named standard, or write: none>

## Out of scope
<what this change does not do>

## Assumptions
<or: none>

## Open questions
none
````

## template.feature

Sections 16.1, 16.3.

````gherkin file=kit/templates/scenario.feature
# purpose: Gherkin skeleton for behaviour tests; business language only, tags carry REQ ID and tier.
@regression @tier1 @REQ-AREA-001
Feature: <business capability>

  Scenario: <one behaviour with concrete values>
    Given <state set up through an API or data builder, not the UI>
    When <one business action>
    Then <observable result>
````

## template.ticket

Section 18.2.

````md file=kit/templates/ticket.md
# <KEY>: <title>

purpose: ticket skeleton for the file tracker and for rewriting weak tickets before intake.

Type: <story|bug|hotfix|chore|refactor|spike|nfr|docs|tests>

## Why
<problem and who has it>

## What done looks like
- <observable result with a number>

## Not included
- <out of scope>
````

## template.pr

Section 10.5.

````md file=kit/templates/pr.md
# <KEY>: <title>

purpose: pull request skeleton with the trace table and gate results.

## Summary
<three lines>

## Trace
| Requirement | Scenario | Test | Commit |
| --- | --- | --- | --- |
| REQ-<AREA>-001 | <scenario> | <test name> | <sha> |

## Gates
- ready: <pass/fail, link to gates-ready.json>
- done: <pass/fail, link to gates-done.json>

## Evidence
RED and GREEN per scenario: `openspec/changes/<name>/evidence.md`.

## Out of scope noticed
- <or: none>
````
