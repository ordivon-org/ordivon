# Innovation Lens Routing R1

Date: 2026-09-21
Status: ACTIVE METHODOLOGY ROUTER / EXTERNAL LENSES FIRST

## Purpose

This document turns EXTERNAL_INNOVATION_THEORY_CENSUS_R1 into an operational routing surface.

It is not a new theory. It answers:

> Given a problem shape, which mature external lens should Ordivon activate first?

The router is intentionally sparse. Do not activate every lens on every task.

## Routing table

| Trigger / question | Primary mature lens | Typical output | Do not use as |
|---|---|---|---|
| Is the innovation mainly a new arrangement of known components? | Henderson & Clark — Architectural Innovation | component-vs-linkage change map | universal novelty score |
| Where should module boundaries be? | Simon near-decomposability + DSM + Baldwin/Clark Design Rules | coupling/dependency map; candidate module boundaries | proof that a decomposition is correct |
| Is extra modularity worth its cost? | Baldwin/Clark real options | experiment/substitution option analysis | generic more-modules-is-better rule |
| Should we keep searching or exploit the current solution? | March exploration/exploitation | exploration budget / stop condition | one-time architecture chooser |
| Search deeply in known knowledge or broadly across domains? | Katila/Ahuja search depth × scope | explicit search policy | scalar search amount |
| Should search cross organizational or technological boundaries? | Rosenkopf/Nerkar boundary-spanning search | boundary-spanning search plan | guarantee that radical search is better |
| Should we reason from a model first or learn by trials? | Gavetti/Levinthal cognitive vs experiential search | model-guided hypotheses + experience loop | replacement for real evidence |
| Is the solution space constrained by a paradigm/trajectory? | Dosi technological paradigms/trajectories | current trajectory + anomaly/paradigm-shift analysis | flat global search assumption |
| Are interactions making the landscape rugged/local-optimum heavy? | Kauffman NK / fitness landscape | interaction/ruggedness hypothesis | literal mapping of every system to NK |
| Can we actually absorb and use external knowledge? | Cohen/Levinthal absorptive capacity | prior-knowledge gap + assimilation/application plan | mere source discovery |
| Are we combining existing capabilities into new organizational capability? | Kogut/Zander combinative capabilities | capability recombination map | pure technical interface checker |
| How should specialist knowledge be integrated? | Grant knowledge integration | integration/coordination mechanism | claim that knowledge has one global owner |
| Can knowledge/solutions transfer across domains by analogy? | Hargadon/Sutton technology brokering | source-domain -> target-domain analogy candidates | proof of semantic equivalence |
| Is the boundary syntactic, semantic, or pragmatic? | Carlile knowledge boundaries | transfer/translation/transformation plan | schema-only compatibility |
| Should we build internally or leverage external ideas/assets? | Chesbrough open innovation | make/buy/partner/license/external-source options | automatic outsourcing rule |
| What complements are required to realize/capture value? | Teece complementary assets | missing complement map | technical architecture model |
| Must the organization continuously reconfigure capabilities? | Dynamic capabilities | sensing/seizing/reconfiguration loop | static system decomposition |
| Are independent organizations/providers jointly creating value? | Ecosystem/platform theory | complement/dependency/governance map | reason to centralize all owners |
| Need systematic candidate combination generation? | Morphological analysis | function × means candidate matrix | final selection method |
| Need to avoid premature convergence on one design? | Set-Based Concurrent Engineering | surviving candidate sets + elimination evidence | infinite exploration |
| Need to compare many architectures across multiple objectives? | MATE / tradespace exploration | Pareto/tradespace view + sensitivity | single scalar ranking |
| Do component assumptions and guarantees compose? | Assume-Guarantee / contract-based verification | assumptions, guarantees, discharged obligations, counterexamples | semantic/business validation |
| Which states/capabilities are reachable under dynamics/controls? | Reachability / control / formal verification | reachable/invariant sets or bounded state graph | business-value proof |
| How do decomposition, integration, verification and validation connect? | Systems Engineering / V-model | lifecycle architecture + V&V plan | domain-specific science |
| Are we managing reusable families with controlled variation? | Software Product Lines / variability management | commonality/variability model | generic plugin ontology |
| Does AI change which hypotheses/tests should be prioritized? | AI prioritized-search literature | ranking/test-capacity model | proof AI invents fundamentally new science |
| Is AI performance uneven across task boundaries? | Jagged technological frontier | capability-boundary experiment | assumption of uniform productivity gain |

## Dispatch families

### 1. Novelty / architecture

Use Henderson-Clark when the question is component concepts versus component linkages. Use Simon, DSM, and Design Rules when the question is decomposition, coupling, and module boundaries. Do not create an Ordivon relation-novelty lens.

### 2. Search policy

Use March for exploration versus exploitation; Katila-Ahuja for depth versus scope; Rosenkopf-Nerkar for boundary spanning; Gavetti-Levinthal for cognitive versus experiential search; Kauffman for rugged interactions; Dosi for paradigm/trajectory constraints. Do not collapse them into a single search score.

### 3. Knowledge acquisition and integration

Use Absorptive Capacity when external knowledge has been found but cannot yet be recognized, assimilated, or applied. Use Kogut-Zander for capability recombination, Grant for specialist knowledge integration, Hargadon-Sutton for analogy and technology brokering, and Carlile for syntactic/semantic/pragmatic boundaries.

### 4. External ownership and value realization

Use Open Innovation for external/internal sourcing, Complementary Assets for missing complements, Dynamic Capabilities for continual reconfiguration, and Ecosystem/Platform theory for interdependent independent owners. Integration difficulty is not authority to centralize ownership.

### 5. Engineering composition and verification

Use Morphological Analysis to generate bounded combinations, SBCE to retain and prune sets, MATE for multi-objective architecture tradespaces, Assume-Guarantee for contracts, reachability/model checking for dynamic state questions, Systems Engineering for integration/V&V, and Software Product Lines for managed variability.

## Lens stacking rule

Stack lenses only when they answer different questions. Example:

    Architectural Innovation
      -> identifies relation-level change
    Assume-Guarantee
      -> checks compositional contract validity
    Systems Engineering V&V
      -> verifies requirements and validates real outcome

Bad pattern: enable March + Katila/Ahuja + NK + C-K + evolutionary search + MATE merely because the task contains the word search.

## Agent-era extension rule

AI/agents are not a reason to rename mature lenses. Instead test whether agents change parameters inside them:

- search cost;
- experiment cost;
- feasible search scope;
- absorptive capacity;
- semantic-translation cost;
- option value of modularity;
- exploration/exploitation balance;
- testing capacity;
- switching cost;
- the jagged capability frontier.

Only repeated evidence of a phenomenon not representable within mature constructs should justify a new theory object.

## Ordivon ownership boundary

Ordivon may own:

- routing from problem shape to mature lens;
- adapters/tooling that instantiate a lens;
- frozen context/evidence of lens use;
- cross-lens orchestration when multiple distinct questions must be answered;
- prospective tests of whether AI changes parameters or relationships in mature theories.

Ordivon does not own the underlying mature theories.

## Default workflow

1. Problem and natural authority first.
2. Select the smallest mature lens set matching the decision.
3. Run primitive/provider census only after the lens boundary is clear.
4. Generate/search candidates using the appropriate mature method.
5. Apply composition contracts where needed.
6. Execute through Runtime/Host/providers.
7. Verify through independent domain authority.
8. Record transfer/applicability boundaries.

The router is a replaceable projection. If a better external theory-selection framework is found, replace it.
