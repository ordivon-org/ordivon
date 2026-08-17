# Ordivon Media Foundations — MF7-D Persistence, Identity, Trajectory, History & Continuity Through Change

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 41 at start  
**Input:** MF0–MF6 frozen; MF7-A→C complete/provisional.  
**Status:** MF7-D complete/provisional. State & Dynamics Foundations remain UNFROZEN.  
**Next:** MF7-E — Invariants, Stability, Equilibria, Attractors & Regimes.

---

# 0. Purpose

MF7-A separated state from observation/representation and full reality. MF7-B separated dynamics from trajectory/history/log. MF7-C separated state from Markov sufficiency and uncertainty from stochasticity.

MF7-D asks:

> **What lets multiple state/process occurrences count as occurrences of the same continuing bearer/process, rather than merely similar successors? What survives repair, replacement, turnover, branching, restart, restore and replay?**

Dangerous collapses:

```text
Persistence = No Change
Identity = Same State
Identity = Same Matter
Identity = Same Structure
Identity = Same Function
Identity = Same Identifier
Identity = Same Name
Identity = Same Memory Bytes
Identity = Same Program Image
Identity = Continuous Trajectory
Identity = Causal Lineage
Lineage = Identity
Replica = Same Object
Descendant = Same Object
Restore = Same Runtime Occurrence
Restart = Continuation by default
Fork = One Identity Continuing Twice
Fusion = One Prior Identity Survives by default
Same State Again = Same State Occurrence
Same Path Shape = Same Trajectory
History = State Sequence
History = Log
Shared History Prefix = Same Complete History
```

---

# 1. Qualitative equivalence is not token identity

Two objects/processes can have the same modeled properties/state while being numerically distinct tokens.

### SD-001
**QualitativeEquivalence ≠ Token/NumericalIdentity.**

### SD-002
State equivalence says two bearer occurrences occupy the same state class; it does not say they are the same bearer occurrence or continuing object.

### SD-003
Two replicas can be behaviorally/structurally indistinguishable while remaining distinct tokens.

---

# 2. Token identity is not a state variable value

### SD-004
**Object/SystemTokenIdentity ≠ StateValue.**

The same object can traverse many state values; multiple objects can instantiate one state value.

### SD-005
Identity claims require a relation across bearer occurrences, not merely equality of state coordinates.

### SD-006
This preserves MF7-A `ObjectIdentity ≠ StateIdentity` and MF6 `StateType/Value ≠ StateOccurrence`.

---

# 3. Persistence is compatible with change

### SD-007
**Persistence ≠ NoChange.**

A persisting bearer can change configuration, properties, internal state, components and activity.

### SD-008
A persistence criterion must therefore specify which transformations preserve bearer identity and which terminate/create/branch it.

### SD-009
Perfect state constancy is neither necessary nor generally sufficient for object/process persistence.

---

# 4. Provisional ContinuationStanding — identity firewall

MF7-D introduces:

```text
ContinuationStanding(B_i, B_j | IdentityCriterion, StandingRoute, Scope)
```

A later bearer/process occurrence `B_j` has ContinuationStanding from earlier occurrence `B_i` when a non-arbitrary target/formal/operational lineage connects them through transformations that the declared domain's identity criterion treats as preserving one token rather than creating merely a replica, descendant, replacement, successor or new instance.

### SD-010
**Similarity ≠ ContinuationStanding.**

### SD-011
**CausalConnection ≠ ContinuationStanding by itself.**

### SD-012
**SameIdentifier ≠ ContinuationStanding by itself.**

### SD-013
ContinuationStanding requires provenance/lineage plus criterion-specific preservation semantics.

---

# 5. Provisional PersistenceStanding

```text
PersistenceStanding(B | Interval/History, IdentityCriterion, Scope)
```

when bearer occurrences across the declared temporal scope form a grounded continuation chain under one identity criterion, subject to explicit branch/fusion/termination rules.

### SD-014
Persistence is a cross-occurrence relation/profile, not an instantaneous property.

### SD-015
Persistence can be interrupted or reconstructed at one standing route while another route treats continuity as preserved; identity must be typed.

---

# 6. Identity criterion is target/domain relative, not arbitrary

Possible criteria can emphasize:

- physical/process continuity;
- causal/lineage continuity;
- organizational/functional continuity;
- constitutive material continuity;
- institutional/legal identity;
- system-generated token/UID identity;
- application/session identity;
- process/runtime lifetime;
- biological lineage/organismal organization;
- artifact provenance/version lineage.

### SD-016
**No one criterion is frozen as universally necessary/sufficient across all object classes.**

### SD-017
Criterion relativity is constrained by target rules, intervention consequences, provenance and consumer purpose; it is not free relabeling.

---

# 7. POSIX fork: same-like process image, different process identity

POSIX `fork()` creates a new child process that is an exact copy of the calling parent except for specified distinctions, including a unique child PID.

### SD-018
**Near-identical process image/state ≠ same process token.**

### SD-019
Fork creates lineage/descendance and shared inherited resources, but a new process identity.

### SD-020
This is a decisive hard case against `SameState/Structure => SameIdentity`.

---

# 8. POSIX exec: different program/process image, continuing process identity

POSIX `exec` replaces the current process image with a new process image while preserving process-level attributes including process ID; Linux explicitly notes that `execve` does not create a new process.

