# Ordivon Social Fabric Cross-Disciplinary Recompile R2

Truth role: architecture/research projection. No execution, scheduling, lease, priority, owner standing, or domain authority.

Audited implementation baseline: `354d885d411de5acbb360df2694aa95e310715bc` (successor to R1 baseline `832468936934e03aa2b8f67836182a8543b124a6`). R1 remains immutable historical architecture evidence.

## 1. Architectural law

`Natural Owners -> rebuildable Social Fabric projections -> Agent UX -> Natural Effect Owner`.

Social Fabric owns no mutable world truth. Core owns only OwnerRef, bounded cuts, deterministic hashing, UNKNOWN/conflict preservation and a thin CloudEvents-shaped observation waist.

Target packages:
- Reality: FactSet, WorkGraph, Freshness/Supersession, Transactive Memory, Reconciliation, COP.
- Signaling: lifecycle, deterministic receptor, semantic scope, propagation mode, compartment/context.
- Coordination: Candidate, Support, Inhibition, optional owner-supplied anomaly origin.
- Regulation: dimensional SocialFlux, owner-backed regulated variables, shadow attention adaptation.
- Provenance adapter: reuse W3C PROV/OpenLineage/OTel owners.
- Commitment: OPA Commitment/Evidence Gate.
- Verification bridge: sequence vs mechanism standing.
- Agent UX: CURRENT / ATTENTION / COORDINATION / AUTHORITY.

## 2. Current implementation

R1 Reality is deterministic and bounded but lacks first-class Transactive Memory and Freshness/Supersession products. R2 Coordination has lifecycle/receptors/damage/modulation/Candidate-Support-Inhibition, but `ordivonscope` mixes semantic scope and propagation. R3 Commitment is OPA-backed and correctly never grants EffectAuthority. Cross-Disciplinary R1 already implemented the CloudEvents `expirytime` migration with legacy-read compatibility and dual-field fail-closed behavior.

## 3. Standards contraction

- CloudEvents core is the event-description waist. Its documented extensions are optional and explicitly have weaker standing than versioned core. Pin extension semantics/currentness and keep extension metadata minimal; data not required for routing/processing belongs in `data`.
- OpenTelemetry/W3C Trace Context remains the correlation/telemetry owner. A SocialSignal is a social observation projection, not a second OTel event catalog; duration belongs to spans and operation-wide properties to attributes.
- W3C PROV-O is already a repository owner for semantic derivation. REAL20 is an adapter/projection, never a new Social provenance ontology.
- OPA/Rego remains policy decision, not enforcement.
- A2A current released specification is 1.0.0. It remains direct agent interoperability/task exchange, not Social Fabric shared truth.
- MCP remains the northbound capability protocol; Social Fabric adds no hidden session state.
- ISO/IEC 15909-1:2019 and -3:2021 are optional formal concurrency references; promotion requires measured conflict/deadlock gaps.

## 4. Systems-biology architecture patterns

- SBML Level 3 validates a small Core plus optional packages. `comp` supports hierarchical reuse; `qual` validates qualitative/categorical standing without fake numerical physics; `fbc` suggests explicit feasibility constraints rather than rankings; `spatial` reinforces explicit locality.
- SBGN uses orthogonal Process Description, Entity Relationship, and Activity Flow projections. Ordivon should likewise avoid one giant social graph.
- CellML 2.0 formalizes components, connections, encapsulation, imports and units. Ordivon should separate component visibility/context from transport and require dimensions on rate-like projections.

## 5. Biology-derived LEGO

### BIO10 Receptor selectivity — ADOPT
Producer emits semantics; consumer interest is receptor-defined. Complex readiness remains OPA-owned rather than a receptor DSL.

### BIO11 Scope / propagation / compartment — ADD
Separate: (a) semantic subject/domain, (b) propagation mode `self|direct|local|broadcast|environmental`, and (c) compartment/context derived from existing Goal/Task/domain/workspace refs. No registry.

### BIO12 Scaffold specificity — ADAPT
Biological scaffold/compartment organization limits cross-talk. Route within the smallest justified compartment first; broaden only when propagation semantics demand it.

### BIO13 Damage origin — HOLD FOR OWNER FACTS
Allow `endogenous|exogenous|unknown` only when natural owner supplies classification. Social Fabric cannot infer security/threat meaning.

### BIO14 Attention adaptation/refractory — MEASURE THEN PROTOTYPE
Persistent unchanged stimulation should not consume unbounded attention. Projection-only adaptation/hysteresis may reduce repeat salience, but new evidence, increased severity or changed subject standing must pierce adaptation. Never delete history.

### BIO15 Quorum terminology — CORRECT
Biological quorum sensing depends on population/density/autoinducer concentration. R3 uses evidence-role predicates, so public wording is Commitment/Evidence Gate, never population voting.

## 6. Chemistry-derived LEGO

