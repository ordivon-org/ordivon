---
schema_version: 1
id: game.deep-foundations.gdf1-f
title: Ordivon Game Deep Foundations — GDF1-F Final Falsification, Reconstruction & Survival Audit
profile: research
lifecycle: frozen
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: Final deletion/compression round over GDF1-A→E. Audits the research vocabulary into frozen core/guards, derived views, handoffs and retirements; freezes only six Action/Control/Skill responsibilities, rejects Embodiment and scalar Skill/floor/ceiling ontology inflation, defines eight reopen conditions, keeps R29/GDF0 unchanged, and hands the next dependency frontier to GDF2 Challenge / Difficulty / Failure / Mastery.
readiness: FROZEN_V1
applies_to:
  - ordivon-game
related:
  - game.action-control-skill-foundations.v1
  - game.play-game-deep-foundations.v1
---
# Ordivon Game Deep Foundations — GDF1-F

## 0. F is a deletion round

A→E deliberately overgenerated distinctions so they could be falsified.

F does the opposite:

```text
ResearchVocabulary != FrozenCore
```

Every surviving named candidate/guard receives exactly one disposition:

```text
freeze-core
freeze-guard
derived-model
handoff
retire
```

Canonical audit inputs:

```text
evidence/gdf1-f/survival-table.json
evidence/gdf1-f/handoff-map.json
scripts/gdf1-f/audit-freeze.mjs
```

The canonical frozen foundation is:

```text
docs/GAME_ACTION_CONTROL_SKILL_FOUNDATIONS_V1.md
```

---

# 1. Final attack on GDF1's own favorite constructs

F first attacks the constructs that GDF1 itself had become attached to.

## ActionCouplingProfile

Useful? Yes.

Foundational core? No.

Everything inside it unfolds into:

```text
entities/states/relations
observation/sensing
ControlMapping
ControlLocus
constraint/dynamics
collision/vulnerability consequence
```

and it is nearly empty in symbolic forms.

Disposition:

```text
DERIVED MODEL.
```

## ControlContributionTopology

Useful for RTS/shared/assist control, but not universally instantiated as a named object.

Its frozen content is the guard:

```text
Joint outcome requires correct controller attribution.
```

Disposition:

```text
DERIVED MODEL.
```

## EvaluationCommitmentSet

Essential as a currentness/provenance rule for open-ended skill relevance, but much of its ontology already exists in GDF0 evaluation/authority foundations.

Disposition:

```text
FREEZE GUARD / evidence contract,
not new core ontology.
```

## TechniqueFamily

Useful in racing/fighting/sports/speedrunning; unnecessary in chess/RTS/sandbox.

Disposition:

```text
DERIVED MODEL.
```

## EntryRequirementRegion / SkillExpressionEnvelope / SaturationAttribution

Real and useful, but their main explanatory burden is Challenge/Difficulty/Mastery.

Disposition:

```text
HANDOFF GDF2.
```

GDF1 retains only:

```text
Capability != Expression
ObservedPlateau != SkillCeiling
```

as anti-collapse guards.

---

# 2. Final frozen core — only six responsibilities

F finds that all tested forms can be covered by a six-responsibility core.

```text
1. GameActionContract
2. ControlMapping
3. ControlLocus
4. SkillProfile
5. SkillRelevantVariableSet
6. ProbeTransformation
```

No seventh core object earns necessity.

---

# 3. Why GameActionContract survives

Across:

```text
button input
analog control
RTS command
turn-based symbolic action
shared assistance
remote control
```

Game needs a stable semantic distinction between:

```text
input/control evidence
action attempt/admission
executed GameAction
world/task consequence
```

Therefore the deep A separation survives not as seven permanent object classes, but as one frozen GameAction responsibility plus anti-collapse laws.

---

# 4. Why ControlMapping survives

Accessibility and remapping repeatedly demonstrate that:

```text
physical expression
```

can change while:

```text
GameAction semantics
```

remain fixed.

Conversely, context can change GameAction meaning while the raw input token stays identical.

So Game needs a current, provenance/version-bound mapping relation.

No specific device vocabulary is frozen.

---

# 5. Why ControlLocus survives

Control locus crosses:

```text
avatar
vehicle
cursor
piece
RTS squad
remote tool
symbolic policy surface
```

while avoiding the failures of `body`, `avatar` and `self-location` as universal action loci.

Thus it earns core status.

---

# 6. Why SkillProfile survives

This is GDF1's most successful reconstruction.

It survived:

```text
motor-heavy skill
symbolic chess
RTS
open practice
assistance
synthetic controllers
remapping
retention/transfer pressure
```

because it makes a weak but falsifiable claim:

> Skill is a learned history-dependent conditional capability profile under a declared scope, not one observed performance or universal scalar.

It does not choose Human mechanisms.

---

# 7. Why SRVS survives

Without SkillRelevantVariableSet, SkillProfile becomes an arbitrary bag of metrics.

Without dynamic/provenance-bound evaluation commitments, SRVS collapses in open sandbox/creative practice.

Without causal/evaluative admission, post-hoc expert correlations can define Skill circularly.

Therefore SRVS earns core responsibility while EvaluationCommitment remains a frozen evidence/authority guard.

---

# 8. Why ProbeTransformation survives

Every serious claim of:

```text
transfer
retention
remapping
perturbation
adaptation
assistance change
```

