# Dated cash needs to contribution projection

## Natural owner and contract

Portfolio owns the pure dated reserve rule; Applications composes it with
the existing strategic contribution allocator. The existing CLI dispatches
the new request kind, with the original request and response unchanged.

Input uses caller-supplied USD integer cents, an explicit as-of date and
inclusive reserve horizon, an emergency reserve distinct from the listed
obligations, unique outstanding obligation IDs with due dates and amounts,
existing holdings, target weights, and desired contribution. The caller
must supply all relevant outstanding obligations, including overdue items.
No forecast income, market gain, liquidity from sales, or liability funding
outside the horizon is assumed. No provider, ledger or authorization is added.

Let R = emergency reserve + sum of outstanding obligations due on or before
the horizon. C = min(requested, max(0, cash - R)). If cash < R, C = 0 and
the result is RESERVE_SHORTFALL with no allocation plan. Otherwise use the
existing contribution-only allocator. The result distinguishes requested,
projected and unallocated contribution, shortfall, overdue amount and
obligations excluded by the horizon. All data remain caller supplied.

## Verification

The Lean model proves bounds, reserve protection, maximal feasible
contribution, and monotonicity under additional admitted obligations for
arbitrary finite lists of natural-number amounts. The Python tests check
date selection, duplicate rejection, integer limits, CLI behavior and
conservation over boundary inputs. These are not a universal proof of
Python/date-parser refinement or proof that the caller supplied real data.

```sh
mise run //domains/capital:verify:formal:liability-reserve
domains/capital/scripts/run-strategic-contribution-brief \
  < domains/capital/examples/goal_funded_contribution_r1.json
```

No external financial action, personalized suitability, tax, transaction
cost, future income, currency conversion or market-return validation is
claimed. This rule is a deterministic first-stage liquidity envelope, not
a multi-period stochastic financial plan.
