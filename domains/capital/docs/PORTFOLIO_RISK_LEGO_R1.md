# Portfolio Risk LEGO R1

Date: 2026-09-19
Status: RESEARCH / READ-ONLY PORTFOLIO RISK CONTRACT

## Purpose

Portfolio Risk LEGO R1 defines the minimum architecture needed to reason about concentration, de-risking, hedging, diversification, and event-sensitive risk without turning Market Capital into an execution recommender.

It exists because these actions are not synonyms:

- **DE-RISK** reduces an existing gross exposure.
- **HEDGE** adds an offsetting exposure to reduce a named factor or covariance component.
- **DIVERSIFY** reallocates capital toward materially different risk sources.
- **HOLD** preserves current exposure when no bounded change is justified.
- **RECONCILE** waits for a known information boundary before changing the risk model.

The first design law is therefore:

```
number of positions != diversification
different tickers != different risk factors
lower net beta != lower gross/margin/liquidity risk
historical correlation != stable hedge relationship
```

## LEGO role audit

Following the local Lens Router / Lens Portfolio contracts, this problem does not justify many cross-cutting lenses.

### LENS

**regime-shift** is the single primary cross-cutting lens.

It owns questions such as:

- has the dependence structure changed?
- is an event boundary changing price discovery?
- are correlations/betas migrating?
- which signposts should cause pause/re-estimation/reversal?

### DOMAIN_METHOD

The following remain finance-native methods and do not count as LEGO lenses:

- gross/net notional and leverage arithmetic;
- margin/liquidation and cash-buffer analysis;
- covariance/correlation estimation;
- rolling and downside dependence;
- regression/factor beta;
- minimum-variance hedge ratio;
- factor-risk attribution;
- stress/scenario analysis;
- liquidity, spread, funding and basis analysis;
- covariance shrinkage when the investable universe becomes large enough to justify it.

### OPERATOR

- LEGO Lens Router selects the cross-cutting lens.
- LEGO Lens Portfolio prevents domain methods from inflating the active-lens count.
- Market Capital truth/effect gates preserve read-only analysis authority.

### DEFERRED

- mean-variance optimization as an allocation owner;
- multi-factor optimizer;
- covariance shrinkage;
- dynamic hedge optimizer.

These become useful only after the observation, factor, constraint and validation layers are reliable.

### REJECTED

- number-of-tickers as a diversification metric;
- full-sample correlation as the sole hedge decision;
- equal-weight validation portfolio as a live allocation rule;
- adding a hedge without measuring the resulting gross exposure and margin burden;
- interpreting a minimum-variance hedge as a return forecast;
- treating a low-correlation asset as a hedge for a specific SNDK factor without a mechanism.

## System boundary

System of interest:

> A read-only portfolio-risk analysis layer that consumes provider/private observations, public market histories and explicit policy inputs, then produces typed exposure/factor/risk/action evidence without financial write authority.

### External authorities

- provider/exchange state owns balances, positions, mark/index/funding, margin and order truth;
- public market providers own historical market observations;
- mature finance methods own covariance, factor, hedge-ratio and portfolio-risk mathematics;
- the user owns risk tolerance and action approval;
- Market Capital owns normalization, bounded derived analysis, provenance and policy gates.

## LEGO graph

```
P0 Private/Public Reality
        |
        v
P1 Exposure Ledger
        |
        +--> gross / net / concentration / leverage / cash buffer
        |
        v
P2 Factor Observatory
        |
        +--> market / tech / semiconductor / memory / idiosyncratic proxies
        +--> beta / residual / attribution
        |
        v
P3 Regime-Conditioned Dependence
        |
        +--> full-window correlation
        +--> rolling correlation
        +--> downside correlation
        +--> beta stability
        +--> event/session regime
        |
        v
P4 Risk Budget
        |
        +--> user-specified max loss / gross / concentration constraints
        +--> no inferred risk tolerance
        |
        v
P5 Action Counterfactuals
        |
        +--> DE-RISK
        +--> HEDGE
        +--> DIVERSIFY
        +--> HOLD
        +--> RECONCILE
        |
        v
P6 Constraint Gate
        |
        +--> margin
        +--> liquidity/spread
        +--> funding/basis
        +--> gross exposure
        +--> correlation/beta instability
        |
        v
P7 Stress + Robustness
        |
        +--> shock scenarios
        +--> regime changes
        +--> hedge breakdown
        +--> event gap
        |
        v
P8 Portfolio Regime Card
        |
        X no forecast truth
        X no automatic allocation truth
        X no order authority
```

## Node contracts

### P1 Exposure Ledger

Minimum outputs:

- account equity as runtime-private observation;
- instrument notional;
- gross exposure / equity;
- net directional exposure;
- concentration by instrument and factor;
- initial/maintenance margin burden;
- cash/available-equity buffer.

Private account values must not be committed to source control.

### P2 Factor Observatory

Start with interpretable proxies rather than an opaque optimizer.

For SNDK the first candidate proxy set is:

- memory: MU, WDC;
- semiconductor: SMH, AMD, NVDA;
- broad growth: QQQ;
- broad equity: SPY;
- alternative risk sources: XAU, BTC, ETH.

A proxy can be useful for measurement without being a suitable trade.

### P3 Regime-Conditioned Dependence

Never emit only one correlation number.

Minimum evidence:

- long-window correlation;
- 20d and 60d rolling correlation;
- downside correlation conditional on SNDK negative-return days;
- regression hedge beta;
- rolling-beta range/dispersion;
- sample count and exact bar/session convention.

