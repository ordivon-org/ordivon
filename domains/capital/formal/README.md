# Capital / Finance — formal model evidence and consumer boundaries

## Portfolio contribution and passive benchmark

The canonical Owner is `Portfolio` in `domains/capital`; there is no Finance
verification service or separate financial authority. This directory contains
one source-adjacent, versioned *mathematical model* of
`src/ordivon_capital/portfolio/strategic_contribution.py`.

### Scope and evidence

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

#### Human

From `domains/capital`, execute `mise run verify:formal:contribution` and
expect `unsat, unsat, unsat, unsat, sat`. To see the read-only, real Python CLI
consumer use the repository's existing
`scripts/run-strategic-contribution-brief < examples/strategic_contribution_r1.json`.
The output is an allocation *projection*, not trading authorization.

#### Agent

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

### All-asset mathematical extension (Lean kernel)

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

### Passive benchmark — exact-arithmetic transition contract

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

A real implementation-refinement falsification found a valid input with
opening `10000000000000000000000000000`, deposit `1`, zero fees/returns: the
original Python 28-digit context silently reported the unchanged opening as
`contributedCapital`. The implementation uses **standard-library Decimal `Inexact` traps for
the cumulative contributed-capital ledger**, which is not a market valuation.
At each strategy/benchmark valuation, it instead permits bounded 28-digit
context rounding of the deposit addition only if the result's conservative
one-ULP error bound is at most `1e-12` of the positive deposit. A meaningful
cash injection that would be lost to valuation rounding is **REJECTED**,
not silently erased; normal tiny fractional-market-value rounding does not
block long-term DCA. Market-return projections intentionally retain the
existing bounded-precision Decimal arithmetic required by the native
`portfolio.paper_investment` consumer; forcing exact infinite-precision
returns would alter established paper replay results. This is a precise
implementation-boundary repair, **not** a universal refinement theorem
for the real-arithmetic SMT model.

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

### Passive benchmark — arbitrary finite periods (Lean) and bounded Python refinement evidence

`PortfolioPassiveBenchmarkGeneral.lean` uses Lean's pinned kernel and **exact
rational arithmetic** with a list of any finite length, rather than extending
the previous two-period Z3 bound by picking a larger fixed number. The proved
properties are: (1) cumulative external contributions equal opening ledger
plus the sum of deposits; (2) identical strategy/benchmark drivers preserve
terminal wealth equality; (3) using the same contribution baseline cancels
from the terminal-gain comparison; and (4) every accepted step's nonnegative
after-fee balance and gross multiplier guarantee nonnegative terminal wealth,
including for any finite sequence of admitted steps. The admission relation
is evaluated against the **evolving** wealth state, not an assumed fixed
opening wealth. This Lean model has no `sorry` or custom axioms.

These are **unbounded-period mathematical specification theorems**; they are
not a proof that Python `Decimal` correctly implements Rational arithmetic.
Python maintains a fully exact external contribution ledger and a separate
bounded market valuation: a cashflow addition in either valuation is accepted
only when the worst-case one-ULP rounding error is no more than a declared
`1e-12` fraction of that deposit. This is an operational numerical error
policy, not a Lean theorem about Python runtime behavior.
Python deliberately rounds market-return arithmetic to its current context;
a blanket exact-arithmetic substitution previously broke the actual Paper
Investment consumer. `tests/test_passive_benchmark.py` separately compares the
real Python implementation against an independently structured standard
`Decimal.Context` oracle for 96 seeded paths of 1, 2, 3, 7, 31, and 120
periods and a 250-period no-fee/zero-return deposit path. Those are bounded
consumer witnesses, not universal implementation refinement.

Another direct falsification discovered that the prior API leaked a raw
`decimal.Overflow` on a finite but out-of-range user-supplied return such as
`1e999999`. The Python public boundary now raises `PassiveBenchmarkError`
for unsupported Decimal-context operations, and the real JSON CLI returns
`REJECTED` (exit code 2) without a traceback. This is a fail-closed
implementation repair, not market-data verification.

**Human:** Run `mise run verify:formal:passive-general` and
`mise run verify:formal:passive-benchmark` from `domains/capital`, then
`mise run verify` for the full real-consumer suite. To inspect a synthetic
read-only result, use the existing `scripts/run-capability-python -m
ordivon_capital.portfolio.passive_benchmark --input
examples/passive_benchmark_first_run_r1.json`.

**Agent:** Resolve the existing `finance-paper-investment` project Skill,
keep the `Lean arbitrary-period model = VERIFIED` observation separate from
`Python Decimal universal refinement = UNKNOWN`, report the actual native
CLI and bounded differential/negative-case outcomes, preserve matched-cashflow
semantics and non-live `capitalAuthority=NONE`, and do not turn mathematical
properties or synthetic samples into prospective return evidence.

---

## Paper Accounting cash, settlement and reserve

**Owner:** `domains/capital/src/ordivon_capital/accounting`. This is a bounded
mathematical model of existing `paper_close.value_session` settlement and
mark-to-market arithmetic, **not** a second ledger or a new Finance Owner.

