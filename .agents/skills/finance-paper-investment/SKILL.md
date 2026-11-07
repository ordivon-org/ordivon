---
name: finance-paper-investment
description: >-
  Use when an Ordivon Agent needs to operate existing Finance Investment Mode
  or Paper Lab, plan contribution-only allocation, compare passive benchmarks,
  replay ETF simulations, examine price-vintage drift, or prepare a paper-only
  PostgreSQL close receipt. Reuse existing natural Owners, not brokerage effects.
compatibility: Ordivon domains/capital; project mise/uv toolchain; native Runtime/Harness; no proprietary skill registry.
metadata:
  source-authority: Ordivon Finance Portfolio Markets and Accounting
---

# Finance Investment & Paper Lab — Agent Skill

This Skill is a **procedure and capability router**, not another portfolio engine, ledger, scheduler, provider client, or agent. Source remains `domains/capital`. For hypothesis freezing, holdout falsification and research candidate economics, switch to the already canonical `.agents/skills/finance-experiment-review/SKILL.md`; do not duplicate that workflow here. Human-facing operations are documented in `domains/capital/docs/FINANCE_HUMAN_GUIDE_R1.md`.

Directory/LEGO consumer audit: domains/capital/docs/FINANCE_DIRECTORY_OWNER_AUDIT_R1.md. Resolve the seven current natural Owners before changing code or deleting historical files. Human and Agent routes are distinct. Use the active Skill source digest, not merely a GitHub Skill file, for deployed discoverability.

## Select the actual goal before invoking any tool

| Intention | Natural Owner | Native entrypoint | Actual standing |
|---|---|---|---|
| Allocate caller-defined new virtual contribution while protecting cash | Portfolio | `scripts/run-strategic-contribution-brief` | Stateless, no orders |
| Compare equal-cashflow strategy and passive benchmark | Portfolio | `python -m ordivon_capital.portfolio.passive_benchmark --input replay.json` under Capital toolchain | Read-only economic description |
| Replay a qualified historical source from a pinned snapshot | Portfolio | `scripts/run-paper-etf-replay-r1 --request request.json --source source.csv [--output private-receipt.json]` | Historical simulation only |
| Compare the economic effect of two source vintages | Portfolio | `scripts/run-paper-etf-vintage-compare-r1 --reference-request ... --reference-source ... --candidate-request ... --candidate-source ...` | Descriptive revision sensitivity |
| Admit an ETF EOD mark or historical source | Markets | `markets.etf_eod_snapshot`, `markets.historical_close_snapshot` | Source/time admission, not rights invented by Agent |
| Close a funded Paper session and read its receipt | Accounting | `scripts/run-capability-python -m ordivon_capital.accounting.postgres_paper_close --account NAME --input SESSION.json` | Mutates ONLY dedicated Paper PostgreSQL; no broker |
| Freeze a hypothesis, compare against passive benchmark and falsify | Research | Existing `finance-experiment-review` Skill and `scripts/run-finance-lego` | Evidence not authority |
| Evaluate exposure and effects | Risk / Governance / Trading | Actual bounded source contracts | No implicit cross-domain permission |
| Operate external OKX Demo provider | Trading / Governance / Accounting | scripts/run-okx-demo-execution and finance-demo-execution Skill | Source consumer and admission contract; external receipt separate |

All command paths above are relative to `domains/capital` except the direct reference to the other canonical Skill. Before using one, check its exact option interface (`--help`) and latest source/contract version.


## Algebraic investment research is not Paper settlement

