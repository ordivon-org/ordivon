---
name: finance-experiment-review
description: Use when an Ordivon Agent freezes a point-in-time Finance hypothesis, evaluates prospective holdout readiness, or compares it with an existing investment candidate and passive benchmark. Reuse Capital's mature source owners rather than creating another Agent or investment engine.
compatibility: Ordivon domains/capital; existing Runtime/Harness, pinned mise/uv Python toolchain.
metadata:
  source-authority: Ordivon Finance Research and Portfolio native contracts
---

# Finance Experiment Review

For Human first use and finance capability discovery, see the
[Finance human guide](../../../domains/capital/docs/FINANCE_HUMAN_GUIDE_R1.md).
This Skill is the scoped Agent research procedure. The natural Owner
source identity is documented in `domains/capital/docs/ARCHITECTURE.md`;
other task Skills should only be loaded when needed.


Finance is an investment-focused capability within Capital, not another
Agent platform, brokerage adapter or source/package identity.

## Existing natural owners: composition, not new implementation

- **Research** `research/experiment_protocol.py` freezes a prospective
  precommitment before any holdout is examined. CLI:
  `domains/capital/scripts/run-finance-lego freeze-experiment < plan.json`.
  It binds declared historical sources, availability at freeze, source
  snapshot/code/config/environment identities, disjoint train/validation/
  prospective holdout, and planned trial family. A returned digest is not an
  independent historical timestamp attestation or data-provider signature.
- **Research** `scripts/run-finance-lego assess-holdout < request.json`
  evaluates frozen protocol and declared evidence. Missing verification is
  `UNKNOWN`; contradictory evidence is `REJECTED`; `REVIEW_REQUIRED`
  does not authorize capital or orders.
- **Research economic candidate evaluation** stays in existing
  `research/investment_candidate.py`, with exact manifest/source/holdout
  file inputs. It is the authoritative Capital source consumer for
  benchmark/return cost-matched evaluation; do not recompute net returns in
  this Skill or the precommitment protocol.
- **Investment Mode** cash-flow-matched passive benchmark stays in
  `portfolio/passive_benchmark.py`. It accepts an explicit prior input file,
  per-period shared deposits, strategy/benchmark gross returns and expenses.
  Run `python -m ordivon_capital.portfolio.passive_benchmark --input replay.json`
  using the existing Capital Python environment. No secondary index replay
  engine or separate portfolio optimization operator is necessary.
- **Portfolio allocation** stays in
  `scripts/run-strategic-contribution-brief`; protect reserves and model
  contribution-only target allocation without placing orders.

## Method

1. Select the simplest cash-flow-matched passive benchmark before claiming a
   strategy has economic value. Contributions, return conventions and
   period timing must be comparable.
2. Freeze hypothesis, code/config/environment and historical data vintage
   before the prospective holdout starts. Dates use UTC calendar-day cuts;
   crossing a timezone boundary does not authorize same-day holdout use.
   Persist the returned artifact
   through the actual Runtime natural owner; SHA-256 does not prove source
   authenticity or that freeze happened at the claimed past time.
3. State dataset point-in-time availability, trial family size, cost model
   and opportunity-cost comparator. Evaluate only strictly post-freeze
   outcomes, distinguish research metrics from order execution.
4. Use `investment_candidate.py` for supplied actual candidate economic
   evidence and `passive_benchmark.py` for comparison. Request independent
   replay, publication time proof and uncertainty estimates separately:
   current source checks cannot assert those facts.
5. Keep research/economic evidence, risk review, capital authorization and
   broker execution as different responsibilities. All source LEGO outputs
   are read-only; no result grants a provider write effect.

## Exact paired PIT probability forecast falsification

Use the same existing Capital Research source instead of making a third
score evaluator: `ordivon_capital.research.pit_joint_forecast.compare_pit_prequential_forecasts`.
Provide actual dated historical price vintages, named ETFs, the common
monthly calendar, per-session frozen decision instants and the later
evaluation time. It reuses `prequential_energy_evaluation` twice on the
**identical** observed decision/outcome pairs, for
`baseline_method=empirical` and `candidate_method=lagged_knn`, and reports
the paired candidate-minus-baseline energy losses, their arithmetic mean
and individual frozen forecast SHA256 references.

A positive loss differential means worse candidate probability scoring,
**not** a real market leverage recommendation, confidence interval or
trading signal. The function intentionally performs no statistical
significance test. Diebold-Mariano time-series inference needs a defensible
dependence model, and comparisons over many chosen models additionally
need multiplicity adjustment (e.g. Hansen SPA), not a guessed alpha
threshold or hindsight-based selection.
The caller must store independent pre-holdout source and forecast evidence
through the canonical Research/Artifact owners. `READ_ONLY_NO_TRADE_NO_ACCOUNTING`
remains mandatory.

## Native precommitment to source-replay consumer