### SD-021
**ProgramImageIdentity ≠ ProcessIdentity.**

### SD-022
A process can undergo radical replacement of memory mappings/program image and retain process identity under OS semantics.

### SD-023
This is a decisive hard case against `ChangedStructure/Program => NewIdentity`.

---

# 9. Fork + exec jointly falsify structural identity

From fork:

```text
high state/image similarity + lineage → distinct processes
```

From exec:

```text
large image/state replacement + preserved process lifetime → same process
```

### SD-024
**Neither structural sameness nor structural difference is sufficient to decide process identity.**

### SD-025
Process identity is governed by lifecycle/continuation semantics and provenance.

---

# 10. Identifier is evidence/handle, not identity by itself

POSIX defines PID as an identifier representing a process during its lifetime and allows reuse only after that process lifetime ends.

### SD-026
**PIDValue ≠ globally persistent process identity.**

### SD-027
The same numeric PID can identify different process lifetimes at different times after reuse.

### SD-028
Identifier + temporal/lifetime provenance is stronger than bare identifier equality.

---

# 11. Stable handle can be more specific than reusable name

Linux documentation notes PID reuse after process exit and designs pidfd/inode-like handles to avoid accidentally acting on a later process that reuses the same numeric PID.

### SD-029
**SameNumericIdentifierAcrossTime ≠ SameToken.**

### SD-030
Identity-aware handles are themselves representations/references to token lifetimes, not the token ontology itself.

---

# 12. Kubernetes hard case: same name, different historical object

Kubernetes permits deleting an object and later creating a new object with the same name, while assigning every created object a distinct UID across cluster lifetime.

### SD-031
**SameName ≠ SameObjectOccurrence.**

### SD-032
A UID is intended to distinguish historical occurrences of otherwise similar/same-named API objects.

### SD-033
Name continuity can express logical role/configuration intent while UID continuity expresses object-token continuity in that institutional/computational system.

---

# 13. API version representation is not object identity

Kubernetes treats different API versions as different representations of the same underlying object rather than new object identities.

### SD-034
**RepresentationVersion ≠ ObjectIdentity.**

### SD-035
Changing representation/schema view need not create a new target object.

This directly reuses MF3 representation standing.

---

# 14. Logical service identity can outlive process/object tokens

A service role/name can be maintained while underlying processes/pods are replaced.

### SD-036
**LogicalServiceIdentity ≠ Worker/ReplicaTokenIdentity.**

### SD-037
A higher-level institutional/functional bearer may persist through lower-level component replacement if the domain explicitly constitutes that continuity.

### SD-038
This is not proof that function alone universally determines identity; it is a standing-route distinction.

---

# 15. Checkpoint/restore reconstructs execution state rather than preserving uninterrupted physical execution

CRIU checkpoint records process-tree/resources; restore recreates process trees by forking tasks and reconstructing resources/state. In some namespace restore cases the real root PID is not predetermined.

### SD-039
**CheckpointRestore ≠ UninterruptedPhysicalProcessOccurrence.**

### SD-040
A restored application can be treated as logical continuation at an application/session route while consisting of newly created OS process occurrences at the runtime route.

### SD-041
Identity across restore is therefore typed and policy/standing dependent.

---

# 16. Same checkpoint can in principle seed more than one continuation

If a stored state image can be restored into multiple independent executions, structural/state equality cannot make all restorations numerically identical to one original runtime token.

### SD-042
**Snapshot/CheckpointEquality ≠ RuntimeTokenIdentity.**

### SD-043
Restore-from-common-state creates shared ancestry/provenance; strict token identity requires branch semantics.

---

# 17. Restart versus continuation

Terminating one process and launching another with the same executable/configuration/name is a new process token under OS lifetime semantics.

### SD-044
**Restart ≠ SameProcessToken.**

### SD-045
An application/service/session identity may nevertheless be intentionally continued across restart by higher-level state/authority rules.

### SD-046
Process identity and application identity must be separately typed.

---

# 18. Branching is the strongest strict-identity firewall

Suppose one predecessor has two later descendants `B` and `C` with `B ≠ C`.

If strict identity held both ways:

```text
A = B
A = C
```

then classical identity entails `B = C`, contradicting their distinctness.

### SD-047
**Strict numerical identity cannot branch into two mutually distinct tokens.**

### SD-048
**Continuation/Lineage can branch; strict Identity cannot.**

### SD-049
Branching therefore requires distinctions such as parent/child, ancestor/descendant, fork/replica, successor/branch rather than declaring every descendant `the same token`.

---

# 19. POSIX fork is the operational branching hard case

The parent continues and a distinct child is created.

### SD-050
**Shared pre-fork history/state ≠ shared post-fork token identity.**

### SD-051
Fork produces a branch point in process lineage with two distinct lifetimes.

### SD-052
A common past does not force one identity after branching.

---

# 20. Cell division is the biological branching hard case

C. elegans lineage studies directly trace sequential cell divisions into daughter cells and differentiated descendants.

### SD-053
**CellLineageContinuation ≠ SameCellToken.**

### SD-054
Parent-to-daughter relation is genealogical/causal continuation, not numerical identity of one cell surviving as two distinct daughters.

### SD-055
Lineage identity and individual-cell identity must therefore be separate biological profiles.

