# Portfolio Scenario Analysis and Pre-Trade Controls R1

Date: 2026-09-19
Status: EXPERIMENTAL / READ-ONLY

## Scope

This path performs standard what-if portfolio analysis and pre-trade evidence-completeness controls.

It does not choose a trade, recommend a quantity, rank scenarios, approve an action, or grant external-effect authority.

## Explicit scenario sizing

Scenario analysis accepts only EXPLICIT_CALLER_COUNTERFACTUAL sizing. No quantity is promoted from regression beta, current leverage, historical position size, inferred investor risk preference, or the legacy Wave A validation IPS.

## Scenario classes

DE_RISK reduces an existing position by an explicit fraction and calculates mechanical exposure changes.

HEDGE adds an explicit signed exposure to a named candidate hedge. It must declare a target factor, and the absolute named factor exposure must actually decline. Historical dependence, margin, liquidity, and funding/basis evidence remain separate requirements.

DIVERSIFY reduces an explicit source exposure and adds an explicit destination exposure. Lower historical correlation is diversification evidence, not causal hedge truth.

HOLD cannot contain position-changing fields.

RECONCILE cannot contain position-changing fields and requires a concrete next evidence boundary.

## Scenario outputs

Each what-if calculation reports baseline/projected gross and net exposure, concentration change, explicit factor-exposure deltas, optional first-order named shock projection, changed instrument identities, and the absence of projected available equity unless margin evidence is measured separately.

The first-order shock calculation is not VaR, expected shortfall, liquidation probability, or a forecast.

## Pre-trade evidence controls

Controls distinguish PASS, FAIL, INCOMPLETE, and NOT_REQUIRED.

Every position-changing scenario requires execution-liquidity evidence. HEDGE and DIVERSIFY additionally require incremental margin and funding/basis carry evidence.

HEDGE requires historical dependence evidence and mechanically reduced named factor exposure. DIVERSIFY requires covariance/factor evidence without upgrading low correlation into causal hedge truth. RECONCILE requires a defined next evidence boundary.

A PASS means required evidence is present under the supplied policy. It does not mean the action is approved.

## Governance

Scenario calculations and evidence controls are classified as non-model calculation/control in the quantitative component inventory. Any quantitative model used as an input retains its own validation and monitoring obligations.
