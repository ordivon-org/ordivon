---
name: finance-experiment-review
description: Use when an Ordivon Agent freezes a point-in-time Finance hypothesis, evaluates prospective holdout readiness, or compares it with an existing investment candidate and passive benchmark. Reuse Capital's mature source owners rather than creating another Agent or investment engine.
compatibility: Ordivon domains/capital; existing Runtime/Harness, pinned mise/uv Python toolchain.
metadata:
  source-authority: Ordivon Finance Research and Portfolio native contracts
---

# Finance Experiment Review

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
   before the prospective holdout starts. Persist the returned artifact
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
