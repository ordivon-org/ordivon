# Market Capital Observation Sensors R1

Date: 2026-09-19
Status: EXPERIMENTAL / READ-ONLY DERIVED OBSERVATION

## Purpose

R1 adds small finance-native observation and reconciliation calculations without turning descriptive observations into forecasts or execution authority:

1. **Open-interest change** — derives ΔOI over an explicitly bounded ordered window.
2. **Repeated microstructure** — summarizes persistence across multiple book/trade-flow snapshots instead of treating one frame as a directional signal.
3. **Underlying reopen reconciliation** — compares an out-of-hours perpetual reference with the reopened underlying cash market and, when available, a post-open perpetual observation.

## Authority boundary

These sensors:

- do not fetch provider data;
- do not read credentials;
- do not own exchange truth;
- do not infer causal contribution;
- do not estimate forecast probability;
- do not recommend or submit orders;
- do not create financial write authority.

They consume already-observed provider/domain data and emit derived observation evidence.

## Open-interest change

Input requires at least two strictly time-ordered observations of the same instrument.

Output includes:

- start/end OI USD;
- absolute ΔOI;
- percentage ΔOI when the baseline is non-zero;
- exact observation span.

The OKX public adapter also reads provider 5m and 1H OI-history windows. It excludes the current incomplete bucket by requiring `bucket_timestamp + period <= as_of`, then derives ΔOI from the two latest completed buckets. The short live-capture-window ΔOI is retained separately and is never mislabeled as a 5m/1H change.

OI level or ΔOI alone is not leverage-crowding truth. downstream market-risk analysis may combine ΔOI with funding and basis only as bounded evidence.

## Repeated microstructure

Input requires repeated observations containing:

- book imbalance in [-1, 1];
- recent trade buy share in [0, 1];
- spread in bps;
- strictly increasing timestamps.

The caller selects the persistence ratio. A directional standing is emitted only when both book and recent trade-flow observations persist in the same direction for at least that ratio. Otherwise the result is `MIXED_OR_NONPERSISTENT_FLOW`.

A persistent sell/buy tilt is still not a reversal/continuation forecast.

## Underlying reopen reconciliation

Before the underlying reopens, the sensor may record `RECONCILIATION_PENDING` with no tolerance selected. Once an underlying reopen price is supplied, the caller must also supply an explicit `validation_tolerance_bps`; R1 deliberately contains no universal market threshold.

Possible descriptive standings:

- `RECONCILIATION_PENDING`
- `UNDERLYING_VALIDATED_WEEKEND_REGION`
- `UNDERLYING_REOPEN_DISAGREEMENT`
- `PERP_REANCHORED_TO_UNDERLYING`
- `PARTIAL_CONVERGENCE`
- `DISAGREEMENT_PERSISTS`

These are price-reconciliation states, not causal explanations.

## downstream market-risk analysis integration

`merge_market_observations()` binds derived OI and repeated-microstructure observations to the same instrument identity before downstream risk analysis:

- `openInterestChangePct`
- mean repeated book imbalance
- mean repeated trade buy share
- microstructure standing/sample count

This closes the previous downstream market-risk analysis evidence gaps without granting the sensors any provider or execution authority.
