# Finance R2 — Investment Evidence, not AI Trade Authority

The verified canonical source cut is the Capital Owner at domains/capital.
Finance is currently one investment-focused business responsibility **within**
Capital; it is not an independently deployed Owner. A wholesale rename of
capital into finance would merge cross-domain treasury/accounting concerns
and break real external consumers.

## Current owner mapping and decisions

| Existing owner | Implemented source | R2 direction |
| --- | --- | --- |
| Markets | src/ordivon_capital/markets/ | Public observations and provenance; Network controls transport |
| Research | src/ordivon_capital/research/ | Frozen hypotheses, temporal validation, bounded evidence |
| Portfolio | src/ordivon_capital/portfolio/ | Benchmark/long-run asset allocation before alpha strategies |
| Risk | src/ordivon_capital/risk/ | Independent limits, factor and tail risk |
| Trading | src/ordivon_capital/trading/ | Execution mechanism; do not move until import consumers qualified |
| Accounting | src/ordivon_capital/accounting/ | External-ledger authoritative accounting and reconciliation |
| Governance | src/ordivon_capital/governance/ | Deterministic effect policy; not an LLM vote |

The first useful new semantic capability is not another trading engine or
Agent platform. It is a **frozen investment research candidate evaluation**,
implemented in src/ordivon_capital/research/investment_candidate.py.
It reuses native Python Decimal, SHA-256, timestamps and JSON rather than
adding an experiment engine, workflow scheduler, new repository, registry
or an unnecessary dependency.

Consumer: a human or Harness/Runtime-controlled research task can run:

    PYTHONPATH=src uv run --locked --group test python -m ordivon_capital.research.investment_candidate \
      --manifest candidate.json --source snapshot.bin --holdout paired-returns.json

Run from domains/capital. The manifest is an exact object with:
schemaVersion=1, kind=ordivon.capital.finance.frozen-research-candidate,
candidateId, hypothesis, frozenAt, featureDataLatestAvailableAt,
sourceSha256, holdoutSha256, trialCount, currency, costCoverage.
Every return observation has periodEndAt, availableAt, strategyGrossReturn,
benchmarkNetReturn, fees, slippage, financing and taxes. Returns and costs
are decimal strings, each explicitly post-freeze, paired on the same
period. Costs are per-period fractional drag and cannot be negative.
Source/holdout SHA-256 commitments verify **the supplied bytes**, not
the economic claims inside those bytes.

Standing is **STRUCTURALLY_REVIEWABLE_NOT_INDEPENDENTLY_VERIFIED** or
REJECTED. There is never a trading grant. This does not attest that
the hypothesis actually existed before outcomes, that market data was
published at the claimed historical time, that strategies can be
independently recomputed, that backtests control trial-selection bias,
or that a good historical return forecasts future performance.
These require external provenance, independent code/data replay,
untouched temporal holdouts and actual portfolio/risk scrutiny.

## R2.1 semantic contract for this bounded capability

- I: FrozenCandidateV1, source_bytes, holdout_bytes.
- O: ResearchEvidenceSummaryV1 or CandidateEvidenceError.
- S: Unit (no persistent state).
- pre: committed source/holdout byte identities and declared feature timing.
  Authentic historical-time publication and precommitment remain UNKNOWN.
- post: invalid evidence is rejected; admitted output is a deterministic
  cost-aware benchmark comparison from strictly post-freeze observations.
- inv: no IO writes, financial effects or capital authority; Decimal-only
  finite simple returns, no negative cost or duplicated time period.
- eff: empty: no credential, network, orders or holdings mutations.
- c: O(n) over n observations, O(n) parsing memory; hard resource
  ceiling remains UNKNOWN pending an upstream admission bound.
- epsilon: exact arithmetic in the active Python Decimal context;
  inference and point-in-time accuracy UNKNOWN, never zero by fiat.
- prov: both input digests verified; provider facts and freeze claims
  unverified, explicitly surfaced in the result.
- unfold: code + direct CLI + focused falsification tests;
  no independent runtime/registry/agent process.

## Deliberate technology selection

Mature provider owners: Qlib/MLflow for real model experiment workflows,
LEAN or NautilusTrader for historical/event-driven execution, DuckDB/Parquet
for data research, and candidate libraries such as Riskfolio-Lib and
PyPortfolioOpt for documented portfolio optimization. These are **not**
blindly installed or declared current. An independently selected component
must first show a real consumer and equivalence against Capital's
frozen contract. Model validation refers proportionately to SR 26-2;
research false discovery must account for selected trials, temporal data
leakage and independent holdout results. This implementation does not
reimplement PBO, portfolio optimization, order/exchange protocols,
Agent lifecycle or orchestration.

