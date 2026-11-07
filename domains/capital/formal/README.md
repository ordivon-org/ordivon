# Portfolio contribution — model proof versus implementation evidence

The canonical Owner is `Portfolio` in `domains/capital`; there is no Finance
verification service or separate financial authority. This directory contains
one source-adjacent, versioned *mathematical model* of
`src/ordivon_capital/portfolio/strategic_contribution.py`.

## Scope and evidence

`PortfolioContributionR1.smt2` uses Z3 QF_NIA on unbounded mathematical
integers and three symbolically chosen asset deficits (`gap0..gap2`). It
models exact Euclidean quotient/remainder apportionment, priority by remainder
then lexicographic asset ID, and a cash-reserve precondition. Four negated
properties must be UNSAT: residual-cent count in `[0, 2]`; exact cent
conservation; nonnegative/no-sell/reserve preservation; stable three-way tie
priority. The fifth query must be SAT to establish reachable tie behavior
*within this abstract model*, not necessarily under every production policy.
Zero-contribution/zero-denominator and more than three assets are NOT proved
by this model. Source/encoding equivalence, external market data, PostgreSQL,
actual broker orders, and numerical performance are NOT proved.

### Human

From `domains/capital`, execute `mise run verify:formal:contribution` and
expect `unsat, unsat, unsat, unsat, sat`. To see the read-only, real Python CLI
consumer use the repository's existing
`scripts/run-strategic-contribution-brief < examples/strategic_contribution_r1.json`.
The output is an allocation *projection*, not trading authorization.

### Agent

Resolve the existing trusted project Skill `finance-paper-investment` (source:
`.agents/skills/finance-paper-investment/SKILL.md`). Invoke the exact task
above, record the Git source revision, the SMT model digest, Z3 version,
results and the native CLI receipt. State evidence separately:

1. **Specification**: Portfolio contributes only available cash, not reserve;
   always integer minor units, stable asset IDs and target weights.
2. **Model checking**: four UNSAT + one SAT for the stated three-asset model.
3. **Implementation refinement**: UNKNOWN — a symbolic proof against the
   actual Python code has not been established; the consumer example and
   native tests are finite witnesses, not a universal refinement theorem.
4. **Real consumer**: use the native CLI and check `executionAuthorized=false`;
   this remains a pure calculation, not a broker integration.

Never replace tests of external effects or broader-than-three-asset behavior
on the strength of this partial model. Do not count `unknown` / timeout as
`unsat`; use the exact expected output gate in the existing mise task.
The toolchain is reused from `tools/formal/mise.toml`, not installed here.

## All-asset mathematical extension (Lean kernel)

`PortfolioApportionmentGeneral.lean` reuses the pinned Lean 4 compiler and
proves quotient-plus-remainder identities for **arbitrary finite lists of
nonnegative integer gaps**. With positive denominator equal to the sum of
gaps, the sum of floor quotas plus the integer residual count equals the
contribution; the residual count is strictly smaller than the number of
assets. Run `mise run verify:formal:apportionment` in `domains/capital`.
This removes the three-asset limit for these two **algebraic** claims only.
The specific *ranking* used for distributing residual cents remains
three-asset model-checked, and the production Python refinement remains
UNKNOWN. Do not infer an all-asset tie-break or broker correctness proof.

## Passive benchmark — exact-arithmetic transition contract

`PortfolioPassiveBenchmarkR1.smt2` models **two ordered periods**, two
portfolio paths with **the same external deposits**, proportional and fixed
fees charged at the start of each period, and a subsequent gross simple return.
It uses Z3's QF_NRA mathematical reals, the same economic ordering as
`portfolio/passive_benchmark.py`. The admission assumptions are nonnegative
opening capital/deposits/fees, expense fractions between 0 and 1, returns no
less than −100%, and fees not exceeding available capital.

The five UNSAT counterexample obligations establish the model's:

1. Exact cancellation of matched external contributions in **terminal wealth
   difference** versus difference of net gains from contributed capital.
2. Nonnegative intermediate and terminal wealth after admitted fee/return steps.
3. A no-fee, zero-return strategy has terminal wealth equal to opening capital
   plus the two deposits (deposits are **not** investment profit).
4. Identical strategy/benchmark costs and returns imply equal terminal wealth.
5. Admissible start-of-period fees cannot increase wealth against the matching
   hypothetical fee-free return in the first period.

The sixth result must be SAT, witnessing a real, positive-deposit, positive-fee,
nonzero-comparison case to disallow a vacuous all-zero proof. This is **model
checking of two periods**; no full Python `Decimal` refinement proof, arbitrary
period-count theorem, authenticated market data, GIPS-compliant TWR/MWR, tax,
transaction fill, or capital authorization is implied. In particular, Decimal
precision/rounding is not modelled by mathematical reals; do not delete
implementation tests based solely on these proof obligations.

**Human:** From `domains/capital`, run
`mise run verify:formal:passive-benchmark`. Read a synthetic native result via
`scripts/run-capability-python -m ordivon_capital.portfolio.passive_benchmark
--input examples/passive_benchmark_first_run_r1.json`. Treat its terminal
wealth difference as a descriptive difference, **not** a return rate.

**Agent:** Resolve the existing project-scoped
`finance-paper-investment` Skill and record model SHA, pinned Z3 version,
exact `UNSAT × 5 / SAT × 1` outcome, native consumer output/CLI, input provenance,
and separate standing: spec/model VERIFIED; implementation refinement UNKNOWN;
real financial outcome UNKNOWN. Compare only matched external deposits and fee
timing, never infer trade authorization.
