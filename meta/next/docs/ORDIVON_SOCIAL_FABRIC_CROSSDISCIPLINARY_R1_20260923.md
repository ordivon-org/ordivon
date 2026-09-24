# Ordivon Social Fabric Cross-Disciplinary Recompile R1

Truth role: architecture/research projection. It does not grant execution, scheduling, lease, priority, or domain authority.

Audited current main baseline: `d3345713a0113deb7800ed523e9b503fb78be60a`.

## 1. Current architecture as LEGO

### L0 — Natural-owner substrate
- Host: semantic continuity, checkpoints, durable collaboration.
- Runtime: Workspace/Job/Attempt/process/artifact physical truth.
- Git/main: implementation currentness.
- Harness + OpenTelemetry/W3C Trace Context: tool-call and causal telemetry.
- Gateway: non-authoritative northbound capability/routing projection.
- Domain owners: domain completion and evidence truth.

### L1 — R1 Reality package
`Owner Cut -> SocialSignal -> FactSet -> WorkGraph -> Reconciliation -> Common Operating Picture`.

Current strength: deterministic cuts, owner boundaries, UNKNOWN preservation, exact cross-owner references.

Current gap: the original R1 plan named Transactive Memory and Freshness/Supersession as first-class projections, but the current compiler does not expose them as independent products.

### L2 — R2 Coordination package
CloudEvents 1.0 envelope -> lifecycle -> receptor routing -> damage/modulatory signals -> Candidate/Support/Inhibition -> symmetric shared/exclusive subject conflict.

Current strength: no winner, no vote/score, no fake lease, no mutable social registry.

Current gaps: custom expiry duplicated a CloudEvents extension; logical scope and propagation mode are conflated; receptor matching is intentionally simple; provenance remains mostly opaque refs; coordination is state-heavy rather than flow/rate-aware.

### L3 — R3 Commitment package
R2 candidate standing + explicit role/evidence/blocker predicates -> OPA/Rego -> `NOT_APPLICABLE | NOT_READY | READY_SHADOW | AMBIGUOUS_MULTIPLE_READY`.

Current strength: explainable evidence gate, no hidden count threshold, no tie-break, EffectAuthority always false.

Current terminology gap: biological quorum sensing is population-density signaling, whereas R3 intentionally does not count population/support. Public architecture should prefer **Commitment Gate / Evidence Gate** over “quorum” except when discussing the historical LEGO name.

## 2. External standards and cross-disciplinary mechanisms

| Source | Mechanism | Decision | Ordivon interpretation |
|---|---|---|---|
| CloudEvents 1.0 | core envelope + documented extensions | ADOPT | Keep CloudEvents waist; use standard `expirytime`; use tracing/sequence/severity extensions only when owner facts exist. |
| OpenTelemetry + W3C Trace Context | causal propagation/context | ADOPT | Correlate signals to owner traces; do not make Social Fabric the telemetry owner. |
| W3C PROV | Entity/Activity/Agent, derivation, revision, invalidation/specialization | ADOPT as projection | Compile structured provenance from owner refs/evidence; never mutate original owner records. |
| SBML Level 3 | stable Core + optional Packages | ADAPT architecture pattern | Social Fabric should have a tiny Core and optional Reality/Coordination/Commitment/Regulation/Concurrency/UX packages. |
| SBGN | orthogonal PD/ER/AF views | ADAPT UX pattern | Separate CURRENT, ATTENTION, COORDINATION and AUTHORITY views rather than one giant graph. |
| Cell signaling | contact/local/directed/global signaling; receptor-selective response | ADAPT | Separate propagation mode from semantic scope; consumers declare receptors. |
| Combinatorial receptor signaling | response depends on combinations | ADAPT at policy layer | Keep receptors simple; use OPA Evidence/Commitment Gate for combinatorial requirements instead of a new receptor DSL. |
| Quorum sensing | density/autoinducer-dependent collective behavior | TERMINOLOGY CORRECTION | Do not call evidence-role readiness “quorum” in agent UX; no count/density semantics unless a real domain requires it. |
| DAMP/PAMP + pattern-recognition receptors | endogenous damage vs exogenous pattern sensing | ADAPT cautiously | Permit owner-supplied anomaly origin/class; Social Fabric must not independently invent security/threat classification. |
| Homeostasis/allostasis | regulated variables, feedback and anticipatory regulation | ADAPT projection | Add pressure/regulation views for canonicalization debt, CI pressure, workspace fanout; advisory only, never hidden scheduler. |
| Stigmergy | environmental traces coordinate later actors | ADOPT principle | Git/Runtime/CI/evidence traces are primary machine coordination; Board should not duplicate machine status. |
| Chemistry reaction networks | reactants/resources, catalysts/modifiers, inhibitors, products, rates/flux | ADAPT model | Separate prerequisites/modifiers/blockers/outcomes and add flow/flux projection; keep public names domain-neutral. |
| Chemical potential | thermodynamic driving quantity | METAPHOR_ONLY | Do not invent a Social Fabric scalar without a measurable owner-native quantity. |
| ISO/IEC 15909 Petri nets | formal concurrent/distributed transition semantics | HOLD/ADAPT optional | Add a shadow concurrency-net package only if current same-subject conflict misses real deadlock/resource-pattern cases. Never schedule from it. |
| FEMA/NIMS Common Operating Picture | shared situational awareness | VALIDATES CURRENT | Confirms R1 COP; no new subsystem required. |
| Transactive Memory Systems | “who knows what / who owns what” | ADOPT projection | Add first-class owner/knower/verifier/evidence locator projection. |
| Blackboard systems | cooperative shared problem space | REJECT mutable form | Rebuildable projections are acceptable; no mutable Social Blackboard database. |

