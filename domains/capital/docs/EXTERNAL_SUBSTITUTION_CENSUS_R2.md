# Market Capital External Substitution Census R2

## Rule

Market Capital does not own a mechanism merely because it can implement it.

Migration loop: decompose -> identify natural external owner -> qualify owner -> replace local mechanism -> retain only cross-owner authority/evidence/reconciliation seam -> falsify.

No new Ordivon Lens, optimizer, research framework, data platform, OMS, reconciliation engine, or accounting engine is introduced when a mature owner exists.

## Current decisions

| LEGO | Mature owner | Decision |
|---|---|---|
| Owner objectives / constraints / mandate | CFA investment-policy-statement process | Use as the semantic template for the future owner mandate / capital constitution. Keep only an Ordivon binding to authority identities. |
| Public/research financial data integration | OpenBB ODP | Preferred candidate for broad standardized research-data access. Do not use it as private account/order/execution truth. Keep it outside the Market core dependency graph until AGPL/deployment boundaries are explicitly accepted. |
| Quant research workflow | Microsoft Qlib + RD-Agent | Run as a separate research capability. Do not reproduce workflow/model/strategy/executor abstractions in Market Capital. |
| Conventional portfolio optimization | PyPortfolioOpt | Preferred first owner when autonomous portfolio construction is instantiated. |
| Advanced portfolio risk/optimization | Riskfolio-Lib | Optional advanced owner; do not pull its large dependency surface into core merely to replace simple descriptive arithmetic. |
| Agent investment-office organization | TradingAgents + ai-hedge-fund | Architecture/reference inputs for analyst/research/CIO/risk role decomposition and mandate-driven cycles. They do not receive policy or venue authority. |
| Risk/policy decisions | OPA | Retain. Python supplies facts and fails closed. |
| Trading engine / live execution | LEAN where already qualified; NautilusTrader as challenger | Do not grant owner status until the exact latest-language contract passes locally. |
| Live execution reconciliation | NautilusTrader challenger + venue reports | No current Nautilus version passes all gates; retain the bounded local baseline and re-run the same fault/risk/recovery matrix for future candidates. |
| Accounting conservation / pending-post-void mechanics | TigerBeetle | Retain. |
| Provider truth | OKX/Binance official/native APIs | Retain as authoritative external reality. |
| Model estimation / validation primitives | NumPy/SciPy/scikit-learn | Retain as library owners. Do not wrap them in a new local statistics framework. |
| Model governance | Federal Reserve SR 26-2, used proportionately as reference | Retain inventory/validation/monitoring boundaries; no compliance claim. |
| Risk-data architecture | BCBS 239 principles, used proportionately as reference | Retain source identity, accuracy, completeness, timeliness and reconciliation expectations; no bank compliance claim. |

## What remains legitimately Ordivon-owned

Only seams that span owners and therefore have no single natural external owner:

1. exact evidence/authority bindings across provider, model, policy, execution and accounting;
2. owner-principal mandate binding;
3. fail-closed capability attenuation and admission;
4. cross-system reconciliation outcome to capital-accounting resolution;
5. durable operation identity and recovery continuity;
6. explicit qualification evidence proving that an external owner is fit for the admitted use.

Everything else is a candidate for deletion, externalization, or reduction.

## Immediate code consequences

### portfolio_risk.py

Keep observed-exposure normalization specific to canonical evidence, thin calls into mature estimators, and evidence rendering needed by policy/model-governance boundaries.

Do not add asset allocation algorithms, covariance-estimator families, optimizer implementations, risk-parity, Black-Litterman, CVaR optimization, or custom scoring/ranking frameworks. Those belong to PyPortfolioOpt/Riskfolio-Lib or later qualified owners.

### portfolio_counterfactuals.py

Keep temporarily as a deterministic read-only projection seam for explicit candidate actions. It must not evolve into an optimizer, recommendation engine, ranking engine, or autonomous sizing system. When a portfolio-construction owner is admitted, candidate generation/sizing moves outward and this module should shrink to evidence projection plus OPA fact binding.

### execution_reconciliation.py

This file remains the bounded current execution-state reconciliation baseline. NautilusTrader exposes broader startup/continuous reconciliation machinery, but no current version is admitted under all Ordivon gates. Do not broaden the local file; do not delete it until a latest-language stable candidate wins the same contract.

Target local responsibility: qualified reconciliation result -> fail-closed accounting reservation resolution + evidence.

Any local order-lifecycle reconstruction duplicated by the admitted execution engine is migration debt.

### private_reality.py

Retain only where independent read-only venue observation is materially useful as an authority boundary or cross-check. Do not force OpenBB into private-account/execution truth and do not replace venue-native authoritative APIs with a research-data abstraction.

## Integration topology

External owners should normally remain separately versioned capabilities or services where dependency, license or authority boundaries differ.

- OpenBB: research-data capability boundary;
- Qlib/RD-Agent: research-R&D capability boundary;
- PyPortfolioOpt: lightweight in-process portfolio-construction candidate;
- Riskfolio-Lib: optional advanced optimization capability;
- LEAN: admitted bounded historical execution capability; NautilusTrader: execution-engine challenger pending current qualification;
- OPA: policy decision point;
- TigerBeetle: accounting substrate.

The monorepo may hold bindings, configs and qualification evidence without collapsing these owners into one Python environment.