For normalized monthly 1r investment optimization, the canonical
representation is `domains/capital/docs/ALGEBRAIC_FINANCE_POLICY_R1.md`
with bounded read-only portfolio operator
`ordivon_capital.portfolio.algebraic_policy`. Unlike prior historical
`research.unit_r_dca` presets, this core does not define a "safe"
percentage drawdown, multiplier, financing APR or default risk preference.
Human owns utility/horizon, market/broker authorities own probabilities/
borrowing/margin, and missing inputs remain UNKNOWN.
`solve_multistage` is the bounded finite-scenario monthly-1r
nonanticipative optimizer under `domains/capital/docs/MULTISTAGE_FINANCE_R1.md`.
Optional `terminal_liabilities_r` requires an externally verified cash
obligation for EVERY terminal leaf. Optimize CRRA on disposable surplus,
report gross/obligation/net values separately; never treat future liabilities
as today's broker collateral. Intermediate expenses are separately modeled by `node_outflow_after_contribution_r`.
This additional contract only handles payments explicitly due after the
current month 1r contribution; it does NOT authorize any early rescue of
pre-contribution defaults or guarantee real broker liquidity.


It requires the FULL externally supplied observable information tree and
conditional probabilities. It separately reports feasible contract residuals,
terminal wealth and an independent LP supporting-hyperplane bound on
numerical utility optimality; neither proves a trusted market forecast.
When circumstances do not support that tree, keep output UNKNOWN.
Use the existing Python module consumer with an exact `gamma`/`nodes` JSON
contract, not a bespoke service: `PYTHONPATH=src uv run --no-sync python -m
ordivon_capital.portfolio.multistage_policy --input path/to/tree.json`.
It returns only caller-supplied (unattested) research standing and a
non-execution effect status. Never interpret its optimized r balances as a
broker or Paper Ledger receipt.
`solve_one_period` is a conditional one-period CRRA solution;
intertemporal monthly cashflows still require genuine Bellman/MPC evidence.
Never route research output into live or Paper execution without an
independently established consumer contract.



## Provider-segment margin and declared liquidation evidence

Use the existing Capital Risk facade `portfolio_risk`:
`assess_provider_margin_segments` and `replay_declared_long_liquidation`.
Do not create another broker, risk database or order executor.

To assess a real reported margin observation, supply a timezone-aware
snapshot, provider identity and per-segment actual margin equity,
initial requirement, maintenance requirement and equity basis.
For an IBKR Securities segment use EWL; for Commodities use NLV.
Never let positive aggregate excess erase a negative individual segment.
A margin breach does not establish whether or when the broker executed
a discretionary forced liquidation.

Only when you have a declared actual share-sale execution, supply the
long-only original marks, fills, fees, cash, debt, debt repayment and
explicit pre/post maintenance. Report the algebraic identity:

    deltaEquity = sum(quantitySold * (fillPrice - referenceMark)) - fees.

Preserve unpaid negative equity and residual loans; do not conjure
profitable liquidation, a guaranteed execution price or the next 1r.
These functions only certify a caller-supplied conditional mathematical
state, never the actual broker. Have Markets/Trading authenticate the
original broker source before any Finance state claim.

Do not import the old experimental `unit_r_dca` defaults (40%, 45%,
7%, margin cushions) as issuer/broker finance requirements.
Formal: `mise run //domains/capital:verify:formal:broker-liquidation`.
Tests: `tests/test_broker_margin_evidence.py`.

## Markets capture admission: never backdate downloaded adjusted prices

Use the existing Markets `historical_close_snapshot.admit_adjusted_close_csv`
through the thin Research `pit_joint_forecast.market_capture_to_pit_vintages`.
Supply the unmodified CSV bytes (Date + one column per ETF), exact SHA256,
assets, requested dated range, source `captured_at` instant and caller-verified
`last_session_close_at` (both timezone-aware).

The function uses Markets' existing parser and SHA checks and returns
existing `PriceVintage` objects with their **conservative knowledge bound**
set to capture time. A newly retrieved five-year file DOES NOT certify
five years of historical vintages. Its historical observations can enter
only decisions occurring at or after this particular capture, never
retrospectively in earlier holdings/backtests. Provider origin, publication
times, total-return adjustment and corporate actions remain independent
evidence. Do not relabel vendor-adjusted closes as raw tradeable fills.
If you need genuine historical point-in-time backtests, acquire a
sequence of separately archived historical captures with actual historical
timestamps and independently recorded supplier evidence.