---

# 21. Lineage is not identity

### SD-056
**Ancestor/Descendant ≠ SameObject.**

### SD-057
Causal descent is evidence of provenance/continuation but permits branching and therefore cannot universally equal strict token identity.

### SD-058
A clone/lineage can itself be a higher-level bearer whose identity persists across many descendant cells; standing route changes the target.

---

# 22. Fusion is the dual hard case

When two prior bearer/process lineages combine into one later bearer, strict numerical identity cannot make that one later token identical to two previously distinct tokens without collapsing their distinction.

### SD-059
**Fusion/CompositionContinuation ≠ strict identity with every input bearer.**

### SD-060
Fusion requires constitution/composition/successor semantics distinct from identity.

### SD-061
MF4 Composition therefore participates in persistence claims involving merger/fusion.

---

# 23. Material sameness is not universally necessary

Human tissues exhibit continual cellular turnover; quantitative estimates find large daily replacement of cells/cellular mass, especially blood and gut epithelium.

### SD-062
**FixedMaterialConstituents are not a plausible universal requirement for organism-level persistence.**

### SD-063
Component turnover can coexist with organism/tissue-level continuation under biological organizational/lineage processes.

### SD-064
This does not prove matter is irrelevant to every object type; material continuity remains one possible criterion/profile.

---

# 24. Ship of Theseus is the canonical material-replacement falsifier

Plutarch reports that the Athenians preserved Theseus' ship while replacing old timbers with new ones over time, explicitly noting philosophical disagreement over whether it remained the same ship.

### SD-065
The case demonstrates that **component replacement alone underdetermines identity without a declared criterion.**

### SD-066
`SameMaterial` cannot be frozen as universal identity criterion; neither can `SameOrganization` be assumed sufficient without domain standing.

---

# 25. Same matter is not universally sufficient either

Components removed from one object can be reassembled elsewhere; material provenance alone can support multiple competing identity claims when organization/continuation branches.

### SD-067
**MaterialOverlap/Reuse ≠ SameBearer by default.**

### SD-068
Material identity claims require boundary, composition and continuation criteria.

---

# 26. Structural sameness is not sufficient

Two independently built byte-identical files, cloned VMs, identical manufactured objects or process replicas can have the same structure/state.

### SD-069
**SameStructure ≠ SameToken.**

### SD-070
Structural equivalence is a type/property relation, not numerical identity.

### SD-071
Fork provides the concrete computational hard case.

---

# 27. Structural continuity is not always necessary

Exec replaces program/process image while OS process identity persists; organisms repair/remodel; software can migrate/upgrade while higher-level service identity remains.

### SD-072
**Large structural change can coexist with persistence under some identity criteria.**

### SD-073
Allowed transformation class is part of the IdentityCriterion.

---

# 28. Functional sameness is not identity

Two replicas can provide the same function simultaneously.

### SD-074
**FunctionalEquivalence ≠ NumericalIdentity.**

### SD-075
A failed component can be replaced by a functionally equivalent one while component identity changes and system/service identity may persist.

### SD-076
Function can support higher-level continuity but cannot universally identify lower-level tokens.

---

# 29. Functional continuity is not universally necessary

An object/system can temporarily lose functionality during repair/sleep/failure and later recover without necessarily being reconstituted as a new token under the relevant domain.

### SD-077
**ContinuousFunctioning ≠ universal persistence requirement.**

### SD-078
Operational downtime and identity termination must remain separate unless domain rules equate them.

---

# 30. Spatial continuity is not identity

Objects can move; different objects can occupy the same location at different times.

### SD-079
**SameLocation ≠ SameObject.**

### SD-080
Continuous worldline/path can support physical persistence evidence but does not alone resolve branching, fusion or hidden replacement.

### SD-081
MF5 positional standing and MF7 identity standing remain distinct.

---

# 31. Temporal continuity is not identity

Two processes can occur continuously one after another without being the same process; one process can be suspended and resumed.

### SD-082
**TemporalAdjacency/Continuity ≠ TokenIdentity.**

### SD-083
A temporal gap does not automatically terminate higher-level logical identity; uninterrupted time does not guarantee sameness.

### SD-084
MF6 provides occurrence structure, not identity criterion.

---

# 32. Causal continuity is evidence, not universal identity

Fork/cell division shows causal lineage can branch.

### SD-085
**CausalContinuity ≠ NumericalIdentity.**

### SD-086
Causal continuity is a strong provenance/continuation route but must be paired with branch/fusion and token-preservation rules.

---

# 33. Process identity differs from object identity

A process is an extended organized occurrence; a material object may participate in many processes.

### SD-087
**ProcessIdentity ≠ ParticipantObjectIdentity.**

### SD-088
The same object can stop one process and begin another; one process can involve changing participants.

### SD-089
Process persistence criteria may emphasize organization/causal-temporal structure rather than constituent token continuity.

---

# 34. Process persistence does not require constant state

### SD-090
A process can pass through phases/modes while remaining one process episode under a declared boundary/continuity criterion.

### SD-091
**PhaseChange ≠ NewProcess by default.**

### SD-092
Process segmentation is criterion/scope dependent and can be uncertain/vague.

---

# 35. Process identity does not equal trajectory shape

Two independent executions can trace identical state values over time.