Investment Mode and Research Mode share evidence but not capital
authority. Even a positive quantified comparison does not cause order
submission. Existing read-only/non-live execution boundaries remain.

## Retirement disposition

Tracked docs/evidence/fixtures carry legacy reproduction and consumer
identities: they are not runtime caches to delete by path pattern.
Do not delete them until current traced consumers are absent and authority
for immutable reproducibility has been qualified. Generated caches and
venvs remain Git-ignored. Retire stale detached workspaces through
Runtime workspace.close (when clean, inactive) and Git's native worktree
inspection/pruning rather than recursive filesystem deletion.

## Scoped acceptance and next business consumers

1. Native test/ruff pass for evidence contract, and actual valid/invalid CLI
   replay. Not an investment strategy performance claim.
2. Extend passive benchmark and cash-flow mode only against independently
   bound holdings, cost assumptions, and a lawful data source.
3. Bind externally timestamped frozen decisions, market-source publication
   receipts, independent source-to-return replay and multiple trial controls.
4. Reuse Harness/Runtime and installed MLflow/Qlib conditionally for the
   Research Factory; no second Agent subsystem.
5. Real broker effects and capital rights are a separately controlled
   phase, not an incidental effect of the research CLI.


## Finance R3 — source-recomputed candidate (schemaVersion=2)

The original v1 interface remains an envelope-only structural check. The same
CLI now admits an optional schemaVersion=2 with kind
ordivon.capital.finance.replayable-research-candidate and two declared
frozen policy parameters:

- strategyAssetWeight: decimal string in [0,1], constant over holdout periods;
  the residual portfolio weight stays in a caller-provided cash series.
- benchmarkExpenseFraction: decimal string in [0,1], constant per period
  and subtracted from the benchmark gross return.

For v2 only, --source must be a JSON array with exactly one observation per
holdout period. Fields: periodEndAt, availableAt, assetGrossReturn,
cashGrossReturn, benchmarkGrossReturn. All simple returns are finite decimal
strings with lower bound -1. Each source end equals the holdout end; declared
availability is between that period end and the holdout availability. Both
source and holdout bytes remain SHA-256 committed.

Independently compute from committed observations:

    expected_strategy_gross = weight * asset + (1-weight) * cash
    expected_benchmark_net = benchmark_gross - benchmark_expense

Both must exactly match claimed holdout returns. Even an adversary who
recommits modified holdout bytes cannot use a false derived return without
detection. Holdout costs, compounding and drawdown use the existing v1
computation. No new backtesting engine or tracking service is introduced.

Successful standing: SOURCE_REPLAYED_PROVIDER_NOT_ATTESTED, with
sourceToReturnRecomputationVerified=true and
sourceObservationProvenanceVerified=false. This is reproducible arithmetic
from the submitted observations, NOT evidence that an external provider
published them, that corporate-action adjustments and universe membership
are point-in-time, that an experiment was truly frozen before the holdout,
or that fees, trials, liquidity and forward profitability are established.
The two authorities remain distinct: this result never grants capital.

R2.1 refinement: I=FrozenCandidateV2 plus committed observation array;
O=ResearchEvidenceSummaryV2 or CandidateEvidenceError; S=Unit;
pre=valid time-aligned observations and declared constant exposure;
post=holdout claims exactly equal independently calculated source projections;
inv=read-only and no capital grant; eff=empty; c=O(n) processing;
epsilon=Decimal-context arithmetic, financial-source error UNKNOWN;
prov=byte digests verified, publisher/freeze claims NOT VERIFIED;
unfold=same evaluator and CLI plus focused v2 falsification consumer.

## Precision of research policy commitments (2026-11-07)

Policy `configDigest` binds the **exact admitted decimal numbers** for
`strategyAssetWeight` and `benchmarkExpenseFraction`, not values rounded to
the default Python `Decimal` context. The canonical representation strips
only base-ten trailing zeros from the exact coefficient and updates the exponent.
Thus `0.5` and `0.50` are the same numeric policy, while two distinct
40-digit fractions remain distinct precommitments. The original source
implementation used context-rounded `Decimal.normalize()` and could map
different values to the same digest; historical receipts must be interpreted
using their pinned source revision, not silently replayed under a newer one.

The source-native Research contract's high-precision counterexample and real
`review_replayed_candidate` admission are separate implementation witnesses.
They do not prove authenticity of the original freeze timestamp, prospective
market source or a profitable investment edge. No new Research owner or Skill
registry is introduced.
