---
schema_version: 1
id: game.post-gpr-domain-coverage.c7-gamestructure-lineage-versioning
title: Ordivon Game — Fresh Coverage C7: GameStructure Lineage / Versioning / Semantic Migration Falsification
profile: research
lifecycle: active
source_role: research
visibility: public
owners:
  - ordivon-game
updated: 2026-08-18
summary: Fresh post-GPR destructive pass over GameStructure lineage, version labels, patches, hotfixes, forks, compatibility, persistent-state migration and identity-preserving versus identity-splitting change. Cross-regime cases show that artifact version, rules representation version, effective semantic currentness, practice/category lineage, persistent entity/world continuity and GameInstance continuity are independent dimensions. After subtracting R13/R24 generic identity/history/lineage, R28 cultural transmission/recognition, GDF0 rule mutability/EffectiveRuleTopology/practice-category continuity, GPR1/GPR3 authority/adoption/currentness, C5 runtime change tracing and C1 ConstitutionBasisAndCurrentness/InstanceContinuityBoundary, no independent Game foundation responsibility survives. A GameStructureLineageView / SemanticMigrationDiagnostic remains a strong practical/research abstraction and becomes an explicit upstream input family for C1 rather than a separate foundation. No GDF4/GPR8 or engineering route is admitted.
evidence_status: strong-local
readiness: C7_REDUCED_NO_NEW_FOUNDATION_ROUTE_NOT_SELECTED
applies_to:
  - ordivon-game
related:
  - game.play-game-deep-foundations.v1
  - game.post-gpr-domain-coverage.c1-instance-constitution
  - game.post-gpr-domain-coverage.c5-adaptive-experience-management
  - game.post-gpr-domain-coverage.c6-meta-practice-extended-apparatus
---
# Ordivon Game — Fresh Coverage C7: GameStructure Lineage / Versioning / Semantic Migration Falsification

## 0. Boundary

This is not GDF4 and not GPR8.

C7 attacks the narrower residual isolated by C6:

```text
artifact version
effective semantic version
practice/category lineage
patch/hotfix applicability
branch/fork
compatibility
persistent world/entity migration
ongoing-instance migration
season/currentness interval
identity-preserving vs identity-splitting change
```

The null model is:

```text
C7
= R13 history/persistence
+ R24 identity/continuity/branching/provenance
+ R28 cultural/practice lineage and recognition
+ GDF0 rule mutability / EffectiveRuleTopology / PlayPractice / GameCategory
+ GPR1 change authority
+ GPR3 adoption/currentness/provenance
+ C5 applied-change tracing
+ C1 ConstitutionBasisAndCurrentness / InstanceContinuityBoundary.
```

C7 must show that GameStructure lineage itself needs a new irreducible responsibility, not merely that current games are patched or that persistent worlds can be migrated.

---

# 1. Candidate deletion pass

## Version primitive

`Version` may mean:

```text
client build
server build
rules document revision
practice rules revision
content release
season identifier
save/world format
protocol version
marketing edition label
```

Delete universal primitive.

## SemanticVersion primitive

A single scalar semantic version is insufficient because effective semantics can be assembled from multiple current sources and scoped overlays.
Delete.

## Patch primitive

Patch is an implementation/publication/change carrier, not the semantic effect itself.
Delete.

## Hotfix primitive

Hotfix differs operationally from full patch but not in Game ontology; its significance lies in effective change/currentness.
Delete.

## Fork primitive as Game-specific kind

Branch/fork is generic lineage structure already covered by R24 identity/provenance.
Delete Game-specific primitive.

## Compatibility primitive

Compatibility is question-relative:

```text
save-load compatibility
rules interoperability
character legality
network/protocol compatibility
content compatibility
comparison compatibility
```

Delete universal boolean.

## Migration primitive

Migration is a transformation workflow preserving selected continuity claims under a mapping; it occurs across many domains.
Delete Game primitive.

## Season primitive

Season may be a competition interval, content cycle, rules-currentness scope or reset boundary.
Delete universal target.

## Legacy primitive

`Legacy` is owner/practice classification, not ontology.
Delete.

---

# 2. Falsifier A — version label can change with zero semantic change

## C7-F1 — D&D 5e / 5.5e labeling clarification

A 2026 editor note on the official Adventurers League 2024-rules migration article states that D&D Beyond now labels the updated rules `5.5e` and the 2014 content `5e`, while explicitly treating that relabeling as a clarity change rather than a rules/gameplay change.

Therefore:

```text
VersionLabelChange
!= SemanticGameChangeByIdentity.
```

Delete label-based identity.

---

# 3. Falsifier B — same client patch can have changing effective semantics