Prepare a **pre-holdout candidate policy** with the v2 replayable candidate's
`schemaVersion`, `kind`, `candidateId`, `hypothesis`, `frozenAt`,
`trialCount`, `currency`, `costCoverage`, `strategyAssetWeight` and
`benchmarkExpenseFraction`. These are only fields available before
holdout; do not include future `sourceSha256` or `holdoutSha256`.

From the repo root, use the existing Capital runner:

    domains/capital/scripts/run-finance-lego fingerprint-policy < policy.json

Copy the resulting `configDigest` into the research plan, then
`freeze-experiment` and persist the receipt through the Runtime natural
owner **before** holdout. SHA-256 alone cannot attest historical timing.

After the observations and derived returns exist, build a native v2
manifest with the same precommitted policy and postfreeze source/holdout
digests in **raw lowercase 64-hex**, as required by
`investment_candidate.py`:

    domains/capital/scripts/run-finance-lego review-candidate --manifest /path/to/candidate.json --source /path/to/source.json --holdout /path/to/holdout.json < review-request.json

CLI option paths are relative to `domains/capital` or absolute. Shell redirection
remains relative to the invoking shell. The request is JSON with `frozen` (frozen receipt) and `evaluatedAt`
(UTC-offset time). This thin adapter does not duplicate return arithmetic.
It rejects retroactively changed weights, trials and false source-derived
returns. Missing independent reproduction and real publisher authenticity
remain UNKNOWN. Research evidence never grants capital allocation or
external order effects.

## Exact precommitted decimal identity

The `fingerprint-policy` source contract now canonicalizes strategy weights and
benchmark expenses by the exact finite Decimal coefficient/exponent, stripping
only base-ten trailing zeroes. Distinct admitted values beyond 28 decimal digits
must not share a `configDigest`. Re-evaluate existing historical policy digests
using their pinned historical source revision; never silently reinterpret an
already-persisted frozen receipt with the new code. Numeric-equivalent spellings
such as `0.5`/`0.50` share the current policy identity.

For a new experiment, fingerprint the complete policy *before* freezing, then
persist that exact digest through the native Runtime owner before holdout.
The source-native consumer should reject changed high-precision weights as
`PRECOMMITTED_POLICY_MISMATCH`. A digest checks local declared policy identity,
not independent historical time or provider authenticity.

## Executable protocol interface

The precommitment input to `freeze-experiment` must be JSON with
`schemaVersion=1`, `kind=ordivon.capital.research.plan`,
`effectBoundary=RESEARCH_ONLY`, a nonblank `hypothesisId`, `baselineId`,
`metricDefinition`, `frozenAt` timezone-aware timestamp, 40-character
`codeRevision`, SHA-256 `configDigest` and `environmentDigest`, positive
`trialsPlanned`, non-overlapping chronological `partitions` and
`historicalSources` with `sourceId`, `snapshotDigest`,
`observedThrough`, `availableAt`.

`assess-holdout` accepts `{"frozen": frozenReceipt, "result": {...}}` where
result fields include exact frozen plan identity, holdout observation and
availability timestamps, source digest, declared trial count, cost/baseline
provenance and independent reproducibility standing. A missing result returns
`UNKNOWN`, not a fabricated PASS. Neither operation fetches market facts,
stores a durable model, invokes a broker or requests financial permissions.

## Evidence and qualification

Native owner verification:
`mise run //domains/capital:verify`. R2.1 source plan CA10 is in
`planning/lego-plan-r1.json`; external owner and physical module inventory
remain authoritative in `config/external_owner_census.json` and
`config/capital_domain_taxonomy.json`. Formal model proof, external data
publisher authenticity, exhaustive search-family accounting, actual provider
execution and independent real-money suitability are **UNKNOWN** until an
observed consumer supplies qualifying evidence.

## Monthly 1r historical-leverage Research: fee-aware rebalance contract

Use `research/unit_r_dca.py` and `docs/UNIT_R_DCA_LONG_HISTORY_R1.md`,
not a new brokerage, pricing engine, or research scheduler. The pure
`solve_turnover_adjusted_exposure` is the sole Research local rebalance
solver and evaluates `gross=target*(equity-fee*abs(gross-prior_gross))`.
It rejects previous-position liquidation costs that would exhaust equity.
The replay continues to own intraday margin checking, 1r monthly flow,
strictly earlier data for risk signals, and descriptive XIRR/drawdown.

Run existing owner verification: `mise run //domains/capital:verify`. Its
formal prerequisites include `verify:formal:unit-r-margin` (two UNSAT, one
SAT) and `verify:formal:unit-r-rebalance` (seven UNSAT, two SAT) using the
repo's pinned Z3, no custom solver. These prove **exact-real static algebra**
only; Python float behavior is supported separately by native consumer tests,
not by an unbounded implementation-refinement proof. Source publisher rights,
future margin gaps, broker liquidation and real alpha remain UNKNOWN.
