# Paper Accounting — formally checked cash and settlement obligations

**Owner:** `domains/capital/src/ordivon_capital/accounting`. This is a bounded
mathematical model of existing `paper_close.value_session` settlement and
mark-to-market arithmetic, **not** a second ledger or a new Finance Owner.

Run its existing-owner admission task from `domains/capital`:

```sh
mise run formal:paper
```

`mise run verify` also invokes this task after Capital's normal native
tests. It uses **upstream Z3 5.3.2**, pinned in the Capital owner's native `[tools]` declaration via mise's existing GitHub backend; no custom solver, new Python
dependency, new registry or extra release pipeline.

## Why these equations, rather than hundreds of tiny mutation cases?

Represent a preceding Paper close by settled cash `C₀`, open purchase
payables `P₀`, open sale receivables `R₀`, marked position value `V₀`,
protected reserve `Q₀`. All money is **integer minor units**.

In the next session let `P_due` and `R_due` mature, `D` be the
contribution, `Q_add` added reserve, `B` newly committed buy cost,
`S` newly accrued sale proceeds, `ΔV` price movement on carried
holdings, `V_b` today's bought-position mark, and `V_s` sold-position
mark. Current Accounting defines:

```text
C₁ = C₀ + D − P_due + R_due
P₁ = P₀ − P_due + B
R₁ = R₀ − R_due + S
Q₁ = Q₀ + Q_add
V₁ = V₀ + ΔV + V_b − V_s

NAV₁ = C₁ − P₁ + R₁ + V₁
     = NAV₀ + D + ΔV + (V_b − B) + (S − V_s).
```

This algebra separates **a cash settlement (not income)** from a trade's
actual mark-versus-cost difference. Without fees/market-price movement,
settlement alone cannot change NAV. The exact formula for intraday
buying-power admission also excludes cash newly received from same-day
sale settlement:

```text
C₁ − P₁ − R_due ≥ Q₁.
```

That is stronger than simply `C₁ − P₁ ≥ Q₁`. Unsettled `R₁` contributes
to economic NAV but never to unencumbered cash.

## Checked result and limitation matrix

| Layer | Exact claim and evidence | Standing |
| --- | --- | --- |
| **Specification** | `paper_cash_settlement_r1.smt2`, signed integer minor units and finite admitted inputs, no timestamp/identifier model | Declared |
| **Model** | Exact Presburger arithmetic (`QF_LIA`) under nonnegative/open-liability/due/reserve preconditions | Defined |
| **SMT proof** | 3 negated universal obligations UNSAT: NAV conservation, pure settlement neutrality, accepted reserve fence | MODEL_PROVED (unbounded mathematical integers) |
| **Falsification** | 2 SAT witnesses: wrong model omits sale receivables; wrong model reuses matured proceeds as intraday buying power | WITNESS_FOUND for wrong models |
| **Implementation refinement** | `paper_close.value_session` and `postgres_paper_close` source formulas match declared terms; existing real cash/settlement/fill tests exercise observed paths | PARTIAL, not machine-checked Python/model equivalence |
| **Real consumer** | `tests/test_paper_close.py`, `tests/test_paper_close_risk.py`, and native physical PostgreSQL integration when disposable DSNs supplied | Native evidence only; external-market truth UNKNOWN |

**What the proof does not establish:** signed-64/unsigned-64 host integer
boundary safety, full Python path semantics, PostgreSQL serializability or
crash recovery, corporate actions, data-source authenticity, fees/slippage
calibration, external settlement, suitability, production deployment or
broker capital authority. Python unbounded integer arithmetic agrees with
the abstract integer domain for admitted ranges, but the complete source
type/admission and serialization bridge is still unproved. Keep its
owner-native execution/consumer tests.

The two **SAT** checks deliberately confirm that important incorrect
approximations are satisfiable. Neither result can be promoted into
`MODEL_PROVED`. A verifier returning `unknown`, a changed query count or
unexpected result **fails the task**; it never silently passes.

## Exact consumers and future retirement boundary

- [Accounting source transition](../src/ordivon_capital/accounting/paper_close.py)
  remains the only pure Paper state authority.
- [PostgreSQL Paper implementation](../src/ordivon_capital/accounting/postgres_paper_close.py)
  retains durable identity and atomic receipt readback.
- [Risk consumer](../src/ordivon_capital/risk/paper_close_risk.py)
  composes admitted Markets marks and Accounting receipts.
- [Finance Human guide](../docs/FINANCE_HUMAN_GUIDE_R1.md)
  explains why a Paper NAV is not immediately spendable cash.
- [Finance Agent Skill](../../../.agents/skills/finance-paper-investment/SKILL.md)
  finds the exact native commands.

To actually remove an example test, first prove that the affected source
predicate is covered by the model **and** a valid implementation refinement
link, and independently retain tests for real database/provider effects.
These model-only proofs do **not** yet meet that deletion threshold.