### SD-093
**SameTrajectoryShape ≠ SameProcessToken.**

### SD-094
Trajectory equality/equivalence must distinguish state-value path, temporal parameterization, bearer identity and occurrence provenance.

---

# 36. Trajectory type versus trajectory token

MF7-D distinguishes:

```text
TrajectoryType/Shape
```

from:

```text
TrajectoryToken/Occurrence
```

### SD-095
**TrajectoryType ≠ TrajectoryToken.**

### SD-096
A trajectory token is tied to particular state occurrences/run/bearer provenance.

### SD-097
One trajectory type can be instantiated by many runs.

---

# 37. Reparameterized path may be same geometric path but different trajectory profile

Two trajectories can visit the same state-space path at different rates/directions/timing.

### SD-098
**StateSpacePath ≠ TemporalTrajectory by identity.**

### SD-099
Order, parameterization, timing and bearer provenance are optional/typed invariants depending claim.

### SD-100
MF5 geometry and MF6 temporal profile must remain explicit.

---

# 38. Same state again is not same state occurrence

A periodic system can revisit abstract state `A`:

```text
A@t1 → B@t2 → A@t3
```

### SD-101
**StateValue(A@t1) = StateValue(A@t3) does not imply occurrence identity.**

### SD-102
Recurring state values are distinct tokens in one history unless the domain explicitly quotients them.

### SD-103
Rewind/replay can recreate state value without recreating original occurrence.

---

# 39. History is not merely a sequence of state values

A target history includes grounded occurrence tokens/relations and provenance; it may include events, process boundaries, inputs, branch/fusion, durations and interventions.

### SD-104
**History ≠ StateValueSequence.**

### SD-105
Identical abstract sequences can occur in different runs/times/bearers and therefore be distinct history tokens.

### SD-106
History identity requires occurrence/provenance standing, not string equality.

---

# 40. History is not log

MF7-B established `Log ≠ History`.

### SD-107
Different logs can represent the same target history; identical log text can be replayed/synthetic or mapped to different occurrences.

### SD-108
**LogIdentity ≠ HistoryIdentity.**

### SD-109
History claims remain MF3-grounded representations/evidence when reconstructed from logs.

---

# 41. Shared history prefix does not mean same full history

Branches can share all occurrences up to a branch point and diverge afterward.

### SD-110
**SharedPrefix ≠ SameCompleteHistory.**

### SD-111
History identity can be prefix-related/lineage-related rather than equal.

### SD-112
Branch-aware histories require explicit ancestry/branch IDs rather than one linear timeline assumption.

---

# 42. Forked histories require branch semantics

After process fork, parent and child share inherited pre-fork state/provenance but instantiate distinct later process histories.

### SD-113
**OnePast can support multiple descendant histories without becoming multiple identical present tokens.**

### SD-114
This is the history analogue of `Lineage ≠ Identity`.

---

# 43. Simulation rewind does not resurrect occurrence identity

A simulation may restore state corresponding to earlier simulation coordinate `t_sim` and continue differently.

### SD-115
**RevisitedSimulationState ≠ OriginalStateOccurrence.**

### SD-116
The new branch has a later wall/runtime occurrence and shared simulation-history prefix/provenance.

### SD-117
Rewind requires branch/versioned-history semantics when new actions diverge from the recorded path.

---

# 44. Checkpoint restore is analogous to simulation branch but identity is layered

A restored checkpoint can be considered:

- same logical application/session;
- new OS process tokens;
- descendant runtime episode;
- same/different distributed service instance depending authority rules.

### SD-118
**RestoreIdentity is typed, not one boolean.**

### SD-119
Identity questions must name the bearer level.

---

# 45. Replica identity

Two concurrently running replicas may share code/configuration/state snapshot and logical service role.

### SD-120
**ReplicaEquivalence ≠ TokenIdentity.**

### SD-121
Replica set/service identity can persist while membership tokens change.

### SD-122
Group/set identity and member identity are different composition levels.

---

# 46. Distributed system identity can be authority constituted

A distributed object may be identified by a system-assigned UID/term/session/key while physical hosting nodes/processes change.

### SD-123
**Institutional/ProtocolIdentity can be genuine operational identity standing.**

### SD-124
It does not automatically transfer to physical substrate identity.

### SD-125
Authority/protocol provenance is first-class.

---

# 47. Identifier aliases and names are many-to-one/one-to-many over time

One object can have multiple aliases; one reusable name can denote multiple historical objects.

### SD-126
**NameEquality/PointerEquality ≠ universal identity test.**

### SD-127
Identifier semantics require namespace, authority, lifetime and reuse policy.

### SD-128
Kubernetes UID/name and POSIX PID reuse are direct hard cases.

---

# 48. Version identity versus object identity

An object can change version while remain one token; a version can be copied into multiple objects.

### SD-129
**VersionIdentity ≠ ObjectIdentity.**

### SD-130
Version lineage is a provenance/change relation, not strict identity by itself.

### SD-131
Same version content can instantiate multiple artifact/deployment tokens.

---

# 49. Artifact content identity versus artifact token identity

Two byte-identical files/blobs can be content-identical while being distinct filesystem/object occurrences.

### SD-132
**ContentIdentity/Equality ≠ ArtifactTokenIdentity.**

