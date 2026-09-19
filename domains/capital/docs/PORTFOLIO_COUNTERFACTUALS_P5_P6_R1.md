# Portfolio Counterfactuals P5/P6 R1

Date: 2026-09-19
Status: EXPERIMENTAL / READ-ONLY COUNTERFACTUAL AND EVIDENCE GATE

## Scope

P5/P6 extends Portfolio Risk Observatory without creating an allocator or execution path.

- **P5 Action Counterfactuals** applies explicit research scenarios to a current exposure ledger and calculates mechanical exposure changes.
- **P6 Constraint Gate** tests whether the evidence required to interpret a scenario is present.

Neither node chooses a trade, recommends a quantity, ranks scenarios, or grants effect authority.

## Sizing law

P5 accepts only:

`sizingBasis = EXPLICIT_CALLER_COUNTERFACTUAL`.

The system does not derive a trade size from:

- minimum-variance beta;
- current leverage;
- historical position size;
- an implicit risk preference;
- the legacy Wave A IPS.

A beta can motivate an externally specified research scenario, but P5 does not promote it into a recommended quantity.

## P5 action semantics

### DE_RISK

Reduces an existing position by an explicit fraction.

Mechanical claims:

- gross exposure should fall;
- the named-position first-order shock sensitivity should fall;
- no new instrument, funding or hedge-dependence model is introduced.

Exact margin release is not invented when provider/account margin evidence is absent.

### HEDGE

Adds an explicit signed notional to a named candidate hedge.

Mechanical claims may include:

- net directional exposure changes;
- gross exposure may increase;
- named factor exposure may change.

A HEDGE scenario must name `targetFactor`. P5 mechanically compares the absolute signed exposure to that factor before and after the scenario. A label cannot turn an exposure increase into a hedge: P6 fails `TARGET_FACTOR_MECHANICS` unless the named factor exposure is actually reduced.

A hedge claim additionally requires separate P6 evidence for dependence, margin, liquidity and funding/basis carry.

### DIVERSIFY

Reduces an explicit source position and adds an explicit destination position.

The destination is not called a hedge merely because historical correlation is low.

P6 requires destination covariance/factor evidence and rejects attempts to upgrade low correlation into causal hedge truth.

### HOLD

No position-changing fields are allowed.

### RECONCILE

No position-changing fields are allowed. P6 requires an explicit next evidence/signpost boundary.

## P5 output

Each counterfactual emits:

- baseline and projected gross/net exposure;
- concentration change;
- per-factor signed exposure deltas when loadings are supplied;
- optional first-order named shock projection;
- changed instrument identities;
- explicit absence of projected available equity unless margin evidence is separately supplied.

The first-order shock projection is not VaR, expected shortfall, liquidation probability or a return forecast.

## P6 gate

P6 separates **evidence completeness** from **action approval**.

Possible check states:

- `PASS`
- `FAIL`
- `INCOMPLETE`
- `NOT_REQUIRED`

Gate standing:

- any FAIL -> `FAIL`;
- otherwise any INCOMPLETE -> `INCOMPLETE`;
- otherwise -> `PASS`.

Even a `PASS` gate has:

- `actionApproved = false`
- `effectAdmissionGranted = false`
- `tradeRecommendationProduced = false`.

### Position-change and new-position evidence

Every position-changing action (DE_RISK, HEDGE, DIVERSIFY) requires measured execution spread/impact evidence. Reducing risk does not make transaction cost disappear.

HEDGE and DIVERSIFY additionally require measured evidence for:

- incremental margin;
- funding/basis carry.

HEDGE additionally requires historical dependence evidence with sample count and the non-recommendation boundary preserved.

DIVERSIFY requires covariance/factor evidence without a causal-hedge claim.

RECONCILE requires a defined next evidence boundary.

## Composition law

P5/P6 is deliberately parallel:

```
explicit scenario A -> counterfactual A -> gate A
explicit scenario B -> counterfactual B -> gate B
explicit scenario C -> counterfactual C -> gate C
```

No winner is selected.

Ranking and optimization remain deferred until:

1. P4 risk budget is explicit;
2. P6 evidence is complete;
3. the objective function and authority for ranking are separately defined.