## 3. Target architecture

```text
Natural Owners
  Host | Runtime | Git | Harness/OTel | Gateway | CI | Domain Evidence
                              |
                              v
+-------------------------------------------------------------------+
| SOCIAL FABRIC CORE                                                 |
| CloudEvents envelope | OwnerRef | bounded cut | deterministic hash |
| trace/provenance refs | UNKNOWN/conflict preservation              |
+-------------------------------------------------------------------+
   |                 |                  |                 |
   v                 v                  v                 v
Reality Package   Signaling Package   Regulation Pkg   Provenance Pkg
FactSet           lifecycle           pressure         W3C PROV view
WorkGraph         receptor            flux             revision chain
Freshness         scope               regulated vars   evidence lineage
Supersession      propagation mode
Transactive Mem   anomalies
Reconciliation    candidates/modifiers/inhibitors
COP
   |                 |                  |                 |
   +-----------------+------------------+-----------------+
                              |
                              v
                     Commitment Package
                    OPA Commitment/Evidence Gate
          NOT_READY | READY_SHADOW | AMBIGUOUS_MULTIPLE_READY
                              |
                              v
                     Agent UX Projections
             CURRENT | ATTENTION | COORDINATION | AUTHORITY
                              |
                              v
                    Natural Effect Owner Binding
           owner-native admission / lease / effect / receipt
```

### Optional formal package
`Coordination facts -> shadow high-level Petri net -> conflict/deadlock/liveness findings`.
This package is **not admitted into the core** until measured dogfood shows that the present same-subject shared/exclusive law misses important cases.

## 4. Biology-derived signaling law

Current R2 `ordivonscope` mixes two questions:
1. **semantic scope** — what subject/domain the signal belongs to;
2. **propagation mode** — how broadly/indirectly it should be observable.

Target neutral propagation modes:
- `self` — producer-local feedback;
- `direct` — explicit peer/subject handoff;
- `local` — neighborhood/domain-local diffusion;
- `broadcast` — system-wide advisory modulation;
- `environmental` — stigmergic trace discovered from Git/Runtime/CI/evidence.

These are routing/projection semantics, not transports. A2A remains one direct transport; no event broker is implied.

## 5. Chemistry-derived flow law

A snapshot answers **what exists**; a reaction/flow view asks **what is changing and at what rate**.

Add a projection-only `SocialFlux` family such as:
- task creation/terminalization rate;
- workspace creation/closure rate;
- merge/integration rate;
- stale-finding creation/resolution rate;
- evidence invalidation/refresh rate;
- canonicalization debt derivative.

No flux becomes priority automatically. It is a modulatory observation for Agent strategy and human attention.

## 6. Delta matrix

| Delta | Current | Target | Priority |
|---|---|---|---|
| D01 expiry | custom `ordivonexpiresat` | CloudEvents `expirytime` | NOW |
| D02 provenance | opaque `evidenceRefs` | W3C PROV projection + trace refs | HIGH |
| D03 transactive memory | planned, not first-class | owner/knower/verifier/evidence locator | HIGH |
| D04 freshness/supersession | partly lifecycle/local findings | first-class cross-owner projection | HIGH |
| D05 scope/propagation | one `ordivonscope` dimension | semantic scope + propagation mode | MEDIUM |
| D06 flow | state/count snapshots | SocialFlux + pressure derivative | HIGH |
| D07 anomaly origin | damage reason code only | optional owner-supplied endogenous/exogenous/unknown origin | MEDIUM |
| D08 quorum terminology | policy-defined “quorum” | Commitment/Evidence Gate | NOW docs/UX |
| D09 agent UX | R1/R2/R3/CLI plumbing exposed | CURRENT/ATTENTION/COORDINATION/AUTHORITY | HIGH |
| D10 formal concurrency | pairwise same-subject conflict | optional Petri-net shadow analysis | HOLD until measured gap |
| D11 mutable shared space | none | remain none | KEEP |
| D12 effect authority | natural owner | remain natural owner | KEEP |