### SD-133
Content-addressed identity intentionally chooses content equivalence as identity criterion for a particular abstraction layer; that criterion must not be exported to physical/storage token identity.

---

# 50. Hash/digest equality is representational criterion, not universal identity

### SD-134
**SameDigest ≠ SamePhysicalObject.**

A digest can intentionally identify immutable content under a content-addressed system while many physical copies share it.

### SD-135
Digest identity is an institutional/formal equivalence criterion over bytes, not numerical identity of carriers.

---

# 51. Replacement versus repair

Replacing a component can preserve higher-level system identity while terminating component identity.

### SD-136
**RepairAtLevelL can contain ReplacementAtLevelL-1.**

### SD-137
Persistence must therefore be multiscale/compositional.

### SD-138
There is no contradiction in `system persists` and `component does not persist`.

---

# 52. Organismal persistence under cell turnover is multiscale

Human cellular turnover is substantial and tissue dependent; cell populations are continually renewed.

### SD-139
**OrganismIdentity ≠ identity of a fixed set of cell tokens.**

### SD-140
Biological persistence can rely on regulated organization, lineage, boundary maintenance and function while components turn over.

### SD-141
This is a model-level inference from turnover evidence, not a claim that matter never matters biologically.

---

# 53. Cell lineage persistence versus cell identity

A stem-cell lineage/clonal population can persist across divisions even though individual cells are born/die.

### SD-142
**LineageBearerIdentity ≠ MemberCellIdentity.**

### SD-143
Higher-level lineage continuity can survive member replacement/branching.

### SD-144
The target bearer must be declared before asking `same?`.

---

# 54. Boundary change can change identity target

A system boundary may expand from process to application to service to organization.

### SD-145
**Identity is boundary-relative because the bearer itself changes.**

### SD-146
This does not mean an object can be arbitrarily declared identical; the new boundary defines a different token class/standing route.

---

# 55. Constitutive parts versus replaceable parts

Some domains treat specific components as constitutive; others treat them as replaceable.

### SD-147
**PartReplacementEffectOnIdentity is domain/criterion dependent.**

### SD-148
No universal percentage-of-material or structural-similarity threshold is frozen.

### SD-149
Quantitative overlap can be evidence but not a universal identity scalar.

---

# 56. Identity is not a similarity score

### SD-150
**TokenIdentity is not graded similarity by default.**

Similarity can be continuous; strict identity is an equivalence/token-membership relation under a criterion.

### SD-151
Near-identical replicas remain distinct; heavily changed continuing objects may remain same token.

### SD-152
Probabilistic identity inference under uncertainty is epistemic confidence about a discrete/typed relation, not partial metaphysical identity by default.

---

# 57. Ambiguous identity evidence is not ambiguous ontology by necessity

Sensor/log provenance may be insufficient to tell whether two observations belong to the same bearer.

### SD-153
**IdentityUncertainty ≠ PartialIdentity.**

### SD-154
Maintain probability/confidence over candidate token correspondences when evidence is incomplete.

### SD-155
Some social/legal/philosophical domains may genuinely leave identity conventionally disputed; model must preserve that instead of fabricating certainty.

---

# 58. Identity relation versus continuation relation

This is MF7-D's central distinction:

```text
IdentityRelation
```

is strict same-token membership under a criterion.

```text
ContinuationRelation
```

is directed provenance/lineage/process continuity and can support branching/fusion/succession.

### SD-156
**IdentityRelation ≠ ContinuationRelation.**

### SD-157
Continuation is usually broader and can branch; strict identity cannot branch among distinct tokens.

### SD-158
PersistenceStanding uses continuation plus explicit token-preservation/branch rules.

---

# 59. Descendant/successor/replacement/replica require typed relations

MF7-D requires at least:

```text
SameToken
ContinuesAs
DescendsFrom
ReplicatesFrom
RestoresFrom
Replaces
Supersedes
BranchesFrom
MergesFrom
Represents
Aliases
```

### SD-159
**One generic `same/related` edge destroys critical identity semantics.**

---

# 60. Identity through replacement is not transitive via similarity

If A resembles B and B resembles C, A/C can be very different; similarity thresholds do not generally form an identity equivalence relation.

### SD-160
**SimilarityChain ≠ IdentityChain.**

### SD-161
Persistence requires grounded continuation at each relevant transformation plus criterion semantics, not accumulation of local resemblance.

---

# 61. Temporal gaps and suspension

A process/application can be suspended, hibernated, checkpointed or disconnected.

### SD-162
**ContinuousActivity ≠ Persistence by necessity.**

### SD-163
A gap may preserve identity under one criterion if continuation state/provenance remains, while terminating an uninterrupted physical process criterion.

### SD-164
Gap handling belongs in PersistenceProfile.

---

# 62. Destruction/recreation hard case

Destroying an object and later recreating one with identical state/name/content generally yields a new token under many operational domains (e.g. Kubernetes UID, process lifetime).

### SD-165
**Recreation ≠ Persistence by default.**

### SD-166
State reconstruction is weaker than token continuation.

### SD-167
Any domain choosing recreation-as-continuation must state the higher-level identity authority/criterion.

---

# 63. Copy versus move/migration

Copy creates multiple descendants/replicas; migration aims to preserve one higher-level identity while changing location/substrate.

### SD-168
**Copy ≠ Move/Migration.**

