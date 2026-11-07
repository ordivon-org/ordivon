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