## 7. Executable LEGO DAG

### Wave A — standards contraction
- **XD00 CurrentArchitectureFreeze**: exact main/source/test/API census.
- **XD01 AuthorityMechanismMatrix**: ADOPT/ADAPT/REJECT/METAPHOR_ONLY evidence matrix.
- **STD10 CloudEventsExpiryMigration**: canonical `expirytime`, legacy-read only, dual-field fail closed.
- **STD11 TraceContextProjection**: bind CloudEvents tracing extension only when owner OTel/W3C context exists.

### Wave B — reality completion
- **REAL20 ProvenanceProjection**: W3C PROV Entity/Activity/Agent/wasDerivedFrom/wasRevisionOf mapping over refs.
- **REAL21 TransactiveMemoryProjection**: owner/knower/verifier/evidence locator.
- **REAL22 FreshnessSupersessionProjection**: current/historical/superseded/stale/unknown across owner cuts.

### Wave C — signaling recompile
- **SIG30 PropagationModeSeparation**: split semantic scope from propagation mode; preserve backward read compatibility.
- **SIG31 ReceptorBoundary**: keep receptor as deterministic interest matcher; combinatorial readiness stays OPA-owned.
- **SIG32 AnomalyOriginProjection**: owner-supplied endogenous/exogenous/unknown, no Social Fabric threat inference.

### Wave D — regulation and chemistry-inspired flow
- **FLOW40 SocialFluxProjection**: event-rate/closure-rate/invalidation-rate deltas from bounded cuts.
- **FLOW41 RegulatedVariableProjection**: canonicalization debt, workspace fanout, CI/backlog pressure with source formulas.
- **FLOW42 AllostaticAdvisory**: forecast/advisory only; no scheduler or priority mutation.

### Wave E — Agent UX
- **UX50 CurrentView**
- **UX51 AttentionView**
- **UX52 CoordinationView**
- **UX53 AuthorityView**
- **UX54 SocialPreflight**: auto-run only for durable/shared/effectful/scarce work; cheap local reads bypass it.
- **UX55 ProgressiveDisclosure**: concise default with drill-down refs.

### Wave F — optional formal concurrency
- **CONC60 GapMeasurement**: collect missed-conflict/deadlock examples that pairwise model cannot express.
- **CONC61 PetriNetShadow**: only PROMOTE if CONC60 proves need; ISO/IEC 15909-style formal projection, never execution.

### Wave G — dogfood and promotion
- **DOG70 OrdivonCanonicalizationDogfood**: stale Task/successor/workspace/main reconciliation.
- **DOG71 WSLMaintenanceDogfood**: exclusive maintenance collision and owner-native effect boundary.
- **DOG72 PaperDogfood**: reviewer/evidence/readiness/transactive memory.
- **DOG73 CapitalDogfood**: advisory/readiness vs EffectAuthority boundary.
- **GATE79 PromoteHoldKill**: measured outcome, owner-boundary, UX and duplicate-owner gates.

## 8. Stop rules
1. No new Social Fabric daemon/database/broker.
2. No new policy language; use OPA/Rego where policy is needed.
3. No Social Fabric resource lease, scheduler, winner selector or EffectAuthority.
4. No biology/chemistry term becomes public API merely because the analogy is attractive.
5. No numeric pressure/flux metric can silently become priority.
6. No Petri-net package until a measured pairwise-conflict gap exists.
7. Historical evidence is immutable; migrations add compatibility or successor evidence rather than rewriting history.
8. Gateway exposure waits until Agent UX projections are proven locally.

## 9. Immediate execution order
`XD00 -> XD01 -> STD10 -> REAL20/REAL21/REAL22 -> FLOW40 -> UX50..UX55 -> dogfood -> optional CONC60`.

The architecture is therefore not “R4 adds more social machinery”. It is a **recompile**: contract custom semantics into standards, complete missing R1 reality projections, add rate/flow observability, and expose orthogonal Agent views while preserving the natural-owner effect boundary.
