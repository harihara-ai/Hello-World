# Change: INV-7-late-fee
Ticket: INV-7
Type: story

## Problem
Invoices paid 45 days late pay no fee.

## Outcome
Invoices paid more than 30 days late carry a 2 percent fee.

## Requirements

### REQ-FEE-001: 2 percent fee after 30 days
Scenario: happy - 31 days late on 100.00
  Given an invoice total of 100.00
  When it is paid 31 days late
  Then the fee is 2.00
  Level: unit
Scenario: error - negative days rejected
  Given an invoice total of 1.00
  When days late is -1
  Then an InvalidArgumentException is thrown
  Level: unit

### REQ-FEE-002: No fee up to 30 days
Errors: none
Scenario: happy - 30 days late on 100.00
  Given an invoice total of 100.00
  When it is paid 30 days late
  Then the fee is 0.00
  Level: unit

## Non-functional
none

## Out of scope
Changing invoice_total.

## Assumptions
Days late is computed by the caller.

## Open questions
none