### SD-169
Whether live migration preserves process/application identity depends on the standing level and protocol semantics; physical substrate identity changes.

### SD-170
Replication/transfer mode must be explicit in provenance.

---

# 64. Trajectory continuity does not prove bearer identity

Two objects can be handed off in exactly the same path/position/time trace, or one tracker can mistakenly stitch tracks.

### SD-171
**ContinuousTrack ≠ GuaranteedObjectIdentity.**

### SD-172
Tracking is an identity inference problem using motion, appearance, interaction and continuity evidence.

### SD-173
MF2 perceptual object persistence similarly cannot be elevated to target physical identity without evidence.

---

# 65. Bearer identity does not require continuous observable trajectory

Occlusion, sensor outage or sleep can create observation gaps.

### SD-174
**ObservationTrajectoryContinuity ≠ BearerPersistence.**

### SD-175
Persistence can be inferred through hidden intervals with uncertainty/provenance.

---

# 66. Counterfactual replacement diagnostic

Hold current state/structure/function fixed but replace lineage/provenance token with an independently created duplicate.

### SD-176
If the domain distinguishes the duplicate from the continuing bearer, qualitative equivalence is not the identity criterion.

### SD-177
Fork/recreation/replica systems operationalize this diagnostic.

---

# 67. Radical-transformation diagnostic

Hold continuation/lifetime provenance fixed while radically changing state/structure/program image.

### SD-178
If the domain preserves token identity, structural sameness is not necessary.

### SD-179
Exec provides the canonical software hard case.

---

# 68. Branch diagnostic

Create two descendants from one prior state/lineage.

### SD-180
If both descendants remain distinct, the inherited relation must be typed as lineage/continuation rather than strict identity with the predecessor.

### SD-181
Fork and cell division are canonical branch tests.

---

# 69. Recreate-after-destruction diagnostic

Destroy bearer token, then reproduce same name/content/state.

### SD-182
If domain authority allocates a new token/UID/lifetime, identity was not encoded by state/name/content alone.

### SD-183
Kubernetes object recreation and POSIX process lifetime/reuse provide hard cases.

---

# 70. Layer-switch diagnostic

Ask identity at several levels simultaneously:

```text
physical substrate
process/runtime
application/session
logical service
artifact/content
organization/institution
```

### SD-184
Apparent contradiction often disappears when identity target is typed by level.

### SD-185
`same service, new process` and `same process, new program image` are coherent multi-level claims.

---

# 71. Provisional IdentityProfile

```text
IdentityProfile = <
  BearerType/Boundary,
  Token/Type Level,
  IdentityCriterion,
  StandingRoute/Authority,
  ContinuationRelation,
  AllowedTransformations,
  Constitutive/Replaceable Components?,
  MaterialContinuity?,
  StructuralContinuity?,
  FunctionalContinuity?,
  Spatial/Temporal Continuity?,
  Causal/Lineage Provenance?,
  Identifier/UID Lifetime?,
  BranchRules,
  FusionRules,
  Restart/Restore/MigrationRules?,
  TerminationCriteria,
  Uncertainty,
  Evidence/Provenance,
  Scope
>
```

### SD-186
Bare `same object=true` is under-specified across complex systems.

---

# 72. Provisional PersistenceProfile

```text
PersistenceProfile = <
  BearerToken,
  Start/End Occurrence,
  IdentityCriterion,
  ContinuationChain,
  Change/Repair/Replacement History,
  Gap/Suspension Periods?,
  ComponentTurnover?,
  Branch/Fusion Events?,
  Restore/Restart Events?,
  Higher/Lower-Level Identities?,
  Evidence/Tracking,
  Uncertainty,
  Provenance,
  Scope
>
```

### SD-187
Persistence must record identity-affecting events, not only start/end timestamps.

---

# 73. Provisional ContinuationClaim

```text
ContinuationClaim = <
  EarlierBearerOccurrence,
  LaterBearerOccurrence,
  RelationType : same-token/continues/descends/replicates/restores/
                 replaces/supersedes/branches/merges/etc.,
  IdentityCriterion,
  Lineage/Provenance Evidence,
  Transformation/Gap,
  Branch/Fusion Context?,
  Authority/StandingRoute,
  Confidence/Uncertainty,
  Scope
>
```

### SD-188
A directed continuation claim should not be silently promoted to symmetric identity.

---

# 74. Provisional TrajectoryIdentityProfile

```text
TrajectoryIdentityProfile = <
  Bearer/Run,
  StateDomain,
  StateOccurrenceSequence/Path,
  TemporalParameterization,
  Branch/Segment Identity,
  Initial/Boundary Conditions,
  DynamicsModel/Standing,
  PathEquivalenceCriterion : exact/reparameterized/geometric/statistical/etc.,
  OccurrenceProvenance,
  Uncertainty,
  Scope
>
```

### SD-189
Trajectory equivalence and trajectory token identity are separate claims.

---

# 75. Provisional HistoryProfile

```text
HistoryProfile = <
  Target/Bearer/Run,
  OccurrenceTokens,
  TemporalRelations,
  State/Process/Transition Claims,
  Inputs/Interventions?,
  Branch/Fusion Structure?,
  Identity/Continuation Relations,
  Source/Log/Evidence Mappings,
  CompletenessClaim?,
  Uncertainty,
  Provenance,
  Scope
>
```

