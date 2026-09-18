# Market Capital Regime Card R1

Date: 2026-09-19  
Status: EXPERIMENTAL / READ-ONLY ANALYSIS NODE

## Purpose

Regime Card R1 converts already-observed market, derivative, context, and optional position state into a bounded machine-readable regime-analysis projection.

It does **not** fetch provider data, own market truth, estimate forecast probabilities, recommend trades, or create external financial write authority.

```
provider/domain observations
        |
        v
domain-native finance normalization
        |
        v
Regime Card R1
        |
        +--> state / divergence / evidence gaps
        +--> competing hypotheses + falsifiers
        +--> signpost projection
        |
        X no order authority
        X no causal identification
        X no forecast truth
```

## Method boundary

LEGO Lens Router R1 selects `regime-shift` as the composite cross-cutting lens when the problem materially involves operating-regime identity, delays, feedback, structural-change hypotheses, and robust signposts.

The finance-native parts remain finance-native:

- market microstructure;
- perpetual basis/funding/open interest;
- time-series indicators;
- position arithmetic and risk;
- exchange/underlying session mechanics.

The Regime Card does not duplicate those methods. It consumes their observations.

## Truth role

Every output carries:

```
truthRole = analysis-evidence-not-forecast-truth
causalStanding = NOT_IDENTIFIED_FROM_OBSERVATIONAL_CARD
forecastProbabilityProduced = false
tradeRecommendationProduced = false
externalFinancialWriteAttempted = false
```

A passing test is not market truth. A Regime Card is not Economic Truth, Capital Truth, or ExternalFinancialWriteAdmission.

## Minimum inputs

Market observation:

- instrumentId
- observedAtMs
- last / mark / index
- open24h / high24h / low24h
- fundingCurrent
- openInterestUsd

Context:

- underlyingMarketOpen
- indexSourceMode

Optional discriminating sensors:

- openInterestChangePct
- fundingRecentMean
- bookImbalance
- tradeBuyShare
- technical RSI inputs by horizon

Optional position projection:

- quantity
- averagePrice
- leverage
- marginMode
- observed liquidationPrice

Optional named signposts are price levels only. They are observations/decision coordinates, not order instructions.

## Fail-closed laws

1. Missing or invalid canonical prices fail rather than being silently coerced.
2. OI level without OI change cannot establish leverage crowding; output is `NOT_IDENTIFIED_MISSING_OI_CHANGE`.
3. One adverse order-flow snapshot may create a divergence, never a reversal claim.
4. Out-of-hours derivative discovery is a distinct regime identity when the underlying market is closed.
5. Causal contribution of catalysts is never inferred from this observational card.
6. Position-level liquidation is marked dynamic because cross-margin/account state can move it.
7. The node contains no network or credential code and no execution/write path.

## Current next evidence

The highest-value follow-up sensors are:

- time-aligned open-interest change;
- repeated microstructure snapshots instead of one book cut;
- last underlying reference and reopening reconciliation;
- event-study baseline where an event mechanism is claimed;
- factor/sector decomposition for exogenous versus instrument-specific moves.