## C7-F2 — World of Warcraft hotfix activation

Current WoW hotfix documentation states that some hotfixes take effect immediately, some require scheduled realm restarts and some changes require a client-side patch.

Thus:

```text
ClientBuildVersion
!= EffectiveSemanticCurrentnessByIdentity.
```

The same client artifact can encounter different server-side effective behavior before/after a hotfix activation boundary.

This reduces to:

```text
change representation
+ applied change
+ activation/currentness
```

already covered by GDF0/GPR3/C5.

---

# 4. Falsifier C — patch name does not uniquely determine semantics over time

## C7-F3 — cumulative hotfix stream

WoW maintains dated hotfix changes against a broader release/patch family.

Therefore:

```text
PatchLabel
!= CompleteEffectiveGameStructureSnapshot.
```

A useful exact query needs `asOf/currentness` and applied-change provenance.

---

# 5. Falsifier D — rules-document version is independent from game/software version

## C7-F4 — Riot competitive rules revisions

Riot Competitive Operations publishes independently versioned and dated competition rulebooks and event-specific rulesets, with multiple revisions inside one competitive year.

Therefore:

```text
CompetitionRulebookVersion
!= ClientGamePatchVersionByIdentity.
```

A concrete esports GameInstance can consume both a software/game version and a current competition-practice rules revision.

GDF0's EffectiveRuleTopology already allows this multi-source constitution.

---

# 6. Falsifier E — effective semantics can be assembled from multiple publication generations

## C7-F5 — Adventurers League mixed-rule migration

During the D&D 2024/5.5e migration, Adventurers League instructed tables to use updated rules where released while retaining the most recent older version of options not yet updated.

Therefore:

```text
EffectiveRuleTopology
!= OnePublicationVersionByIdentity.
```

The live practice can be a scoped composition of current rules from different publication generations.

This strongly rejects a single `semanticVersion` scalar as foundation truth.

---

# 7. Falsifier F — persistent character continuity survives rules migration

## C7-F6 — Adventurers League character update window

Adventurers League allowed existing characters to be rebuilt/migrated to the updated rules, with a grace period after which applicable character options had to use the new rules.

Thus:

```text
PersistentCharacterContinuity
!= RuleVersionIdentity.
```

and:

```text
RuleMigration
!= CharacterReplacementByIdentity.
```

R24 already owns identity continuity and migration; GDF0 owns current rules.

---

# 8. Falsifier G — migration can preserve some state while transforming other state

## C7-F7 — D&D migration is selective

The same organized-play migration allowed some character rebuilding while explicitly preserving or constraining other historically acquired state, such as treasure/items, under separate rules.

Therefore:

```text
Migration
!= FullStateRewrite
!= FullStatePreservation.
```

A migration is a scoped transformation contract over selected state/evidence/rights.

This is generic transformation/provenance plus owner-local Game semantics, not a new primitive.

---

# 9. Falsifier H — persistent world migration can be spatially/history heterogeneous

## C7-F8 — Minecraft existing-world upgrade

Official Minecraft world-upgrade material for Caves & Cliffs Part II describes existing worlds being updated to new height/depth semantics while preserving existing world regions/chunks and adding/generated space under the new world-generation regime.

Therefore:

```text
SamePersistentWorld
!= HomogeneousSingleGenerationVersionEverywhere.
```

and:

```text
WorldContinuity
can coexist with partial/region-specific migration.
```

World/history owns persistent state; Game current rules govern future generation/interaction.

---

# 10. Falsifier I — save/world-format migration is not GameStructure identity

## C7-F9 — world upgrade mechanism

A world may require data-format/transformation work to remain loadable under a new runtime while the recognized GamePractice/GameCategory remains continuous.

Thus:

```text
SaveFormatVersion
!= GameStructureIdentityByIdentity.
```

Runtime owns serialization/format mechanics; Game owns only semantic consequences of the migrated state.

---

# 11. Falsifier J — shared source lineage does not imply same current GameStructure

## C7-F10 — World of Warcraft Classic branch reconstruction

Blizzard's Classic retrospective documents historical source/data/art assets and separate code branches used to reconstruct Classic gameplay on modern infrastructure.

The modern game and Classic share historical provenance but are maintained as distinct current practices/products.

Therefore:

```text
SharedHistoricalSource
!= SameCurrentGameStructureByIdentity.
```

This is ordinary branch-aware lineage, consistent with R24:

```text
SharedPast != SharedNumericalIdentity after fork.
```

---

# 12. Falsifier K — different implementations can realize a recognized historical GameStructure

## C7-F11 — Classic gameplay on modern code