The output carries only `SECONDARY_VENDOR_NOT_ATTESTED` and is research
only, not valid as a Markets/Paper settlement mark. Preserve source byte
digests and the raw downloaded bytes through the existing Artifact Owner;
do not build a new market database or source registry.

## Direct PIT research-to-Portfolio consumer

Use the existing Research `pit_joint_forecast` --solve option for frozen,
caller-supplied historical vintages and exact cross-ETF return scenarios.
It calls the existing `portfolio.multistage_policy` solver directly,
without inventing another financial optimizer or execution subsystem.

From `domains/capital` run:
`PYTHONPATH=src uv run --no-sync python -m ordivon_capital.research.pit_joint_forecast --input request.json --solve`.

Without --solve the prior evidence-only JSON output is unchanged.
Compare `forecast_evidence` with `conditional_allocation`. The former is an
uncalibrated joint empirical/lagged-neighbor hypothesis. The latter is
a conditional numerical solution under the caller's gamma/fees/funding/
broker margin terms; the LP numerical optimality bound is NOT proof
of market predictive skill. Both have `NONE_NO_TRADE_NO_ACCOUNTING` effects.
The timestamp, raw-vintage evidence and actual broker contracts must be
verified independently. Forward falsification uses the existing
finance-experiment-review Skill.

## How to route the source LEGO registry (CA01—CA10)

Do not invent a second LEGO namespace, general controller or another skill
registry. Consult the current canonical `planning/lego-plan-r1.json`.
The existing source units map to requested effects as follows:

- **Markets**: CA01 qualifies public observations; not private venue truth.
- **Risk**: CA02 measures dependence; CA03 projects positions/factor
  exposures. They are observations, not independent causal trade signals.
- **Portfolio**: CA04 evaluates named what-if composition with the Risk
  contract; CA09 computes contribution-only long-horizon allocation.
- **Governance**: CA05 applies the non-live effect admission. A passing
  source policy is not a broker execution permit.
- **Trading**: CA06 interprets ambiguous provider order standing; UNKNOWN
  remains UNKNOWN when external confirmation is missing.
- **Accounting**: CA07 owns durable reservation/journal semantics. Reuse its
  PostgreSQL paper close, never build a second NAV/ledger engine.
- **Research**: CA08 validates prospective evidence; CA10 freezes and reviews
  the experiment protocol. Continue using `finance-experiment-review`.

These are implemented **source-level** contracts only. The exact physical
Consumer, external-data authority, deploy readiness and permissions must be
checked separately at use time. Routes for modern ETF/paper modules remain
their respective Markets/Portfolio/Accounting implementations, not new
shadow LEGO registrations.

## Safe initial consumer (works without provider credentials)

From repository root:

```sh
domains/capital/scripts/run-strategic-contribution-brief \
  < domains/capital/examples/strategic_contribution_r1.json
```

Known fixture: `allocationsMinor.BOND_CORE=10000`,
`allocationsMinor.INDEX_CORE=0`, `cashAfterMinor=40000`, and
`executionAuthorized=false`. USD amounts are integer **minor units**
(cents); weights are basis points summing to 10000. Output retains
`dataStanding=CALLER_SUPPLIED_UNATTESTED` and
`riskStanding=NOT_EVALUATED`. Never report the example as source-qualified
investment advice.

## Passive benchmark transition proof and real consumer

