# Veilwild R1 — Independent Multi-Agent Execution Protocol

Date: 2026-09-07
Status: `PRE-RUN_CANDIDATE`
Topology source: `ACTIVATED_E2E_SUBGRAPH_R1.json`

## 1. Core law

```text
AgentPopulation is an execution topology.
E2EGraph is a product/capability topology.
They are related but not identical.
```

The opening production campaign currently proposes 25 logical Agent roles over 27 execution fronts and 46 active E2E closures.

## 2. Independence rule before first verdict freeze

Every A01–A25 Agent receives the same campaign baseline and its own role card.

Before freezing its first verdict, an Agent may read:

- the common source baseline and current repository state;
- `GAME_CAPABILITY_ACTIVATION_R1.md`;
- `ACTIVATED_E2E_SUBGRAPH_R1.md/.json`;
- its own role card;
- source-current external standards, documentation and public evidence relevant to its own front;
- existing pre-campaign owner evidence that predates the current round.

Before first-verdict freeze, an Agent **must not** read:

```text
another A01–A25 current-round report
another current-round verdict
another current-round scratchpad
another current-round repair commit
Coordinator synthesis of current-round findings
A23 Red-Team verdict
current-round peer chat transcript
```

Independent disagreement is useful evidence.

## 3. First verdict content

A first verdict is a compact frozen object, not a final report.

It must include:

```text
AgentId / FrontIds
ExactBaseline
Role interpretation
Current standing
Top falsifiers
Expected inputs from other fronts
Outputs/interfaces this front expects to provide
Highest-risk boundary assumption
Initial recommendation:
  PROCEED
  PROCEED_WITH_CONSTRAINTS
  REQUIRES_REPAIR
  SCOPE_SPLIT_REQUIRED
  BLOCKED_BY_AUTHORITY_OR_APPARATUS
```

After this object is frozen, the Agent may begin bounded interface exchange.

## 4. What may be shared after verdict freeze

Allowed shared interface messages are deliberately narrow:

```text
interface name
producer front
consumer front(s)
semantic meaning
representation/carrier
version/revision identity
required fields / units / coordinate conventions
preconditions
consumer-visible failure modes
validation oracle
compatibility status
```

Allowed examples:

- creature state names/semantics;
- rig bone or animation contract;
- environment concealment-zone representation;
- material/shader inputs;
- audio cue/state binding;
- glTF axis/unit/metadata expectations;
- telemetry event names/fields;
- build/run invocation and artifact identity.

Not allowed as an “interface update”:

- another Agent's full verdict;
- why another Agent thinks the product is good/bad;
- another Agent's private red-team findings before formal defect publication;
- a copy of another lane's whole scratchpad;
- Coordinator pressure to agree.

## 5. Semantic dependency is not scheduling dependency

The E2E graph contains feedback loops. Therefore:

```text
E2ESemanticEdge != MustWaitForProducerToFinish
```

A dependent Agent may begin by:

- freezing requirements;
- defining falsifiers/oracles;
- constructing local fixtures;
- identifying missing interfaces;
- validating existing carriers;
- building adapters against explicit interface drafts.

It should not invent upstream product truth merely to stay busy.

## 6. Execution phases

### Phase 0 — common admission

All A01–A25 independently verify exact baseline/source truth and role scope.

### Phase 1 — independent first verdict

All A01–A25 freeze their first verdict without current-round peer results.

No Coordinator synthesis before all expected first verdicts are frozen or explicitly marked unavailable.

### Phase 2A — upstream product / knowledge / direction

Primary fronts:

```text
A01 Product/Core Loop
A02 Player Experience/Session/Onboarding/UX/Cue Design
A03 Research-to-Product
A04 Art Direction
A21 Telemetry / Player Evidence protocol preparation
A22 Accessibility constraints
```

Their outputs constrain downstream production but do not own specialist implementation. A21/A22 begin early so evidence and accessibility requirements are not bolted on after integration.

### Phase 2B — parallel specialist production

```text
A05 Environment 3D
A06 Creature 3D
A10 Material/LookDev
A11 Lighting
A13 Behavior
A15 Sound Design
A24 Rights/Provenance
```

### Phase 2C — dependent production

```text
A07 Rigging
A08 Animation Production
A09 Animation Systems
A12 Camouflage Shader/Rendering
A14 Navigation/Collision/Affordance
A16 Interactive/Spatial Audio/Mix
```