The Classic reconstruction used classic data/art with modernized technical infrastructure/code to reproduce the intended classic gameplay experience.

Therefore:

```text
ImplementationCodeIdentity
!= GameStructureOrPracticeIdentityByIdentity.
```

This reinforces:

```text
GameArtifact != CompleteGameStructure.
```

Lineage must be semantic/practice-aware, not build-hash identity.

---

# 13. Falsifier L — compatibility does not imply identity

## C7-F12 — D&D 5e / 5.5e compatibility

The current official labeling note states that both rule versions remain supported and compatible while still distinguishing them as different labeled rules generations.

Therefore:

```text
Compatible(A,B)
!= Identical(A,B).
```

Compatibility is a relation for a declared operation/scope, not identity evidence.

---

# 14. Falsifier M — incompatibility does not imply referent replacement

## C7-F13 — required character conversion

An old character representation can become non-current/non-legal under updated organized-play rules until rebuilt, while the practice still treats the migrated result as continuation of the character.

Therefore:

```text
RepresentationIncompatibility
!= EntityIdentityBreakByIdentity.
```

Identity authority and migration mapping remain separate.

---

# 15. Falsifier N — currentness is practice/scope-relative

## C7-F14 — D&D general support vs Adventurers League current rule

The broader D&D ecosystem can continue supporting older and newer rules labels while Adventurers League adopts a specific current-rule policy for organized play.

Thus:

```text
GloballyAvailableVersion
!= CurrentEffectiveVersionForPractice.
```

GDF0 currentness is scope/practice-relative, exactly as needed.

---

# 16. Falsifier O — published source availability does not mean immediate currentness

## C7-F15 — organized-play adoption timing

D&D organized-play updates explicitly govern when newly released options are legal in specific campaigns/practices.

Therefore:

```text
ArtifactPublicationTime
!= PracticeEffectiveTimeByIdentity.
```

This is GPR3 adoption/currentness + GDF0 EffectiveRuleTopology.

---

# 17. Falsifier P — ongoing GameInstance migration is owner-local, not inferred from patch

## C7-F16 — structure change vs current instance

Consider an authorized rule/hotfix change while GameInstances already exist.
Possible owner-local policies include:

```text
apply immediately to running instances
apply at next phase/checkpoint
apply only to newly constituted instances
invalidate/restart affected instances
allow old and new cohorts concurrently.
```

Therefore:

```text
StructureVersionChange
!= GameInstanceContinuityDispositionByIdentity.
```

This is exactly C1's `InstanceContinuityBoundary` consuming a changed `ConstitutionBasisAndCurrentness`.

C7 does not need a separate instance-migration foundation.

---

# 18. Falsifier Q — same GameInstance can remain continuous through rule change when practice says so

## C7-F17 — mutable effective rules

GDF0 already freezes that stable rule content is not necessary for historical/practice continuity and rule mutability is compatible with GameStructure when authority/currentness remain resolvable.

Thus:

```text
RuleContentChange
!= InstanceOrPracticeReplacementByIdentity.
```

Whether a particular instance survives is C1 owner-local continuity semantics.

---

# 19. Falsifier R — a small overlay can split practice/category without large version delta

## C7-F18 — category split

GDF0 explicitly allows a small practice overlay to create a distinct recognized category.

Therefore:

```text
SemanticDeltaMagnitude
!= IdentitySplitThresholdByIdentity.
```

There is no universal semver-like major/minor rule for Game identity.

---

# 20. Falsifier S — large mechanical change can preserve recognized lineage

## C7-F19 — bounded recognized transformation

Conversely, substantial rule/content transformation can remain within a recognized historical lineage when the relevant practice/community treats it as continuation.

Therefore:

```text
LargeMechanicalDelta
!= IdentityBreakByIdentity.
```

GDF0/R28 already own recognized practice/category continuity.

---

# 21. Falsifier T — branch/fork creates provenance relation, not automatic merge semantics

## C7-F20 — divergent maintained branches

After a fork, two descendants may share historical source while accepting different future changes.

Therefore:

```text
CommonAncestor
!= MutualPatchApplicability
!= MergeabilityByIdentity.
```

Any later adoption/cherry-pick/translation must be an explicit mapping/current adoption decision.

Generic lineage + GPR3 adoption are sufficient.

---

# 22. Falsifier U — semantic adoption can be selective rather than whole-version merge

## C7-F21 — partial rule-source adoption

A practice can adopt one updated rule/option while retaining older semantics for another not-yet-updated source.

Therefore:

```text
Adoption
!= WholeVersionReplacementNecessity.
```

The correct foundation object is the current EffectiveRuleTopology assembled from authoritative sources, not a Git-like merged version object.