If dependence changes materially by window or downside state, mark hedge relationship unstable rather than averaging it away.

### P4 Risk Budget

Risk tolerance is an explicit input, not inferred from account behavior.

Example policy questions:

- maximum acceptable account-equity loss under a -10% SNDK shock;
- maximum gross notional / equity;
- maximum single-instrument risk contribution;
- minimum available-equity buffer;
- maximum hedge gross-up;
- whether event-gap risk must be capped before a known event boundary.

No default becomes investment truth.

### P5 Action Counterfactuals

Every action candidate must state which risk it changes.

**DE-RISK**
- reduces SNDK notional;
- directly reduces directional, margin and liquidation sensitivity;
- introduces no second basis/funding/correlation model.

**HEDGE**
- adds a short/offsetting factor exposure;
- can reduce covariance-driven risk;
- usually increases gross notional and introduces hedge basis, funding, liquidity and correlation-breakdown risk.

**DIVERSIFY**
- reallocates capital to a distinct risk source;
- should be assessed by total-portfolio covariance/factor contribution, not ticker count.

**HOLD**
- valid when the current risk budget is satisfied and marginal action would add more model/transaction risk than it removes.

**RECONCILE**
- preserves option value when a known event/session boundary is near and new evidence will materially change the model.

### P6 Constraint Gate

A hedge is inadmissible as a risk-reduction claim if any of the following is unmeasured:

- resulting gross exposure;
- incremental initial/maintenance margin;
- funding/basis cost;
- execution spread/liquidity;
- hedge-factor instability;
- downside dependence;
- event/session mismatch.

### P7 Stress + Robustness

Required counterfactuals include:

- SNDK idiosyncratic -5/-10/-20%;
- memory/semiconductor sector shock;
- broad-tech risk-off;
- hedge correlation breakdown;
- weekend/perpetual versus underlying reopen gap;
- funding/basis dislocation;
- margin-buffer deterioration.

## Current public SNDK study

A bounded OKX public-data study on 2026-09-19 used 178 completed daily SNDK returns where available.

Selected results:

| Proxy | Full corr | 20d corr | 60d corr | Downside corr | Full-sample hedge beta |
| --- | ---: | ---: | ---: | ---: | ---: |
| MU | 0.844 | 0.838 | 0.879 | 0.751 | 1.075 |
| SMH | 0.750 | 0.518 | 0.686 | 0.691 | 2.140 |
| WDC | 0.738 | 0.631 | 0.778 | 0.576 | 0.889 |
| AMD | 0.643 | 0.310 | 0.692 | 0.572 | 0.914 |
| QQQ | 0.611 | 0.154 | 0.547 | 0.481 | 3.177 |
| NVDA | 0.382 | 0.327 | 0.349 | 0.399 | 1.155 |
| SPY | 0.377 | -0.174 | 0.197 | 0.206 | 3.041 |
| XAU | 0.248 | -0.236 | 0.133 | 0.204 | 1.103 |
| BTC | 0.160 | 0.106 | 0.048 | 0.037 | 0.428 |
| ETH | 0.148 | 0.104 | 0.041 | 0.036 | 0.301 |

Interpretation boundaries:

- MU currently behaves most like a memory-factor hedge proxy, not a diversifier.
- SMH/WDC/AMD are still substantially overlapping semiconductor/storage risks.
- QQQ/SPY dependence is visibly window-sensitive.
- XAU/BTC/ETH have lower historical dependence but low correlation alone does not identify a hedge mechanism.
- the 20d versus 60d changes show why one static hedge ratio is insufficient.

## Mature-method alignment

External research supports the architecture rather than replacing provider truth:

- CFA portfolio-risk material treats covariance/correlation as core portfolio-risk inputs and emphasizes that diversification depends on less-than-perfect correlation.
- CFA 2026 asset-allocation material warns that mean-variance optimization is input-sensitive, can produce concentrated allocations, and can leave underlying risk sources undiversified even when holdings look diversified.
- CFA multifactor material treats factor models as standard tools for risk attribution, exposure control and portfolio construction.
- MSCI's factor-risk frameworks likewise decompose portfolio risk into factor exposures and contributions rather than counting holdings.
- CME hedging material uses covariance/volatility/beta-based hedge ratios and explicitly treats imperfect correlation as residual basis/tracking risk.
- OKX cross-margin documentation makes gross/margin effects first-class: adding a hedge may offset PnL directions while still changing shared-margin requirements and liquidation dynamics.

## Research consequences

1. The next production candidate is **Portfolio Risk Observatory**, not Portfolio Optimizer.
2. Risk budget must precede hedge selection.
3. Full hedge ratios are descriptive counterfactuals, not recommended sizes.
4. A candidate hedge must be evaluated for both variance reduction and gross-up/margin cost.
5. Diversification analysis must use risk factors and downside/rolling dependence.
6. Private account state stays runtime-private and is never committed as research evidence.
7. SNDK's 2026-09-21 S&P 100 effective-date boundary remains a Regime Card signpost; event-specific action is not inferred from index inclusion alone.

## Stop condition

R1 is complete when:

- each action class has a typed risk delta;
- risk budget inputs are explicit;
- factor/dependence evidence includes regime/stability diagnostics;
- gross/margin/funding/liquidity costs are present;
- private reality is non-persistent by default;
- the output remains read-only and non-prescriptive.
