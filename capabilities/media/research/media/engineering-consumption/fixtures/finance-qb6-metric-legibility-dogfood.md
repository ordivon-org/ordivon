# OMPC-v0 Fixture D — Finance metric / legibility dogfood

Fixture D consumes existing **Finance-owned** evidence. It performs no live trading, no venue write and no current-account observation.

## Exact source fence

Observed Finance repository revision: `6ed0730ce6f7b067ddb56d806a744e121b987402`.

Primary evidence:

- `evidence/qb6-owner-conditioned-agent-choice-20260812.json`
  - exact file digest `sha256:261887acd11177c43ed9e03f07003e8b586658bd485384fcc0a4910b928590bb`;
- `evidence/qb6-owner-conditioned-agent-followup-20260812.json`
  - exact file digest `sha256:343f541d87e002be407f62d7d53e0dc7530ff9b813d44f94175b37602e732ccd`;
- both were introduced by Finance commit `ac882d94c94700e8558b39003c00cdf41271ca5b`.

Supporting Finance anti-laws:

- `evidence/apf-alpha-production-foundations-20260815.json`;
- exact file digest `sha256:1cc4cef93bceca95cfd4f74268707b79bd33e60e359ebb1bb61cfebe6e9bc717`;
- introduced by `42c92b4ca539c0d0b1b93317bc7b5df8fb6ec34b`.

All introducing commits are ancestors of the observed Finance revision. That ancestry is recovery evidence, not a claim that the historical owner/account state is current now.

## The controlled contrast

QB6 deliberately exposes a case where headline scalar metrics are not enough to determine a capital-transition conclusion.

The same candidate carries these values in both the first and followup packets:

```text
standalone cumulative return       +7.1029%
standalone Sharpe                   1.0162
owner-marginal cumulative delta    +0.7506%
point-in-time alpha annualized     -0.3024%
alpha standing                      descriptive-no-causal-alpha-claim
```

The first Finance choice is:

```text
more_research
```

The followup adds read-only suitability evidence while retaining the same headline performance/attribution metrics:

```text
allowed maximum candidate weight       0.10
minimum-notional equity fraction        0.329071...
within allowed intent weight?           false
qualifying live execution receipts      0
external financial write attempted?     false
```

The Finance followup choice becomes:

```text
no_op
transitionIntent = null
```

Therefore the decision changed while the headline metric surface did not.

## Destructive tests

### D1 — Positive standalone return does not prove novel alpha — PASS

The candidate has positive standalone return and Sharpe, while Finance records it as a known passive/growth exposure and the point-in-time attribution is explicitly `descriptive-no-causal-alpha-claim` with annualized alpha approximately -0.30%.

Retained law:

```text
positive return != novel alpha
```

### D2 — Headline metrics do not determine transition eligibility — PASS

The listed headline metrics are unchanged across QB6 turns, yet the Finance disposition changes from `more_research` to `no_op` after new owner/execution-suitability evidence arrives.

Retained law:

```text
same visible metrics != same domain decision
```

### D3 — Abstract target weight does not prove physical expressibility — PASS

Finance permits at most a 10% candidate weight in the risk-increase intent shape. The fresh read-only suitability evidence reports a minimum-notional equity fraction of about 32.9%, so the abstract permitted weight is not physically expressible under the observed contract granularity.

Retained law:

```text
abstract portfolio intent != physically expressible transition
```

### D4 — Metric-only projection is truthful but materially incomplete — PASS

A card showing only `+7.10%`, `Sharpe 1.02`, and `+0.75% owner-marginal delta` would contain source-grounded numbers. It would still be insufficient for the decision-facing task because it omits the candidate's known-exposure status, no-causal-alpha attribution, research-only standing, minimum-notional infeasibility, and execution-receipt boundary.

This is a Media legibility failure without any false numeric literal.

Retained law:

```text
numerically true projection != semantically sufficient projection
```

### D5 — Finance authority remains external — PASS

Finance itself states that reports, CLI projections, dashboards, Agent summaries and MCP views are disposable projections and do not acquire canonical truth by displaying it. Media therefore owns only the representation/legibility consequence here, not Finance calculation, portfolio, alpha, applicability or transition semantics.

## OMPC consequence

Fixture D adds **Metric / Proxy Non-Collapse** as invariant 11:

```text
visible metric != underlying target truth
favorable scalar metric != decision eligibility
```

A decision-facing metric projection must preserve enough definition, scope, proxy/attribution standing and material omitted context to avoid silently promoting the metric into a stronger domain claim.

No new OMPC semantic role is required. No Finance schema, calculation engine, dashboard authority, Media metric engine or MF10 is admitted.

## A/B/C/D consequence

Fixture D expands OMPC beyond UI/creative/interaction-shaped cases into Finance datafication/legibility. The shared result is now stronger:

- source truth remains external;
- projections select and compress;
- omission can be structural, temporal or contextual;
- identity and metrics cannot substitute for their targets;
- action/decision standing cannot be inferred from presentation.

This further supports OMPC as a shared reference/conformance discipline. It still does not demonstrate duplicated implementation machinery that justifies a shared Media runtime/SDK.