The existing `portfolio.passive_benchmark` remains the sole descriptive
matched-cashflow benchmark replay. Check the source-adjacent two-period Z3
model using `mise run //domains/capital:verify:formal:passive-benchmark` and
the **arbitrary-finite-period** Lean rational model using
`mise run //domains/capital:verify:formal:passive-general`. Read
`domains/capital/formal/README.md` for exact proof scope. Neither the model's
five UNSAT/one SAT results nor the Lean induction are a Python `Decimal`
implementation-refinement proof. The
real consumer is still the native `scripts/run-capability-python -m
ordivon_capital.portfolio.passive_benchmark --input ...`; keep real economic
returns, fees, cashflow provenance, and hypothetical replay claims separate.
Do not call terminal wealth difference a GIPS time-weighted or money-weighted
return. Do not add another Finance reporting engine. Real consumer falsification
identified that default Decimal precision could silently swallow external
cash additions. A second real-consumer counterexample showed that rejecting
**all** rounding would incorrectly block routine long-horizon DCA. The Python
benchmark now keeps cumulative external cash **exact** (`Inexact` trap), but
allows per-valuation deposit rounding only within a conservative one-ULP error
budget of `1e-12` times the positive deposit. Materially lost cash injections
and non-finite/overflowed valuations are `REJECTED`; market-return rounding
still follows the established context for `portfolio.paper_investment`.
Treat arithmetic-domain REJECTED as unavailable, never as lost customer money.
The full Python Decimal refinement remains UNKNOWN. The native multi-period
differential/CLI tests are bounded consumer evidence, not a universal proof.

## Paper replay admission

1. Freeze the source provider, rights, `availableAt`, exact source revision,
   SHA-256 and calendar sessions; do not equate a file digest with publisher
   authenticity. Historical copies edited after the tested dates cannot
   establish prospective outcomes.
2. With an explicit `--request` JSON and digest-matching `--source`, run
   `scripts/run-paper-etf-replay-r1`. The existing example
   `examples/paper_fixed_mix_etf_20261106.json` is a **request only**:
   no source CSV is bundled. If the source is missing, report BLOCKED /
   UNKNOWN rather than generating synthetic price facts.
3. Inspect `standing`, `capitalAuthority`, `sourceCommitClaimVerifiedExternally`,
   `providerPriceAuthenticityVerified`, `prospectiveHoldoutVerified`,
   `finalStrategyNAV`, `finalBenchmarkNAV`, `strategyMaxDrawdown`, and
   `dailySettlements`. Distinguish bounded mathematical replay from
   independently verified market performance.
4. A requested --output receipt is atomically published create-once. An identical replay is idempotent; different bytes at an occupied path fail without replacing the existing receipt. Use a distinct path for each source/policy version.
5. For a revised source vintage use the existing
   `scripts/run-paper-etf-vintage-compare-r1`, not a third price-replay
   implementation. The result indicates historical sensitivity, never
   prospective alpha.

## Formal Accounting evidence (load only when checking cash invariants)

Use `domains/capital/formal/paper_cash_settlement_r1.smt2` and the
owner-native `mise run formal:paper` task for three SMT-Presburger
invariants plus two deliberately satisfiable incorrect-model witnesses.
The natural specification and proof-level caveats are in
`domains/capital/formal/README.md`. Model proof != source refinement,
PostgreSQL persistence, deployment or capital authority. Do not create
a second ledger, copy Z3 into a private verifier or delete meaningful
database tests on model-only evidence.

For a symbolic **source implementation** check of the two-date no-trade
Paper settlement subset, run `mise run //domains/capital:formal:paper:source`.
This uses the original `value_session` in upstream CrossHair under actual
signed-int64 prior-NAV and resulting-cash admission preconditions; its task
must explicitly report `Confirmed over all paths.`. A model-only success
is not implementation proof, and this scoped source check is not
PostgreSQL crash/serialization proof or exchange/broker evidence.
See the existing formal README. Reuse this task; do not create a parallel
Skill, checker, ledger, or formal framework.

## Stateful Paper Accounting admission

1. Check that the user/owner is asking for a **simulated** close and that
   `ORDIVON_CAPITAL_PAPER_PG_DSN` refers to the dedicated `ordivon_paper`
   database and a paper-only role. This writes virtual journal state, unlike
   the read-only portfolio CLI. No actual broker, bank or live exchange.
2. Bind one exchange session, prior close, funded cash, existing positions,
   fill identity, settlement dates, fees, and closing marks. The Markets
   qualified EOD path requires **both** `--market-snapshot` and
   `--market-binding` with empty inline marks; never mix unqualified inline
   prices and admitted snapshots.