These Agents may begin earlier with requirements/oracles, but actual product binding consumes declared producer handoffs.

### Phase 2D — runtime / interchange / build integration

```text
A17 Engine Integration
A18 Asset Interchange/Validation/Runtime Loading
A19 Build/Reproducibility + Workstation/Engineering repair router
A21 Telemetry / Player Evidence instrumentation integration
A25 Player Interaction Runtime / Camera / Input / UI
```

### Phase 3 — exact-condition technical evaluation

A20 owns performance engineering/evaluation under an exact integrated condition.

A20 may recommend producer repairs but cannot silently redefine the visual/product target to make performance green.

### Phase 4 — independent integrated falsification

A23 receives a **frozen integration candidate** plus admissible receipts, not producer scratchpads.

A23 attacks:

- fresh launch;
- complete loop reachability;
- visual/audio/behavior coherence;
- missing/placeholder assets;
- state desynchronization;
- crash/softlock;
- performance evidence transport;
- false activation claims;
- Human-claim laundering.

A23 does not own routine producer implementation.

### Phase 5 — owner-correct repair / replay

Formal defect receipt:

```text
observed consequence
exact candidate/condition
failing oracle
probable owner front/E2E
minimal reproduction
severity
```

Then:

```text
CompositeFailure
→ owner-correct repair
→ constituent validation
→ same composite consequence replay
→ independent re-evaluation where required
```

### Phase 6 — Human-ready admission

A02/A21/A22/A23 can jointly determine whether apparatus/product/protocol is ready for a real participant.

They cannot manufacture the Human evidence itself.

## 7. Producer / judge separation

Mandatory:

```text
A23 Red Team != production owner
A24 Rights/Provenance != final product judge
A20 performance evaluator != authority to redefine product thesis
A21 Human protocol designer != Human participant
A01 integration authority != automatic specialist truth authority
```

If A23 makes an emergency repair, the repaired claim needs another independent re-check before A23 may rely on it for final adjudication.

## 8. Interface publication

Each Agent maintains at most one campaign-local interface handoff file per owned front unless a second file is materially necessary.

Preferred path:

```text
experiments/veilwild-r1/handoffs/<agent-id>-<front-id>.json
```

Interface handoff is durable product communication. Chat prose is not the authority.

## 9. Commit / artifact rules

Every producer change must identify:

```text
source baseline
workspace
exact commit
changed files
artifact identities where material
validation commands/oracles
known limitations
```

`git status clean` is useful but not semantic completion.

Generated/interchange/runtime copies must identify whether they are:

```text
AUTHORITATIVE_EDITABLE_SOURCE
DERIVED_INTERCHANGE
DERIVED_RUNTIME_COPY
BUILD_ARTIFACT
EVIDENCE_ARTIFACT
```

## 10. Human claim guard

Until a real participant produces evidence under a frozen protocol/build condition:

```text
fun = UNKNOWN
immersion = UNKNOWN
believability = UNKNOWN
Human detectability = UNKNOWN
Human cue usefulness = UNKNOWN
Human fairness = UNKNOWN
```

Expert inspection or synthetic image/audio metrics may narrow technical hypotheses but do not change these standings.

## 11. Scope-pressure admission and implementation escalation

A production Agent may discover pressure; it may not unilaterally change the R1 topology. A proposed new pressure-triggered E2E must use `scopePressureProposals` with exact blocker evidence and distinct input/output/failure/oracle. Admission requires affected-owner technical evidence + A01 product-thesis necessity + Coordinator record. `DORMANT_R1` requires explicit scope amendment and fresh topology falsification. Implementation depth inside an active closure changes zero topology counts unless a distinct stable responsibility emerges.

## 12. Dynamic split / merge rule

An opening Agent role should split when a sub-front develops:

```text
stable distinct input
+ stable distinct output
+ distinct repeated failure modes
+ distinct oracle
+ enough parallel pressure that shared ownership hides defects or blocks progress
```

Opening roles may merge only after evidence shows the distinction is not carrying independent product responsibility.

Do not merge solely because one Agent finished early.

## 13. Stop conditions

A front stops its current wave when one of these is true:

```text
validated handoff ready
formal blocker receipt emitted
standing falsified/contradicted
authority/appartus gate reached
scope split justified
```

Do not generate filler work after the front has satisfied its current product responsibility.
