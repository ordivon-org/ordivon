# Ordivon Capital Domain Taxonomy R1

Standing: `ACTIVE_SOURCE_OWNER_TAXONOMY`

Ordivon Capital is the umbrella, not a synonym for market data or trading. The active source tree is decomposed by responsibility:

| Domain | Owns | Does not own |
|---|---|---|
| Markets | public market/reference facts, microstructure, public streaming, market-transport qualification | orders, account effects, portfolio decisions |
| Trading | provider/private reality, order intent, FIX projection, execution feasibility, execution reconciliation | portfolio optimization, durable accounting |
| Portfolio | explicit caller-supplied portfolio counterfactual projection | autonomous ranking, execution |
| Risk | exposure, dependence/factor statistics, expected shortfall, risk-budget measurement | mandate authority, order routing |
| Research | model monitoring, prospective validation, evidence persistence, standards inventory | execution authority |
| Governance | execution/live-test/risk-budget/pre-trade policy gates | provider truth, market data |
| Accounting | durable reservation/post/void/idempotency and ledger bindings | market truth, execution routing |

The dependency direction is intentional. In particular, Markets must not depend on Trading, Portfolio, Risk, Research, Governance, or Accounting. Binance USD-M symbol/reference normalization therefore lives in `markets/binance_usdm_reference.py`; Trading provider qualification may consume that market/reference contract, but public market capture does not depend on Trading.

## External vocabulary basis

This split follows established industry vocabulary rather than introducing an Ordivon-specific finance ontology:

- FIX Trading Community separates Market Data from Trade (orders/executions) and Post-Trade business areas.
- CFA Institute distinguishes investment research/portfolio management, trading, risk management, and accounting as separate investment-industry functions.
- OpenGamma Strata separates market data from trade/position product models and risk calculations.

These are semantic references, not compliance or certification claims.

## Execution

`Execution` is a capability under Trading:

`Capital -> Trading -> Execution`

Trading also contains order lifecycle, provider effect boundaries, FIX projection and reconciliation. Therefore `Trading` is the name for the component that “管交易”; `Execution` is the narrower mechanism that routes and realizes an order.

## Compatibility boundary

The Python package `ordivon_capital.market` is retired with no compatibility shim.

This source-owner migration does **not** silently rewrite protocol/evidence identities. Existing `ordivon.capital.market.*` JSON kinds are versioned contract identifiers embedded in schemas, configs and frozen evidence. They were migrated through the explicit v2 registry; current runtime code emits and requires domain-correct v2 identities, while v1 replay uses historical source identity rather than a compatibility shim. Likewise the deployed `ordivon_market_capital_*` Prometheus family and historical `Market Capital` evidence/fixture names remain registered compatibility/provenance identities.
