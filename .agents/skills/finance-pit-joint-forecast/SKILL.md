---
name: finance-pit-joint-forecast
description: Construct past-only vintage-aware joint ETF return scenarios and prequential probability scoring before invoking Capital's existing multistage CRRA optimizer. Research-only; never broker/Paper Ledger effects.
---

# Finance PIT joint forecasting — Agent skill

## When to use

Use when a Capital Agent needs to construct a reproducible historical information set, jointly sampled ETF one-month joint gross-return scenarios, a proper probabilistic score, or an exact `Portfolio.multistage_policy` JSON input from externally provided economic contracts. This is a **Research input adapter**, NOT an order, market data authority, financial adviser, or alternative portfolio optimizer.

## Required evidence before execution

- `assets`: stable ETF identity, source-owned consecutive monthly ETF valuation endpoints (one per calendar month, not daily quotes), and price observations with asset/session/positive adjusted close.
- `published_at`: real provider/release availability timestamp with timezone. Do not fabricate historical vintage timestamps from today's downloaded revised prices.
- `raw_source_sha256`: raw response identity from a source owner. A matching SHA proves bytes, **not** independently authenticated exchange market truth.
- `source_standing`: explicit verified-origin or unverified-secondary vendor standing.
- `as_of`: exact historical decision instant, NOT today's timestamp unless it is truly a decision today.
- `economic_contract`: risk aversion `gamma`, initial margin for each ETF, transaction costs, per-scenario maintenance ratios, cash and loan gross returns. These values are required from the human/econometric/Broker owner; never fill with arbitrary 40%, 1.5x, 7% APR or other defaults.

## Run

```bash
cd domains/capital
PYTHONPATH=src uv run --no-sync python \
  -m ordivon_capital.research.pit_joint_forecast --input /path/to/market-and-economic.json
```

The output has `optimizer_input`, `forecast_evidence`, `effects` and `input_sha256`. Hand the **unmodified** `optimizer_input` JSON into the published `Portfolio/multistage_policy.py` consumer (its CLI accepts exactly `gamma` + `nodes`). The evidence envelope stays with Research/Artifact, not on a Broker order.

Do not call this a verified *conditional forecast*. The default forecast is the empirical distribution of past **joint** observed ETF return vectors. If a new conditional model is introduced, pre-register its information set and model class, then use the same `weighted_energy_score` on genuine future observed outcomes. Compare to this simple baseline before retaining complexity.

## Owner and verification boundaries

Capital/Markets supplies source, adjusted-price semantics and exchange calendar. Capital/Research chooses observable vintages, forms distributions and runs independent prequential scores. Capital/Portfolio alone decides conditional economic allocation. Capital/Trading owns actual brokerage rules, fill and forced liquidation. Capital/Accounting owns the only real Paper/settlement book. Runtime/Artifact own execution and evidence placement.

Reviewable invariants:
1. Every selected source price has `published_at <= as_of`.
2. Historical source revisions cannot alter an earlier frozen forecast.
3. No cross-asset independence assumption, hidden future branch or missing-day forward fill.
4. Independent `gamma`, borrowing costs and margin requirements are **not invented**.
5. Unknown source or financial-contract fact remains `UNKNOWN`, not a zero, a guess or a false claim.
6. Human-facing output distinguishes empirical distribution score from investor return and broker applicability.

Verification: `python -m unittest discover -s domains/capital/tests -p test_pit_joint_forecast.py -v` (8 pure property/consumer checks). Full Ordivon Owner verification and canonical Skill registry must occur when the change reaches `main`; do not claim that preparing a SKILL.md file installs or activates it.

## Retire and reuse

If an existing validated Markets/Research module already provides these exact as-of and joint-scenario semantics, delete this adapter after migrating its actual consumers rather than keeping two feature-compatible versions. Do not remove unrelated active worktrees or source files based only on age or filenames.


## Optional conditional pilot in the original interface

Set a top-level JSON field "forecast_method" to "lagged_knn" to
reweight one-month joint return scenarios based only on complete
historical consecutive month-pairs (r_t, r_t+1). Default remains
"empirical". The conditioner uses Euclidean distance between
log-gross joint return vectors and a fully disclosed integer square-root
neighbor count. This is a pilot estimator, NOT calibrated market probability
or proof of investment advantage. Insufficient historical transitions
produce an explicit error; no invented default market rates or silent
fallback.

Both methods return the existing one-step optimizer_input of
gamma and nodes, with separate conditioning evidence. Prequential
validation can use the same forecast_method and reports energy and
variogram scores; the latter reveals dependence misspecification but is
not strictly proper by itself. Never compare these estimates to real market
outcomes without authenticated historical price publication vintages.


For broker maintenance that is invariant across return outcomes,
"economic_contract" may contain an explicit per-asset
"maintenance_by_asset" array instead of "scenario_maintenance".
The adapter repeats only the caller-supplied broker numbers once the
forecast scenario count is known; actual state-specific margin contracts
must continue to use scenario_maintenance. Never assume one uniform
rate applies to a real brokerage account without provider evidence.


## Historical multi-month structural scenario trees (not a predictive upgrade)

The same canonical Research CLI provides `--mode monthly-tree`, accepting an
explicit `trading_sessions` exchange calendar, an `as_of` timestamp, actual
published price vintages and complete stage-wise economic terms. It emits
`optimizer_input` for the **existing** Portfolio multistage CRRA solver.
The distinct `research/pit_monthly_paths.py` module owns only the historical
path-prefix construction and delegates market vintage selection to
`research/pit_joint_forecast.py`. No parallel optimizer/registry is created.

**Human:** historical full-path replay preserves serial dependence, but a
singleton observed prefix can identify its historical future; never report an
in-sample optimization result as forward investment alpha. Verify the source
calendar and point-in-time market data separately.

**Agent:** prefer the `one-step` conditional lagged-KNN pilot only for
prequential evaluation; it is not yet a calibrated multi-step Markov model.
`monthly-tree` is a structural nonanticipativity/consumer research fixture.
Read `forecast_evidence.predictive_recursion` and
`standing=STRUCTURAL_HISTORICAL_PATH_TREE_NOT_PREDICTIVE_ADMISSIBLE` before
interpreting a scenario value. Preserve distinct forecast, economic contract,
solver and effect standing. Use the existing `finance-experiment-review`
Skill for forward-validation methodology.

Run: `python -m pytest tests/test_pit_joint_forecast.py tests/test_pit_monthly_tree.py tests/test_terminal_liabilities.py` from `domains/capital`.
