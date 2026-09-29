# AI Infrastructure Constraint Graph R1

Date: 2026-09-29  
Standing: **RESEARCH MODEL — CURRENT FRONTIER PROJECTION, NOT PROVIDER TRUTH, NOT INVESTMENT AUTHORITY**

## Purpose

This is the first consumer-first implementation of the Recursive LEGO R2.1 representation for the AI-capital physical bottleneck problem. It does not create a new Capital domain, a universal infrastructure ontology, a state tag, a portfolio recommendation, or execution authority.

The frozen R1 chain is deliberately small:

```text
accelerator logic
→ HBM
→ advanced packaging
→ AI-ready data-center IT
→ electricity generation
→ transformer / switchgear
→ grid interconnection / transmission
```

The research question is: **which required complement is currently the evidence-supported minimal bottleneck frontier, how much can AI/automation increase effective capacity without building new physical stock, and where can the frontier migrate when one constraint relaxes?**

## Representation contract

The graph keeps separate:

- technology capability;
- technology readiness (TRL) for a specific technology;
- manufacturing readiness (MRL) for a specific production process;
- installed stock;
- annual flow/ramp;
- utilization/backlog;
- qualification and lead time;
- effective-capacity improvement from software/AI;
- demand growth and rebound;
- jurisdiction-specific evidence;
- Capital interpretation.

A portfolio layer such as `HBM` or `electricity-generation` never receives one synthetic TRL/MRL. Readiness numbers belong to a specific device/process/project.

## External natural owners

The method reuses mature external references rather than reimplementing them:

- ISO/IEC/IEEE 15288: system life-cycle and recursive system-element processes;
- NASA TRL: technology-specific readiness;
- GAO/MRL: manufacturing maturity from laboratory/pilot to full-rate production;
- ISO 22400: manufacturing operations KPIs;
- ISO 23247: manufacturing digital twin/digital thread/composition;
- NIST 2026 AI/ML Smart Manufacturing roadmap: AI-enabled sensing, autonomous systems, digital twins, robotics, logistics and remaining industrial barriers;
- IEA Energy and AI: data-center electricity scenarios and energy-system timing mismatch;
- Berkeley Lab Queued Up: U.S. generator/storage interconnection queue evidence.

## Current frontier, 2026-09-29

### United States / U.S.-led AI ecosystem

Current R1 frontier:

1. **transformer-switchgear** — current evidence includes high-voltage transformer lead times reported up to 160 weeks and multi-year advance procurement;
2. **grid-interconnection-transmission** — >2,060 GW of generation+storage remained in U.S. interconnection queues at end-2025, while Berkeley Lab reports long timelines and high withdrawals.

HBM, advanced packaging, AI-ready facilities and locally firm generation remain candidate constraints, but R1 does not promote them above the two current-frontier nodes without stronger evidence.

### China

Current R1 frontier:

1. **accelerator-logic** — model-based evidence shows domestic frontier-equivalent compute flow remains much smaller than Nvidia's global output;
2. **HBM** — direct reporting shows HBM scarcity and export restrictions affecting Chinese accelerator pricing; domestic-HBM-supported frontier output remains limited in model estimates.

Advanced packaging is intentionally **CANDIDATE/UNKNOWN** in this R1. Global packaging tightness is well evidenced, but the present evidence set does not contain a strong enough China-specific capacity/backlog series to call it an independent current frontier.

Data-center shell, national generation, transformer production and national transmission are not current national frontiers under the evidence used here. This does not claim that every Chinese AI site has adequate power, cooling or local interconnection.

## Four clocks

The graph uses four feedback clocks:

1. `COGNITION_SEARCH` — software/search/design loops;
2. `VERIFICATION_QUALIFICATION` — real validation, reliability and customer qualification;
3. `MANUFACTURING_RAMP` — factories, yield and production throughput;
4. `INFRASTRUCTURE_INSTITUTION` — construction, site, grid, permitting and rights-of-way.

AI tends to have the strongest direct leverage on the first clock, meaningful but bounded leverage on the second and third, and the weakest ability to compress the fourth. Software can nevertheless increase **effective** physical capacity: DOE dynamic-line-rating research, for example, shows roughly 10–40% transfer-capability uplift in suitable conditions without building a new line. That is an efficiency gain, not removal of physical or reliability limits.

## No overall bottleneck score

R1 explicitly forbids an aggregate 0–100 health score. A surplus in accelerator supply cannot cancel a transformer deficit. The only admitted quantitative headroom formula is:

`headroom = capacity / requirement - 1`

and only when capacity and requirement have the same unit, scope and time basis. Otherwise the graph preserves qualitative/UNKNOWN headroom and the underlying observations.

## Demand / efficiency bridge

For useful work:

`effective compute requirement multiplier = demand multiplier / algorithmic-efficiency multiplier`.

Two illustrative counterfactuals are frozen in the config:

- demand 2×, efficiency 3× → compute requirement ~0.67×;
- demand 10×, efficiency 3× → compute requirement ~3.33×.

These are arithmetic counterfactuals, not forecasts. They exist to make rebound explicit rather than silently assuming efficiency lowers total physical demand.

## Capital boundary

The graph is upstream research evidence. It may later support explicit, time-bounded Capital evidence claims after a real producer/validation contract exists. It must **not** directly mutate `decision_state_claim_registry.json`, infer owner risk appetite, rank securities, or authorize an external financial effect.

The existing Capital R2 chain remains the consumer boundary:

```text
explicit evidence claim
→ state projection
→ model atlas / risk-budget boundary
→ decision support
→ frozen decision record
→ later outcome measurement
```

## Next evidence frontier

The next highest-value work is not adding more nodes. It is replacing qualitative headroom with same-unit measurements where possible:

- accelerator delivered compute versus deployable demand;
- HBM qualified GB/TB bandwidth supply versus accelerator BOM demand;
- China-specific 2.5D/3D packaging capacity/backlog/yield;
- energized high-density AI IT MW versus contracted/installed accelerator MW;
- site-level firm power and electrical-equipment lead times;
- interconnection completion time rather than queue MW alone.

Only after those producer contracts are stable should the graph emit canonical Capital state claims.