Run its existing-owner admission task from `domains/capital`:

```sh
mise run formal:paper
```

`mise run verify` also invokes this task after Capital's normal native
tests. It uses upstream **Z3 5.3.3** via the exact `z3-solver==5.3.3.0`
PyPI wheel, run through the owner's existing pinned `uvx` toolchain.
The verification task calls Z3's upstream `Z3_eval_smtlib2_string` API
directly on the same SMT-LIB source. No custom solver, application runtime
dependency, parallel registry or extra release pipeline is introduced.

### Why these equations, rather than hundreds of tiny mutation cases?

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

### Checked result and limitation matrix

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

### Scoped source-symbolic implementation refinement (CrossHair)

The source-adjacent `paper_settlement_source_contract.py` directly invokes
`accounting.paper_close.value_session` for a two-session, no-new-trade,
no-held-position case with two matured/not-yet-matured buy payables and
sale receivables. Six integer symbolic inputs are admitted only with
nonnegative payable/receivable bounds, protected-cash backing and
**both** existing-NAV and resulting-cash signed-int64 receipt bounds.
This links the real Python transition to the Z3/Lean settlement arithmetic
for that exact subset, without implementing another accounting state machine.

From `domains/capital`, execute `mise run formal:paper:source` using upstream
CrossHair 0.0.113 + Z3 5.3.3.0 via the existing `uvx` toolchain. The task
requires `Confirmed over all paths.` from the real source and refuses
silent exits or unconfirmed paths. The owner-native `mise run verify` also
runs this scoped consumer. Before the combined receipt bounds were added,
CrossHair found a real counterexample: cash 1 and receivables at the signed
int64 ceiling matured together would make the next receipt overflow.
The source correctly rejects that invalid prior-state/receipt domain; the
contract now excludes the unreachable input rather than weakening
`value_session` or claiming it must accept an overflowing close.

**Evidence scope:** bounded symbolic exploration of the exact declared Python
subset and a demonstrated negative counterexample, not kernel-level complete
Python refinement, arbitrary account history, fill identity/calendar,
PostgreSQL SERIALIZABLE transitions, crash recovery, real exchange settlement,
provider data authenticity or brokerage authorization. Existing actual
PostgreSQL consumer/readback tests must remain. The CrossHair outcome is
`SOURCE_SYMBOLIC_CHECKED_IN_SCOPE` only when witnessed on a source revision.

### Exact consumers and future retirement boundary

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

## Accounting reservation state machine: model proof and real PostgreSQL consumer

The Capital Accounting owner now has an independent mathematical model at
\`formal/AccountingReservationR1.smt2\`. The model is deliberately **not**
another Python ledger or another event store. Its state is an integer
budget \`B\`, posted consumption \`S\`, pending reservations \`P\`,
and a reservation resolution status \`{0=absent,1=pending,2=posted,3=voided}\`.
The safety invariant is \`B >= S + P >= 0\` with \`S,P >= 0\`.
An admitted reservation adds \`a>0\` to pending only if \`S+P+a <= B\`;
POST transfers \`a\` from pending to posted, and VOID removes \`a\` from pending.
Resolution status cannot legally transition twice.

Running \`mise run formal:accounting-reservation\` from \`domains/capital\`
uses **upstream pinned Z3 5.3.3** via the existing owner's \`uvx\`
verification pathway. Exactly **7** universal negated properties must be
\`UNSAT\`; two intentionally broken models must each be \`SAT\`.
A solver error, \`unknown\`, missing obligation or changed result is a failure.
The model is in mathematical unbounded integers, not an assertion about
machine word overflow, currencies, real-world broker settlement or PG
isolation.

**Refinement boundary:** the current implementation,
\`accounting/postgres_ledger.py\`, uses PostgreSQL SERIALIZABLE operations
and mutations of the original pending row's \`status\`, plus separately
recorded resolution transfers. The reference project TigerBeetle uses
immutable original transfer records instead; these are **not identical
storage representations**. Proof of the abstract model does not prove
that the PostgreSQL source faithfully implements all its transitions.

The real-implementation evidence therefore remains
\`tests/test_postgres_ledger.py\` (locking, idempotence and restart),
\`tests/test_postgres_accounting_traces.py\` (36 ordered two-action traces
against independently specified expected balances and outcomes), and
the nonlive effect-matrix test. Tests that mutate Accounting data are
allowed **only against a separate disposable PostgreSQL database**
named \`ordivon_capital_test_*\`; a skipped provider test is **NOT** a
completed real-consumer certification.

**Human:** choose the economic obligation, account namespace and
source-of-truth receipt; read the safety invariant before interpreting
the PG result. Research portfolio output is not a broker receipt.
**Agent:** first run the Z3 task to verify the model; then run the real PG
trace and restart consumers with a disposable DSN; attach separate
MODEL_PROVED vs IMPLEMENTATION_NATIVE_TESTED standings. Do not claim
the formal model proves a production database implementation or live
trade settlement.

Official references: https://docs.tigerbeetle.com/coding/two-phase-transfers/
and https://www.postgresql.org/docs/current/transaction-iso.html .