### SD-190
A history can be partial/uncertain/nonlinear and still have legitimate standing.

---

# 76. Standing routes for identity/persistence

1. **Physical/Material** — physical bearer/process continuity under a physical criterion.
2. **Biological/Lineage/Organismal** — organism, cell, clone, tissue identities with lineage/organization rules.
3. **Computational/Runtime** — process/thread/runtime object lifetimes.
4. **Application/Service** — logical application/session/service continuity across runtime replacement.
5. **Formal/Simulation** — constituted entity/run identity under formal rules.
6. **Artifact/Content** — artifact token versus content-addressed/version identities.
7. **Institutional/Legal/Social** — authority-defined identity/continuity.
8. **Perceptual/Tracking** — inferred object persistence in perception/tracking.
9. **Representational** — identifiers/records/track IDs standing for target identities.
10. **Hybrid**.

### SD-191
**StandingRoute ≠ EvidenceRoute.**

---

# 77. Strongest non-collapse stack after MF7-D

```text
QualitativeEquivalence
 ≠ Numerical/TokenIdentity
```

```text
StateIdentity
 ≠ ObjectIdentity
 ≠ ProcessIdentity
```

```text
Persistence
 ≠ NoChange
```

```text
SameMatter
 ≠ SameObject by universal identity
```

```text
SameStructure
 ≠ SameObject
```

```text
SameFunction
 ≠ SameObject
```

```text
SameIdentifier/Name/PID
 ≠ SameToken without lifetime/provenance
```

```text
Continuation
 ≠ Identity
```

```text
Lineage/Descendance
 ≠ Identity
```

```text
Replica
 ≠ SameToken
```

```text
Restore/Recreate
 ≠ SameRuntimeOccurrence
```

```text
ProgramImageIdentity
 ≠ ProcessIdentity
```

```text
ProcessIdentity
 ≠ Application/ServiceIdentity
```

```text
StateValueEquality
 ≠ StateOccurrenceIdentity
```

```text
TrajectoryShape/Type
 ≠ TrajectoryToken
```

```text
StateSpacePath
 ≠ TemporalTrajectory
```

```text
History
 ≠ StateSequence
 ≠ Log
```

```text
SharedHistoryPrefix
 ≠ SameCompleteHistory
```

```text
StrictIdentity
 ≠ BranchingLineage
```

---

# 78. Claims rejected by MF7-D

Reject as universal/foundational:

- persistence means no state/property/component change;
- same state or same snapshot proves same object;
- same matter is necessary/sufficient for identity;
- same structure/content/function proves identity;
- same identifier/name/PID proves identity across time;
- continuous time/spatial path alone proves identity;
- causal continuity/lineage equals strict identity;
- a descendant/replica is numerically the same object as its source;
- strict identity can branch into multiple distinct descendants;
- every restore/restart is the same runtime process occurrence;
- checkpoint bytes carry process token identity by themselves;
- same program image means same process;
- different program image means different process;
- same logical service means same worker/process;
- same state recurring later is same state occurrence;
- same trajectory/path shape means same trajectory token;
- history is only a state sequence or log;
- shared historical prefix means same full history;
- component replacement necessarily terminates higher-level identity;
- function loss/downtime necessarily terminates identity;
- identity is one universal similarity score.

---

# 79. Primary/authoritative evidence anchors

- **POSIX `fork()` (The Open Group).** `fork()` creates a new child process that is an exact copy of the caller except for specified distinctions, including a unique process ID. Hard case for `same/near-identical process state ≠ same process token` and for branching lineage.
- **POSIX `exec()` (The Open Group) + Linux man-pages `execve(2)`.** `exec` replaces current process image while preserving process identity attributes such as PID; Linux explicitly clarifies that no new process is created. Hard case for `same structure/program ≠ process identity` and `large state/image change ≠ identity termination`.
- **POSIX process lifetime / Linux `/proc` documentation.** PID represents a process during its lifetime and can be reused after lifetime ends; Linux `/proc` documentation explicitly warns about PID reuse. Hard case for `same identifier value ≠ same token across time`.
- **Kubernetes official Object Names and IDs.** Same resource name can be reused after deletion, while every created object has a distinct UID intended to distinguish historical occurrences. Hard case for `same name ≠ same object` and for authority-constituted token identity.
- **CRIU official Checkpoint/Restore design.** Checkpoint captures process-tree/resources; restore recreates process trees through `fork()` and restores resources, with restored real PID not always predetermined in namespace scenarios. Hard case for `restore state ≠ uninterrupted OS process occurrence` and layered logical/runtime identity.
- **Plutarch, _Theseus_ 23.1.** Historical Ship of Theseus case records gradual replacement of timbers and explicit disagreement over whether the vessel remained the same; conceptual hard case for universal material-identity rules.
- **Sulston & Horvitz (1977), `Post-embryonic cell lineages of the nematode, Caenorhabditis elegans`, Developmental Biology 56:110–156; Sulston et al. (1983), embryonic lineage.** Directly traced repeated cell divisions, migrations/deaths and branching cell lineages. Hard case for `lineage/causal descent ≠ same individual cell token`.
- **Sender & Milo (2021), `The distribution of cellular turnover in the human body`, Nature Medicine 27:45–48.** Quantifies substantial ongoing cellular turnover/cellular-mass replacement in human tissues. Supports the inference that fixed cellular constituent identity cannot be a universal organism-persistence requirement.

