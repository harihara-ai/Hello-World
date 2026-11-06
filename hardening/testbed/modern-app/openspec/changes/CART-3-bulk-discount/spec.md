# Change: CART-3-bulk-discount
Ticket: CART-3
Type: story

## Problem
A cart with 12 units pays the same unit price as a cart with 1 unit.

## Outcome
Carts with 10 or more units get 5 percent off the subtotal.

## Requirements

### REQ-CART-001: 5 percent off at 10 units
Scenario: happy - 10 units at 10.00
  Given a cart with 10 units at 10.00
  When the discount is computed
  Then the discount is 5.00
  Level: unit
Scenario: error - negative quantity rejected
  Given a cart line with quantity -1
  When the discount is computed
  Then a ValueError is raised
  Level: unit

### REQ-CART-002: No discount below 10 units
Errors: none
Scenario: happy - 9 units at 10.00
  Given a cart with 9 units at 10.00
  When the discount is computed
  Then the discount is 0.00
  Level: unit

## Non-functional
none

## Out of scope
Coupons and loyalty points.

## Assumptions
Prices are in one currency.

## Open questions
none