3. Use only the existing Accounting entrypoint
   `scripts/run-capability-python -m ordivon_capital.accounting.postgres_paper_close
   --account NAME --input session.json` with the optional paired market
   arguments. It owns payable/receivable entries, atomic close, exact replay
   and PostgreSQL readback. The Skill never calculates a second NAV.
4. Output receipt identifiers, mode, snapshot lineage and whether a durable
   readback was actually witnessed. If source/receipts are missing, mark the
   unavailable field UNKNOWN and avoid publishing fictitious daily P&L.

## Portfolio mathematical verification (no extra proof framework)

For a new-cash/no-sell allocation request, reuse
`mise run //domains/capital:verify:formal:contribution` and
`domains/capital/formal/README.md`. The pinned Z3 proof checks the
three-symbol abstract largest-remainder model, *not* arbitrary portfolio
size or the production Python function's refinement. Preserve the native
`run-strategic-contribution-brief` consumer as a separate observation.
The additional task `mise run //domains/capital:verify:formal:apportionment` proves general finite-asset quota and residual-count algebra with Lean, but it does not prove Python implementation refinement or all-asset tie-break.
Report model UNSAT/SAT, source digest and actual consumer result distinctly;
never upgrade the model evidence to a broker or capital authority.

## Decision and falsification rules

- **I**: goal, user investment assumptions, explicit capital units, current
  canonical source and qualified time/rights evidence.
- **O**: actual CLI result, receipt/digest, source availability, risk and
  authorization standing, absent/UNKNOWN facts and next natural consumer.
- **pre**: legitimate paper/no-effect purpose; exact source-qualified input
  for any claim beyond caller-supplied simulation.
- **post**: output honestly describes existing computation and never infers
  financial authority from a research/report status.
- **inv**: same cashflow base for benchmark, protected cash preserved,
  accounting owner alone owns NAV, no duplicate execution/ledger state.
- **eff**: read-only for Portfolio/Research, Paper-only DB for Accounting;
  never live broker order/transfer.
- **c**: source modules dictate bounded costs and limits; UNKNOWN without
  exact implementation evidence.
- **epsilon**: source vintage errors, fees/corporate actions and probabilistic
  uncertainty remain explicit; do not convert UNKNOWN to false.
- **prov**: module path, pinned source rev, dataset digest, actual session,
  observed result and real consumer evidence.
- **unfold**: Human goal → natural Owner → native call → validated receipt
  → independent research/risk interpretation.

The source of truth for composition is
`domains/capital/config/capital_domain_taxonomy.json`; for R2.1 identities,
`domains/capital/planning/lego-plan-r1.json`; for source/external Owner
census, `domains/capital/config/external_owner_census.json`. Execute
`mise run //domains/capital:verify` for acceptance. Treat repository Skill
packaging as discovery instructions only, **not** registration of a new
runtime, scheduler, financial provider, credential authority or live
investment mandate.

References: https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx ;
https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview ;
https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/

## Independent multistage cashflow replay (Research falsifier)

Use the EXISTING Portfolio multistage CRRA solver as the only optimizer.
For independent falsification, package its exact input JSON as problem
and its solution JSON as solution in one research-only JSON object.
Run from domains/capital using the native environment:

    PYTHONPATH=src uv run --frozen --no-sync --group test python -m ordivon_capital.research.independent_policy_replay --input /path/to/solver-pair.json

This pure stdlib Research capability deliberately imports NO SciPy or
Portfolio optimizer internals. It recomputes, from the public solution,
each branch's before-deposit equity, pre-deposit maintenance, exactly
one monthly 1r contribution, correctly dated due payments, turnover fees,
post-trade budget, initial margin, terminal liabilities, probability mass,
CRRA expected utility and certainty equivalents.