---

# 23. Falsifier V — season/version boundary need not reset persistent identity

## C7-F22 — season/currentness interval

A new season can change competition rules/content/rank state while preserving:

```text
player identity
account identity
character/world history
practice/category lineage.
```

Therefore:

```text
SeasonBoundary
!= UniversalIdentityReset.
```

Season is a scoped temporal/practice marker, not a foundation primitive.

---

# 24. What survives subtraction

C7 leaves a strong practical/research family:

```text
GameStructureLineageView
SemanticMigrationDiagnostic
```

A useful lineage view may expose:

```text
structureRef / practiceRef
sourceRepresentationRefs
predecessor / successor / fork provenance
adoption/currentness intervals
change/patch refs
scope of effective semantic change
compatibility claims by operation/scope
migration mappings
preserved / transformed / dropped state classes
instance applicability policy
category/practice continuity claims
identity authority / recognition refs
provenance/evidence
```

A useful migration diagnostic asks:

```text
What changed semantically?
What only changed representation/label/build?
Which source became authoritative/current?
Which persistent state must migrate?
Which state must not migrate?
Which old/new versions may coexist?
Which running GameInstances are affected?
Does each affected instance continue/restart/end?
Which practice/category identity claims remain recognized?
```

---

# 25. Core anti-collapse laws

```text
VersionLabel != SemanticChange
ClientBuildVersion != EffectiveSemanticCurrentness
PatchLabel != CompleteEffectiveGameStructure
RulebookVersion != GamePatchVersion
EffectiveRuleTopology != OnePublicationVersion
PersistentEntityContinuity != RuleVersionIdentity
Migration != FullRewrite != FullPreservation
SaveFormatVersion != GameStructureIdentity
SharedHistoricalSource != SameCurrentGameStructure
ImplementationIdentity != PracticeIdentity
Compatibility != Identity
Incompatibility != IdentityBreak
ArtifactPublicationTime != PracticeEffectiveTime
StructureVersionChange != InstanceContinuityDisposition
SemanticDeltaMagnitude != IdentitySplitThreshold
CommonAncestor != MutualPatchApplicability
Adoption != WholeVersionReplacement
SeasonBoundary != IdentityReset
```

---

# 26. Why no independent Game foundation responsibility survives

The apparent C7 obligation can be decomposed completely:

```text
Generic predecessor/successor/fork identity
→ R24

History/provenance of state
→ R13/R24

Cultural/practice lineage recognition
→ R28 + GDF0 GameCategory/PlayPractice

Current effective semantic composition
→ GDF0 EffectiveRuleTopology

Change/adoption authority/currentness
→ GPR1/GPR3

Applied adaptive/runtime change trace
→ C5

Persistent entity/world migration
→ R24 + World/Runtime owner-local mapping

Effect on concrete GameInstance constitution/continuity
→ C1.
```

The remaining Game-specific question is not an independent lineage primitive. It is:

```text
which current GameStructure basis applies to this GameInstance,
and what does a basis change do to instance continuity?
```

That is already the center of C1's surviving responsibility.

Therefore:

```text
C7 independent Game foundation responsibility
= DOES NOT SURVIVE SUBTRACTION.
```

---

# 27. C7 materially strengthens C1

C1 already requires:

```text
ConstitutionBasisAndCurrentness
```

C7 now establishes that this basis cannot be represented by a single version string/hash.

It may need to consume a lineage/currentness projection over:

```text
artifact/source refs
practice overlays
adopted rule revisions
hotfix/currentness boundaries
migration status
```

while remaining agnostic to the generic mechanics of software version control.

Thus:

```text
C7
= upstream lineage/currentness diagnostic input to C1
not independent downstream foundation.
```

---

# 28. Ownership boundary

## Game owns

```text
which current semantic/rule composition is effective
which migration transformations have Game meaning
which version differences affect legal action/evaluation/instance constitution
practice/category continuity claims where Game-relative
```

## Runtime / software delivery owns

```text
client/server builds
serialization formats
binary patching
protocol compatibility
deployment/realm restart mechanics
```

## World owns

```text
persistent world state and physical causal state
```

## Social/Cultural/Institutional owns

```text
recognition of practice/category lineage
institutional adoption/currentness policies
```

## Generic identity/history owns

```text
predecessor/successor/fork/provenance structure
```

## C1 owns

```text
concrete GameInstance basis/currentness and continuity consequence.
```

---

# 29. Practical reconstruction verdict

C7 has a strong practical consumer story. Complex Game systems need to answer:

```text
Which rules actually applied to this run/match/world?
Did a hotfix change semantics without a client patch?
Which rulebook revision was current for this tournament?
Was this character/world migrated or replaced?
Which state was preserved/transformed?
Can old/new versions coexist?
Did an existing GameInstance continue across the change?
```

So:

```text
GameStructureLineageView
SemanticMigrationDiagnostic
```

are high-value future derived contracts.

But current evidence does not justify a generic canonical lineage database or a new GPR cluster.

Verdict:

```text
strong practical/research gap = YES
GPR admission                = NO
new Game foundation          = NO
engineering route            = NOT YET PROVEN
```

---

# 30. Agent-era result

Agent-generated rules/content and autonomous live operation increase the frequency of:

```text
micro-patches
branching variants
per-instance overlays
rapid migrations
selective adoption
```

but they do not create an Agent-specific version/lineage primitive.

They make exact:

```text
provenance
scope
currentness
authority
migration mapping
```

more important.

GDF0/GPR1/GPR3/C1 remain sufficient.

---

# 31. Foundation reopen audit

```text
R1-R29 / F1-F9 = NOT REOPENED
GDF0            = NOT REOPENED
GDF1            = NOT REOPENED
GDF2            = NOT REOPENED
GDF3            = NOT REOPENED
```

Especially:

```text
GDF0 PRC-3 Rule/authority failure = NOT TRIGGERED
```

because all effective-version cases remain representable through EffectiveRuleTopology + authority/currentness.

And:

```text
GDF0 PRC-5 Category/mechanism failure = NOT TRIGGERED
```

because branch/version cases strengthen the distinction between mechanical delta and recognized category identity.

No Agent-era primitive is required.

---

# 32. C7 final classification

```text
C7 destructive pass = COMPLETE

Version primitive          = REJECTED
SemanticVersion primitive  = REJECTED
Patch primitive            = REJECTED
Hotfix primitive           = REJECTED
Game-specific Fork         = REJECTED
Universal Compatibility    = REJECTED
Migration primitive        = REJECTED
Season primitive           = REJECTED
Legacy primitive           = REJECTED

GameStructureLineageView / SemanticMigrationDiagnostic
= STRONG USEFUL PRACTICAL/RESEARCH ABSTRACTION

Independent Game foundation responsibility
= DOES NOT SURVIVE SUBTRACTION

C7 classification
= STRONG PRACTICAL/DIAGNOSTIC GAP
  + GENERIC IDENTITY/HISTORY + GDF0 CURRENTNESS/ADOPTION
  + UPSTREAM INPUT TO C1 CONSTITUTION/CONTINUITY
  + NOT GENUINELY NEW GAME FOUNDATION
  + NOT ROUTE SELECTED
```

---

# 33. Relative update after C1-C7

```text
C1 GameInstance Constitution / Continuity
= SURVIVES as strong Game-owned downstream foundation candidate

C2 Evaluation / Comparability
= REDUCED

C3 Dynamics / Emergence
= REDUCED

C4 Population / Matching
= REDUCED

C5 Adaptive Experience Management
= REDUCED

C6 Meta-practice / Extended Apparatus
= REDUCED

C7 GameStructure Lineage / Versioning
= REDUCED into generic lineage/currentness + C1 upstream input
```

C1 is now the only survivor among seven tested candidates.

Integrity / cheating / exploit and active unknown-continent search remain before any survivor-selection round.

---

# 34. External evidence anchors

Representative current/direct-practice anchors used as falsifiers:

```text
D&D Beyond / Adventurers League — 2024 core-rules migration article, including the 2026 5e/5.5e labeling clarification, current-rule adoption policy, 60-day character migration window and mixed old/new option guidance.
World of Warcraft — current 2026 hotfix notes distinguishing immediate activation, realm-restart activation and client-side patch requirements.
Riot Games Competitive Operations — 2026 library with independently revisioned/date-scoped LoL competition rulebooks and event-specific rulesets.
Minecraft official Feedback/FAQ — Caves & Cliffs Part II existing-world upgrade and mixed persisted/newly generated world-region behavior.
Blizzard World of Warcraft Classic retrospective — historical source/data branches and use of modern technical infrastructure to reproduce Classic gameplay.
```

These are falsifier/evidence anchors, not Ordivon ontology authorities.

---

# 35. Frontier after C7

```text
C1 GameInstance Constitution / Continuity
= strong foundation-unclosed candidate

C2-C7
= reduced under destructive subtraction

Integrity / cheating / exploit
= unresolved cross-cutting candidate

unknown continents
= OPEN
```

Still:

```text
NextGPR            = UNKNOWN
NextPracticalRoute = UNKNOWN
NextFoundation     = UNKNOWN
```
