# Model Foundry R1 → R2 Convergence Receipt

Date: 2026-09-27
Status: **CANONICAL KNOWLEDGE-SLICE MIGRATION; NO MODEL RUNTIME / PLANNER DEPLOYMENT**

## Current source truth

The integration workspace was opened from current local `main` at `2bc46824d986c842375759ff39c731ee79195c5b` with a clean source state. The historical Model Foundry line remains at `eb9755d7a282d8158fd0c714885a7ab17ce9975c` and contained 55 files under `docs/research/model-foundry/` at census time.

The historical branch had diverged materially from current main; it is therefore treated as provenance/knowledge input, not merged wholesale.

## Owner decision

`packages/composition` is **not** the owner of Model Foundry discovery/selection knowledge. Its current contract explicitly excludes provider catalogs and ranking/planning. `catalogs/knowledge` is the correct current Structure R2 location for reusable, non-authoritative model/composition mappings.

No root model registry, provider registry, workflow engine, scheduler, planner service, permission system or new authority is introduced.

## R1 disposition

### KEEP as principles
- DELETE-CUSTOM-BY-DEFAULT;
- workload-first composition;
- hardware/serving as architecture variables;
- evidence-bound claims;
- `generate != judge != verify != authorize != execute`;
- composition is not automatically beneficial.

### MIGRATE / NORMALIZE
- Model LEGO → Cognitive Operator + Logical Architecture + physical/provider realization;
- Resource LEGO → Qualification Envelope resource/measurement regime;
- compatibility map → semantic / representation / training / physical / evidence-transfer dimensions;
- provider selection matrix → non-authoritative discovery mapping;
- decision-model lineage → replaceable `DECIDE` physical plans;
- shared-state research → typed state/memory carrier contracts.

### REPLACE
- bare benchmark rankings → bounded benchmark observations / Qualification Envelopes;
- assumed multi-provider failure diversity → measured item-level error diversity;
- generic `memory` → typed state placement;
- one `router` concept → cognitive route / plan selection / runtime dispatch;
- one `composition` concept → parameter / neural-graph / system composition planes.

### DO NOT MIGRATE AS CURRENT TRUTH
- old branch topology;
- stale provider standings;
- training campaigns as default next action;
- unqualified superiority claims;
- any implication that a model output owns authorization, effect, evidence or domain truth.

## Integrated slice

Current main receives only:
- the R2 knowledge boundary/ontology;
- two reusable JSON Schema contracts for operator records and qualification envelopes;
- a small decision-provider discovery catalog;
- bounded benchmark observations demonstrating task reversals and calibration effects;
- repository tests that enforce key non-collapse invariants.

Physical-plan optimizers, routing algorithms and experimental prototypes remain out of canonical source until a concrete consumer earns an owner boundary.
