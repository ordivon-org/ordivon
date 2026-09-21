# External Implementation Comparative Qualification R1

## Purpose

This is a make-vs-adopt qualification rule, not a new Ordivon framework.

An external project is not better because it is older, popular, highly starred, or feature rich. Those facts may justify evaluation; they do not justify substitution.

The comparison unit is one exact LEGO contract.

Examples:

- order sizing, not LEAN;
- execution reconciliation, not NautilusTrader;
- portfolio optimization, not Riskfolio-Lib;
- public research-data normalization, not OpenBB.

A project may win one contract and lose another.

## Baseline

Every replaceable external candidate is compared against the smallest credible local baseline that satisfies the same contract.

Because Ordivon can use multiple coding Agents in parallel, local implementation cost must be measured under the actual Ordivon development model. Claims that a mechanism would take a conventional team months are not accepted as evidence when a bounded local implementation can be produced and falsified quickly.

The local baseline should preferentially compose mature primitives rather than reimplement them. For example, a local expected-shortfall calculation built from NumPy is not treated as from-scratch numerical software.

## Hard gates

An external candidate cannot substitute for the local baseline when any required hard gate fails.

### 1. Semantic and authority fit

The candidate must satisfy the exact admitted contract without weakening it.

Examples:

- do not weaken an At-the-Opening requirement to DAY merely because a candidate lacks support;
- do not replace authoritative venue/account truth with a research-data abstraction;
- do not allow a trading engine to mint Owner or policy authority.

### 2. Functional correctness

Use the same golden fixtures, property tests, differential tests, edge cases and failure cases against both implementations.

For financial stateful components, include ambiguous outcomes, duplicate/reordered events, partial fills, reconnects, restarts and recovery.

### 3. License and governance acceptability

License, redistribution/deployment obligations, project governance and dependency implications must fit the intended deployment. Popularity does not override an incompatible license or governance boundary.

### 4. Security and software-supply-chain acceptability

Use current external evidence where applicable:

- OpenSSF Scorecard checks as security-posture evidence;
- SLSA provenance/source/build evidence where available;
- vulnerability and dependency review;
- release-signing/provenance evidence.

These are security signals, not proof of functional superiority.

## Comparative quality evidence

After hard gates pass, compare quality under the ISO/IEC 25010:2023 product-quality vocabulary where relevant:

- functional suitability;
- performance efficiency;
- compatibility;
- interaction capability when humans operate the component;
- reliability;
- security;
- maintainability;
- flexibility;
- safety where financial effects make fail-safe behavior material.

Only relevant characteristics need measurements; do not create a decorative scorecard.

Typical evidence:

| Property | Evidence |
|---|---|
| correctness | differential/golden/property tests |
| coverage | admitted contract + edge-case matrix |
| reliability | fault injection, restart/recovery, soak runs |
| performance | latency/throughput/resource benchmark |
| interoperability | provider/version/platform matrix |
| maintainability | local glue LOC, API churn, upgrade diff, test burden |
| security | Scorecard/SLSA/vulnerability/dependency evidence |
| operability | observability, diagnostics, recovery controls |
| replaceability | ability to isolate/upgrade/remove the dependency |

## Maintenance and community evidence

CHAOSS-style project-health signals such as activity, responsiveness, contributor concentration and release continuity may estimate future maintenance risk.

Star count is discovery evidence only.

A project with 100k stars can lose to a 100-line local implementation if the local implementation has a smaller trusted computing base, exact semantics, lower maintenance cost and sufficient test coverage.

Conversely, a large mature engine can beat a short local implementation when its advantage lies in difficult state-space coverage, recovery behavior, provider compatibility, battle-tested edge cases or continuing upstream maintenance.

## Reimplementation economics

Record at least:

- local implementation size;
- number and complexity of external dependencies;
- Agent effort to produce the baseline;
- Agent effort to integrate the external candidate;
- expected upgrade/migration burden;
- external API/version churn;
- amount of local adapter/glue retained;
- tests and operational evidence required for each.

Elapsed project age is not counted as value by itself.

## Decision rule

Do not calculate one synthetic total score.

1. Hard gates must pass.
2. Both implementations must satisfy the same semantic contract.
3. Material disadvantages must be explicit.
4. Substitution occurs only when the external candidate shows a concrete net advantage relevant to the admitted use.
5. If the evidence is approximately tied, prefer the smaller trusted and operational surface.
6. If the local implementation is simple, stable, well-tested and built directly from mature primitives, retaining it is valid.
7. Re-run qualification when the contract or a material candidate version changes.

## Current Ordivon Capital implications

### Already supported by comparative/local qualification evidence for bounded contracts

- LEAN: buying-power/order-sizing and bounded historical execution contracts already have local acceptance evidence.
- NautilusTrader: historical rc4 crypto OMS/Risk/shadow evidence is retained, but no current version is admitted as the canonical owner. Current-version qualification must pass the latest-language gate and the same executable risk/effect contract.
- OPA: policy decision ownership is locally tested and application code fails closed around it.
- TigerBeetle: bounded reservation/post/void and restart identity mechanics have local smoke/acceptance evidence.

This does not mean the entire projects are globally superior.

### Candidates that are not yet substitution-qualified

- OpenBB for broad research-data integration;
- Qlib/RD-Agent for autonomous quantitative R&D;
- PyPortfolioOpt for future portfolio construction;
- Riskfolio-Lib for future advanced portfolio optimization;
- TradingAgents and ai-hedge-fund for investment-office organization.

They remain candidates/reference implementations until a real local contract exists and a differential qualification is run.

### Local implementations that should not be removed merely because a larger library exists

- simple NumPy-based descriptive expected shortfall;
- deterministic read-only counterfactual projection;
- thin provider/evidence normalization where it preserves an independent authority boundary.

Their replacement requires evidence of net benefit, not repository popularity.

## Latest-stable language gate

Language freshness is a hard admission gate, not a quality bonus.

As of 2026-09-21 the Ordivon Capital baseline is:

- Python 3.14.7;
- Rust 1.98.1.

Only the latest stable release counts for the canonical production/research baseline. Beta, nightly and pre-release language toolchains belong to experimental lanes and do not satisfy this gate.

An external candidate is rejected from the adopted set when it requires an older language runtime, lacks support for the current latest stable language version, or has not passed local executable qualification on that version.

Historical evidence collected on an older language runtime remains historical evidence only. It cannot authorize substitution under the current baseline.

If Ordivon ports an external project to the latest language version itself, that port is evaluated as a local implementation/fork. The unmodified upstream project does not receive external-owner status merely because the port exists.
