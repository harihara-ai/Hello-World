# Repo A: more-itertools

Upstream: https://github.com/more-itertools/more-itertools at `1ea82a7`. Pure Python, no dependencies.
The full suite runs in about 36 seconds here.

## Judge configuration (frozen)

- `test_cmd`: `python3 -m unittest -q {tests}`
- `regression_cmd`: `python3 -m unittest -q`
- split: `time`, held-out fraction 0.34 (the newest commits are held out)
- caps: 30 turns and $2.0 per task, $25.0 per generation, $150.0 total
- model: CLI default (not pinned)

## Mining

88 fix-with-test candidates. 32 were dropped as features or vague reports. 24 were dropped by validation,
either because the hidden tests already pass before the fix, or because they fail even with the fix on
Python 3.11. **32 tasks remain: 21 train, 11 held-out.** All 32 have the regression check enabled.
See `mine.log` for every decision.

Five older train tasks marked ⚠ are features the filter missed: a new parameter or protocol method, with no
new top-level function. They are kept for now. If they turn out to be unsolvable from their one-line
message, a later re-mine can drop them.

| split | task | date | bug report |
|---|---|---|---|
| heldout | `def2dabea8` | 2026-09-14 | Fix one()/only() dropping a falsy user-supplied exception |
| heldout | `6b1907de29` | 2026-09-09 | fix: seekable.peek/bool no longer drop items when maxlen is 0 |
| heldout | `d992be0de9` | 2026-07-12 | Fix stability in running_min and running_max |
| heldout | `958990e22c` | 2026-07-03 | Raise for negative slice sizes in sliced() |
| heldout | `f51a53bfd2` | 2026-06-30 | fix: handle empty interleave_evenly input |
| heldout | `edb3346f83` | 2026-04-10 | Fix empty ranges in numeric_range.__reversed__ |
| heldout | `71b46b06fb` | 2026-04-01 | Issue #1057: Raise exception for invalid size in windowed() |
| heldout | `8089263d23` | 2026-04-01 | Issue: #898: Sync recipe with main docs. Eliminate quadratic fallback. |
| heldout | `be5793a55f` | 2026-02-02 | Two fixes for repeat with iterator arguments |
| heldout | `06f3181912` | 2026-01-02 | Simplify nth_combination_with_replacement. Fix incorrect exception. |
| heldout | `def2d821c0` | 2026-01-02 | Simplify nth_permutation. Fix incorrect exception. |
| train | `b0aa91efbb` | 2025-12-30 | Fix random_product() as well |
| train | `073d23421b` | 2025-12-30 | Fix support for iterators using "repeat" |
| train | `adeda34bd1` | 2025-10-28 | Fix bug for negative inputs to exactly_n(). Optimize code. |
| train | `cf186b5de4` | 2025-10-10 | Fix product_index() with iterator input |
| train | `21d3d88359` | 2025-08-21 | Issue 1003: Multidimensional reshape() (#1062) ⚠ feature-like |
| train | `cca32949f1` | 2025-07-14 | fix last() when __reversed__ is None |
| train | `ae37eb38a1` | 2025-01-11 | Add more sample() tests and fix bug in strict option with counts |
| train | `8ee69910e8` | 2025-01-09 | remove string.format(); fix tests |
| train | `e733192454` | 2024-10-11 | Issue 916: lt only for is_sorted (#917) |
| train | `db67158d79` | 2024-05-02 | Fixed.  Indices need to be sorted. |
| train | `ab72fc8a4e` | 2023-05-21 | Fix unique_in_window to match described behavior |
| train | `cd0a3a87d2` | 2023-04-19 | Issue #707: fix ``iterate()`` to enable ``func`` to raise StopIteratio |
| train | `9245cd04c0` | 2022-11-22 | Fix issue 658 for split_after |
| train | `49a4b3c94b` | 2021-08-01 | Fix bugs in chunked_even |
| train | `fb89af02fd` | 2021-07-12 | fixed repeat_each() to accept infinite iterators as input |
| train | `2e81a562fb` | 2021-03-10 | Fix split_before for an empty collections. |
| train | `fc0bb86f4c` | 2020-05-25 | Slice support for islice_extended  (#429) ⚠ feature-like |
| train | `62411c1618` | 2020-03-29 | Fix spy to make returned iterable immutable |
| train | `3150ad2e05` | 2020-01-11 | Define bucket.__iter__ (#371) ⚠ feature-like |
| train | `39306e8aa5` | 2020-01-11 | maxlen parameter for seekable (#365) ⚠ feature-like |
| train | `e08fff0833` | 2020-01-11 | Make numeric_range an iterable (#363) ⚠ feature-like |

## Smoke test (real `claude -p`, no harness)

`seed try cca32949f1 --max-turns 15 --max-cost 1`: **PASS**, $0.066, 5 turns, 10 s of agent time.
The hidden tests passed (655) and the regression suite stayed green (840). The one-line fix and the full
result are in `smoke-cca32949f1/`. The agent's final message said it had *not* run the tests, so it
claimed nothing. That is honest, and it shows why the Judge's own test run is the evidence.