---

# 80. Deep reconstruction

Naive identity model:

```text
snapshot at t1 == snapshot at t2
            ↓
          same thing

or

same ID/name
    ↓
same thing

or

continuous causal chain
    ↓
same thing
```

MF7-D replaces it with:

```text
Bearer occurrence B_t1
       │
       │ provenance / causal / operational lineage
       ▼
transformations / repair / state change / replacement
       │
       ├── criterion preserves token? ────────> SameToken continuation
       │
       ├── creates branch? ──────────────────> Descendant/Replica/Fork
       │
       ├── replacement? ─────────────────────> Replaces/Supersedes
       │
       ├── restore/recreate? ────────────────> RestoresFrom / NewRuntimeToken
       │
       └── fusion? ──────────────────────────> Constituted/Merged successor

IdentityCriterion + StandingRoute + Provenance + Branch/Fusion Rules
                         │
                         ▼
                 PersistenceStanding
```

Meanwhile:

```text
state equality
structural similarity
material overlap
functional equivalence
identifier equality
trajectory continuity
```

are **evidence/profiles**, not universal identity themselves.

The decisive move is:

> **Persistence is grounded token continuation through transformation under a declared identity criterion. Continuation/lineage is broader than strict identity because it can branch, merge, restore or replace. Static similarity cannot establish identity, and radical state/component change need not destroy it.**

---

# 81. Deepest MF7-D result

Provisional:

> **Identity through change is not the persistence of one state, material set, structure, function, name or identifier. A bearer/process persists when its temporally distinct occurrences are connected by non-arbitrary continuation/provenance standing that a declared domain criterion treats as preserving one token across allowed transformations. Continuation is broader than strict identity: it can encode descent, replication, restore, replacement, branching and fusion, while strict numerical identity cannot branch into multiple distinct tokens. Identity must therefore be typed by bearer level and standing route—physical process, biological organism/lineage, runtime process, logical application/service, artifact/content or institutional object—and cross-level identity claims must not be collapsed.**

Compact:

```text
Similarity says looks/behaves alike.
State equality says same condition class.
Lineage says comes from.
Continuation says carries forward.
Identity says same token under a criterion.
Persistence is identity-preserving continuation across change.

Fork copies state but creates identity.
Exec changes image but preserves process.
Restore recreates runtime while it may preserve logical application.
Cell division branches lineage without one cell becoming two identical cells.
Turnover replaces components without forcing organism identity to end.
```

---

# 82. MF7-A/B/C audit

## MF7-A State
Survives. State and identity are even more clearly distinct; same state can occur in different bearer tokens and one bearer traverses many states.

## MF7-B Dynamics
Survives. Dynamics generates/weights continuations; realized transition/trajectory does not by itself settle bearer identity. EvolutionStanding and ContinuationStanding are distinct.

## MF7-C Markov/Memory
Survives. A state representation can be sufficient/insufficient regardless of bearer token identity; restart/restore can reproduce sufficient state without preserving runtime token.

### SD-192
**MF7-D triggers no need to restart MF7-A→C, but adds Identity/Continuation as new required profiles.**

---

# 83. Earlier-foundation audit

- **MF6 Time:** occurrence tokens/temporal relations are necessary for persistence histories but Time does not determine identity; no reopen.
- **MF5 Space:** spatial continuity is evidence but not identity; no reopen.
- **MF4 Composition:** part replacement/fusion/group identity confirms composition-level typing; no reopen.
- **MF3 Representation:** names, UIDs, logs, snapshots and hashes represent/reference identity; they are not target identity by themselves; no reopen.
- **MF2 Perception:** perceptual tracking/persistence can infer but does not constitute target identity; no reopen.

### SD-193
**MF0–MF6 remain FROZEN; MF7-D triggers no concrete earlier FoundationReopenCondition.**

---

# 84. MF7-E handoff

Next round should move from `what persists?` to `what remains unchanged / returns / resists perturbation under dynamics?`

Required topics:

```text
Invariant
Conserved Quantity
Symmetry
Equilibrium
Fixed Point
Steady State
Stationarity
Stability
Lyapunov Stability
Asymptotic Stability
Attractor
Basin
Limit Cycle
Metastability
Regime
Phase/Mode
Resilience
Robustness
Homeostasis
Hysteresis
Bifurcation
Critical Transition
```

Central attacks:

```text
Invariant ≠ Constant State
Conserved Quantity ≠ No Dynamics
Equilibrium ≠ Stability
Fixed Point ≠ Attractor
Steady State ≠ Equilibrium by universal identity
Stationary ≠ Static
Attractor ≠ Goal
Basin ≠ Reachability by identity
Stability ≠ Robustness ≠ Resilience
Homeostasis ≠ Static State
Metastable ≠ Stable Forever
Regime ≠ State
Phase/Mode ≠ Attractor
Bifurcation ≠ Random Jump
```

Central question:

> **What makes some features invariant/stable/regime-defining across a dynamical family, rather than merely unchanged along one observed trajectory?**

**Next: MF7-E — Invariants, Stability, Equilibria, Attractors & Regimes.**