Agent guidance: Always replay the EXACT frozen solver input and matching
output before claiming numeric investment experiment results. Preserve
returned input digest; never substitute realized future markets into
the original information tree. REJECTED means a model/receipt mismatch.
A passing result is NOT proof of optimizer optimality, trading
authorization, or an audited data source; use independent analytic
benchmarks and upstream solver's documented LP bound for numeric
optimality evidence.

Human guidance: Compare original obligation/return inputs with the replay
receipt and check max_identity_residual_r and minimum_collateral_surplus_r.
Positive terminal R is NOT investment profit without subtracting all
contributed 1r and cash obligations. Only externally evidenced cash and
broker contracts permit economic conclusions.

## Reusable information-tree representation LEGO (source-only)

Use `ordivon_capital.portfolio.information_tree` for the **pure, solver-free** representation and validation contract. Public entry: `validate_information_tree(MultistageProblem(...))` with its canonical `InformationNode` type. It checks observable information histories, monthly timing, conditional probabilities, branch discernibility, declared liabilities and supplier-provided margin assumptions. It does **not** authenticate data releases, prove conditional-probability calibration, qualify a broker, or certify optimality.

Only after validation should an Agent call the **existing** `ordivon_capital.portfolio.multistage_policy.solve_multistage`; no duplicate optimizer, ledger or execution authority is created. The existing Research/PIT `multistage_policy.InformationNode` and `MultistageProblem` remain the **same Python types** as the canonical information-tree module, not shadow DTOs. Prefer the canonical `information_tree` import in new direct validators. To validate behavior, use `tests/test_multistage_policy.py`, `tests/test_pit_joint_forecast.py`, and `tests/test_capital_domain_taxonomy.py`.

Human workflow and economic assumptions: `domains/capital/docs/FINANCE_HUMAN_GUIDE_R1.md` and `docs/MULTISTAGE_FINANCE_R1.md`. Always record source revision, original upstream market/broker evidence and resulting validation standing, separately from optimizer residuals and economic claims.

## PostgreSQL-only Accounting retirement (no legacy oracle)

The only current durable Accounting ledger is
ordivon_capital.accounting.postgres_ledger. Use the existing
accounting.substrate typed instructions. For nonlive effects, route to
scripts/run-nonlive-capital-effect-matrix, which requires an explicit PG DSN.
Never restore or select SQLite, start a second ledger, or promote a Paper
accounting receipt to actual broker evidence.

For independent mechanical verification use a disposable,
purpose-named ORDIVON_CAPITAL_PG_TEST_DSN with
tests/test_postgres_ledger.py and tests/test_postgres_accounting_traces.py.
The latter executes 36 ordered two-action traces against a genuine PG backend
with independent expected statuses, cash conservation and visibility.
Never run mutation tests on a production financial database. Retired:
SQLite source, data importer, differential oracle, old restart smoke and
the unconsumed R0-R5 historical acceptance runner.

Human guidance is in domains/capital/docs/FINANCE_HUMAN_GUIDE_R1.md.

## Accounting reservation formal LEGO: model versus physical refinement

For pure mathematical obligations, run the existing Capital task
\`mise run formal:accounting-reservation\` and inspect the single source
\`domains/capital/formal/AccountingReservationR1.smt2\`. The Z3 model
checks 7 universally quantified integer-safe transition properties and
2 SAT witnesses for unsafe alternatives. This is \`MODEL_PROVED\`,
**not** source, PostgreSQL transaction, or external-provider proof.

For actual refinement evidence, use the existing PostgreSQL Accounting
Owner only: \`tests/test_postgres_ledger.py\`,
\`tests/test_postgres_accounting_traces.py\` and the nonlive effect
matrix. Supply a physically disposable test database via
\`ORDIVON_CAPITAL_PG_TEST_DSN\` and the required
\`ordivon_capital_test_*\` database-name fence. If PG credentials are
absent, record \`NATIVE_CONSUMER_UNKNOWN\`, never promote a skip to PASS.
Account-state snapshots and original pending transfer status can be
updated by the current PG implementation; do not falsely assume
TigerBeetle's immutable-original-transfer storage model.