requires knowing what changed and what stayed fixed.

This is true for motor, strategic, accessibility and synthetic control cases alike.

Thus ProbeTransformation earns core status as an evidence relation.

---

# 9. What F refuses to freeze

F specifically rejects ontology inflation from the research history.

```text
SkillState
→ RETIRE.

Embodiment as one construct
→ RETIRE.

ExperientialEmbodimentProfile as one score
→ RETIRE.

EvaluationTargetSet
→ RETIRE / replaced.

TaskRelevantVariableSet as general ontology
→ RETIRE / replaced by SRVS.

TechniqueFamily
→ DERIVED.

ActionCouplingProfile
→ DERIVED.

ControlContributionTopology
→ DERIVED.

ControlAccessProfile
→ DERIVED.

EntryRequirementRegion
SkillExpressionEnvelope
SaturationAttribution
→ GDF2 HANDOFF.
```

---

# 10. Final skill evidence architecture

The frozen relationship is intentionally small:

```text
GameStructure / Practice / Current Evaluation Commitments
                  │
                  ▼
        SkillRelevantVariableSet
                  ▲
                  │
GameActionContract + ControlMapping + ControlLocus
                  │
                  ▼
          Performance Evidence
                  │
        exact provenance/condition
                  │
                  ▼
         ProbeTransformation
                  │
            history across probes
                  ▼
             SkillProfile
```

When control is distributed, derived contribution attribution is added.
When body/tool structure matters, derived action coupling is added.
Neither is mandatory core.

---

# 11. Final body/embodiment reconstruction

E's evidence survives F only as guards and derived roles.

There is no frozen Game entity named:

```text
Embodiment
StructuralBody
EmbodiedAgent
```

Instead Game may project exact relations such as:

```text
ControlLocus
sensor/effector availability
morphology/reach
collision/passability
vulnerability/consequence
tool/vehicle dynamics
```

when they causally matter.

Human owns:

```text
BodyOwnership
SenseOfAgency
SelfLocation
BodySchema
PeripersonalSpace
```

Media owns avatar/body representation.

This is sufficient for all E cases without adding a primitive.

---

# 12. Final control attribution reconstruction

F also rejects a combinatorial ontology of:

```text
HumanSkillProfile
SystemSkillProfile
JointSkillProfile
Human+AssistA+AssistB SkillProfile...
```

Instead:

```text
SkillProfile
+
attribution target identity
+
when needed, sparse ControlContributionTopology
```

handles the distinction.

Frozen guard:

```text
JointControllerPerformance
!= HumanIndependentSkill
!= SystemIndependentSkill.
```

---

# 13. Final owner boundary

## Frozen Game responsibility

```text
semantic GameAction
mapping/locus of authoritative control
skill evidence scope/relevance/transformation
Game-authoritative structural consequences
```

## Not Game foundation ownership

```text
neural motor control
motor memory/body schema
ownership/agency/self-location
avatar rendering/perceptual encoding
physical-world body mechanics
```

Game can consume those domains without absorbing them.

---

# 14. Final novelty ledger

GDF1 has earned no N3 scientific novelty.

```text
N3 = NONE
N2 = NONE
```

The strongest value remains N1 integration/reconstruction:

```text
non-scalar SkillProfile
SRVS with current evaluation provenance
ProbeTransformation discipline
GameAction/control/body target separation
conditional sparse action-coupling view
challenge/ceiling handoff discipline
```

Independent integration is not promoted to scientific novelty.

---

# 15. Foundation audit

A→F has pressured R21/F1–F9/GDF0 with much deeper mechanism and cross-GameForm cases than were available at initial freeze.

No contradiction requires a new semantic primitive.

Therefore:

```text
R29 FoundationReopenCondition = NOT TRIGGERED
GDF0 PRC-7 = NOT TRIGGERED
```

GDF1 defines its own explicit ACS-PRC-1→8 conditions in the frozen v1.

---

# 16. Dependency verdict

The next branch is now no longer ambiguous.

GDF1 has given us a serious model of capability and its expression conditions.

The largest unresolved upstream question is now:

> Given a SkillProfile, what makes a situation challenging, difficult, recoverable, learnable, punishing or mastery-bearing for a particular participant/controller under current conditions?

Therefore:

# **GDF2 — Challenge / Difficulty / Failure / Mastery**

is the exact next deep branch.

It receives:

```text
SkillProfile
SRVS
Capability != Expression
EntryRequirementRegion
SkillExpressionEnvelope
SaturationAttribution
AssistanceTimescaleSeparation
```

rather than reinventing Skill.

---

# 17. Freeze verdict

```text
GDF1-A→F = COMPLETE

Action / Control / Skill Foundations v1 = FROZEN

core responsibilities = 6

GameActionContract
ControlMapping
ControlLocus
SkillProfile
SkillRelevantVariableSet
ProbeTransformation

Embodiment single construct = REJECTED
TechniqueFamily = DERIVED
ActionCouplingProfile = DERIVED
ControlContributionTopology = DERIVED
Skill floor/ceiling/challenge constructs = GDF2 HANDOFF
Human motor + ownership/agency/self-location = HANDOFF Human
Avatar/body representation = HANDOFF Media

R1–R29/F1–F9 unchanged
GDF0 unchanged

next = GDF2 Challenge / Difficulty / Failure / Mastery
```