### CHEM20 State vs flux — IMPLEMENT
Kinetics is dimensional change over time. SocialFlux requires exact start/end timestamps, explicit numerator unit, time denominator, source refs and coverage standing. No dimensionless pressure score.

### CHEM21 Catalyst/modifier vs inhibitor/blocker — DESIGN
Catalysts and inhibitors are not one signed variable. Future coordination projection should distinguish prerequisites, accelerators/modifiers, blockers/inhibitors and outcomes without exposing chemistry jargon in Agent UX.

### CHEM22 Phase/owner bridge — KEEP EXISTING LAW
Gateway/A2A/adapters move references/requests across owner boundaries but do not transfer truth authority.

### CHEM23 Mechanism epistemic boundary — ADD TO VERIFICATION
A sequence is not automatically a mechanism. Use `SEQUENCE_OBSERVED | MECHANISM_HYPOTHESIS | MECHANISM_EVIDENCE_SUPPORTED`; causal owners/evidence remain external.

### CHEM24 Autocatalytic cascade — HOLD
Measure trigger -> duplicate work/alert -> more trigger loops first. No detector without real recurrence evidence.

### CHEM25 Equilibrium warning — KEEP AS TERMINOLOGY GUARD
Do not use equilibrium as synonym for completion/convergence without measured forward/reverse flows.

## 7. Delta matrix

| ID | Current | Target | Disposition |
|---|---|---|---|
| D01 | custom expiry | documented `expirytime` + legacy read | DONE |
| D02 | opaque evidence refs | existing W3C PROV projection | ADAPTER DESIGN |
| D03 | TMS planned | Authority/Capability/Host/evidence locator | DESIGN BY REUSE |
| D04 | scattered currentness | first-class freshness/supersession | DESIGN BY REUSE |
| D05 | scope conflates propagation | semantic scope + propagation + compartment | DESIGN |
| D06/D18 | snapshots only | dimensional SocialFlux | IMPLEMENT NOW |
| D07 | generic damage | owner-supplied anomaly origin | HOLD |
| D08 | historical “quorum” | Commitment/Evidence Gate | CONTRACT |
| D09 | R1/R2/R3 plumbing UX | four orthogonal Agent views | HIGH |
| D10 | pairwise conflict | optional Petri shadow | MEASURE FIRST |
| D13 | CE extension maturity blurred | pinned optional-extension boundary | DOC/AUTHORITY |
| D14 | old A2A refs may remain | A2A 1.0.0 currentness | AUDIT |
| D15 | SocialSignal/telemetry overlap risk | explicit observation-vs-telemetry boundary | CONTRACT |
| D16 | no compartment model | projection-only compartment/context | DESIGN |
| D17 | repeat warnings equally salient | adaptation/hysteresis | MEASURE FIRST |
| D19 | score temptation | OPA constraint feasibility | KEEP |
| D20 | visibility implicit | compartment/component visibility | DESIGN UX |
| D21 | sequence may be over-read | mechanism standing | VERIFICATION BRIDGE |
| D22 | no runaway-loop model | autocatalytic cascade measure | HOLD |
| D23 | bridges may look authoritative | bridge-does-not-transfer-truth invariant | KEEP |

## 8. Executable DAG

Wave 0: XD02 external currentness -> XD03 extension maturity.
Wave 1: FLOW40 dimensional flux -> FLOW41 regulated variables -> FLOW42 allostatic advisory (HOLD until measured).
Wave 2: REAL20 PROV adapter + REAL21 Transactive Memory + REAL22 Freshness/Supersession.
Wave 3: SIG30 propagation separation + SIG31 compartment + SIG32 receptor regression + SIG33 anomaly origin + SIG34 attention adaptation measurement.
Wave 4: EPI40 mechanism-standing bridge + EPI41 OPA feasibility terminology/regression.
Wave 5: UX50 CURRENT + UX51 ATTENTION + UX52 COORDINATION + UX53 AUTHORITY + UX54 progressive disclosure + UX55 social preflight + UX56 visibility filters.
Wave 6: CONC60 conflict-gap measurement + CASCADE61 self-amplification measurement; Petri/cascade implementations stay HOLD until gates pass.
Wave 7: DOG70 canonicalization + DOG71 WSL/VHD + DOG72 Papers + DOG73 Capital -> GATE79 PROMOTE/HOLD/KILL.

## 9. Stop rules

1. No Social database/daemon/broker/scheduler/lease/winner selector.
2. No duplicate PROV, trace, currentness, authority or policy owner.
3. No dimensionless pressure scalar by default.
4. No cross-disciplinary analogy without a testable invariant.
5. No biology/chemistry jargon in public Agent API merely for elegance.
6. Adaptation cannot hide severity escalation or new evidence.
7. Sequence alone cannot establish mechanism/causality.
8. Petri/cascade packages require measured failures first.
9. Historical evidence is immutable.
10. Gateway exposure waits for local Agent UX dogfood.
