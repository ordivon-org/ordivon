---
schema_version: 1
id: game.deep-foundations.gdf0-d
title: Ordivon Game Deep Foundations — GDF0-D Cross-Context Falsification
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: Cross-context falsification of GDF0-C mechanisms across animal/free play, sandbox, mastery, professional/high-stakes play, work/training/science/art/ritual, community rule practices and Agent-era dynamic-rule systems. Demotes AgencySculpting and DynamicEvaluationTopology as Game-specific discriminators while retaining them as domain-general mechanisms, strengthens EvaluationLayering and EffectiveRuleTopology, and shifts the search for Game-specificity toward configuration-level coupling rather than one hidden Game atom.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf0-a
  - game.deep-foundations.gdf0-b
  - game.deep-foundations.gdf0-c
  - game.foundations-research.r29
---
# Ordivon Game Deep Foundations — GDF0-D

## 0. Question

GDF0-C constructed minimal mechanism families:

```text
P process/local valuation
F frame + evaluation layering
S agency scaffold / effective rules
E exploration / learning progress
R perturbation / recovery
A agency sculpting / policy differentiation
```

D asks the question C intentionally deferred:

> Which of these mechanisms remain Game-specific when we pressure them against the closest non-game neighbours?

The round is adversarial. A mechanism that appears just as strongly in work, training, ritual, science or art cannot explain Game identity merely because it is useful in Game design.

Canonical machine-readable research matrix:

```text
evidence/gdf0-d/cross-context-matrix.json
scripts/gdf0-d/audit-cross-context.mjs
```

The matrix is qualitative research judgement. The audit script makes completeness and counterexample accounting reproducible; it does not turn qualitative coding into objective truth.

---

# 1. Cross-context corpus

D pressures the models across:

```text
animal social play
free pretend play
open Minecraft-like sandbox
casual formal game
professional esport
high-stakes gambling
speedrunning/community rule overlays
training drill
scientific experimentation
artistic improvisation
ritual
gamified work
AI dynamic-rule game execution
Agent-based rule balancing / production
```

The important design is not breadth for its own sake. Each non-game case is chosen because it is a **nearest structural neighbour** of a C mechanism.

---

# 2. D1 — AgencySculpting / PolicyDifferentiation fails Game-specificity

C operationalized context-sensitive action structure through:

```text
AdaptivePolicyGain =
E_c[max_a Q(c,a)] - max_a E_c[Q(c,a)]
```

This remains useful. D rejects the stronger interpretation.

## 2.1 Nearest-neighbour attack

High context sensitivity also exists in:

```text
medical/professional decision procedures
scientific experimentation
adaptive training
engineering/control work
artistic improvisation
```

These activities can require:

```text
context-dependent observation
non-dominated action alternatives
conditional policy
feedback
learning
error correction
```

without becoming Games.

Therefore:

```text
High PolicyDifferentiation
!= Game

High AdaptivePolicyGain
!= Ludicness
```

## 2.2 What survives

AgencySculpting remains an excellent **action-problem design mechanism**:

```text
Does context matter?
Does information matter?
Do different policies lead to different consequences?
Are choices dominated/decorative?
Can the participant learn the distinctions?
```

That is highly valuable to Game, training, tools and other interactive systems alike.

## 2.3 Status change

```text
C5 AgencySculpting:
  Game-specific candidate → DEMOTED
  domain-general action-problem mechanism → RETAIN
  Game design falsifier → RETAIN strongly

C8 PolicyDifferentiation / AdaptivePolicyGain:
  candidate Game-science novelty → DEMOTED
  operational structural probe → RETAIN
```

The mathematics was already ordinary decision theory; D removes the remaining temptation to treat its Game use as category-specific novelty.

---

# 3. D2 — DynamicEvaluationTopology survives only as a general agency distinction

C established:

```text
NoFixedGlobalGoal != NoEvaluation
```

D strongly retains that separation.

## 3.1 Open sandbox pressure

Minecraft has been used experimentally precisely because its traditional sandbox form does not impose one specific correct goal or way to play. Experimental conditions can then add directed building/exploration or leave participants much freer.

This supports:

```text
absence of authored fixed terminal goal
!=
absence of participant-directed relevance/project structure
```

Free building, exploration and creative construction can be organized around temporary projects, aesthetic preference, curiosity, self-imposed challenges or social commitments.

## 3.2 Non-game pressure

But the same is true in:

```text
science
art
open-ended design
research
conversation
```

where local relevance and evaluation can be dynamic, plural and self-authored.

Therefore C9 cannot explain Game-specificity.

## 3.3 Important narrowing

For intentional policy:

```text
some relevance / preference / evaluation relation
is required to explain why one action is selected over another.
```

But that is a general agency fact, not a Game fact.

For animal/infant PlayBehavior where phenomenology and explicit intention are unavailable, D refuses to infer a hidden scalar goal merely from organized behavior.

## 3.4 Status

```text
C9 DynamicEvaluationTopology:
  NoFixedGoal distinction → RETAIN strongly
  Game-specific mechanism → REJECT
  general participant-policy coordinate → RETAIN
```

---

# 4. D3 — Exploration remains a subset; mastery pressure becomes stronger

C already falsified `Play = information gain` structurally.

D adds real-world pressure from long-horizon game practice.

Large-scale motor-learning research using a first-person-shooter scenario followed thousands of voluntary participants across hundreds of thousands of one-minute repetitions and found continued sensorimotor refinement over extended practice.

This does not measure world-model information gain directly, so D does **not** claim:

```text
information gain = zero.
```

It does strengthen the separability hypothesis:

```text
familiarity / repeated exposure can coexist with continuing performance refinement.
```

Professional/competitive game studies likewise find skill development, competition and social motives alongside career/extrinsic motives.

Therefore mature Play can draw value from mechanisms other than novelty:

```text
execution refinement
timing / precision
self-comparison
opponent adaptation
social competition
rhythm
expression
identity
```

D does not decide which dominates; those belong to later Skill/Challenge/Value foundations.

Status:

```text
E Exploration / LearningProgress:
  subset mechanism → RETAIN
  universal Play mechanism → REJECTED earlier, reinforced
```

---

# 5. D4 — Perturbation/Recovery is not Play-specific; social regulation is the interesting pressure

Animal play provides particularly useful falsification because it lacks authored formal GameStructure.

Wild chimpanzee research reports play-solicitation gestures and partner-sensitive self-handicapping; self-handicapping occurred more often toward younger recipients. Comparative social-play work also emphasizes role reversal, restraint and signals that prevent rough interaction from escalating into real aggression.

This strengthens R's narrow mechanism:

```text
play can contain deliberately modified control,
self-handicap and recoverable perturbation.
```

But athletic drills, emergency training and rehabilitation can deliberately instantiate the same perturbation/recovery dynamics.

Therefore:

```text
PerturbationRecovery != Play
```

The more interesting Play-specific pressure is not perturbation itself but how interaction is **regulated as play**:

```text
signals
reciprocity
self-restraint
role reversal
partner-sensitive intensity
continuation maintenance
```

These are strongest for social play and cannot automatically generalize to solitary/object/imaginative play.

Status:

```text
R-model:
  narrow mechanism → RETAIN
  Play discriminator → REJECT
  migrate to Skill / Challenge / Social Play foundations
```

---

# 6. D5 — EvaluationLayering and ConsequenceCoupling survive strongly

Professional esport is a high-value stress test because it can be simultaneously:

```text
GameParticipation
+ skilled performance
+ career/work
+ social identity
+ money/status competition
```

Empirical work on competitive gamers reports competition, skill-development and social motives alongside career planning and extrinsic incentives.

This supports B/C's separation:

```text
GameGoal
!= ParticipationPurpose
!= PlayerValue
!= ExternalStake
```

and:

```text
PlayFrame != ConsequenceIsolation
```

Gambling provides the extreme conceptual case: a local game structure can remain intact while economic consequence coupling becomes very high.

## 6.1 Stronger consequence model

D retains ConsequenceCoupling as a vector rather than one scalar:

```text
bodily
economic
social
reputational
identity
institutional/legal
knowledge/skill
```

Different external channels can strengthen independently.

## 6.2 What this does not prove

High external instrumentality does not prove that subjective PlayMode survives unchanged.

Motivational studies show game engagement can occur under very different motivational profiles with different subjective outcomes.

Therefore:

```text
GameStructure can remain stable
while PlayExperience changes materially.
```

This is direct support for C11 Structural/Experiential Dissociation in humans as well as Agents.

Status:

```text
C4 EvaluationLayering → STRENGTHENED N1 synthesis
ConsequenceCoupling → STRENGTHENED analytical coordinate
Neither is a Game-category discriminator alone.
```

---

# 7. D6 — Speedrunning strongly validates distributed rule authority

Speedrunning is an unusually clean test of:

```text
GameArtifact != CompleteGameStructure
```

Current Speedrun.com moderation guidance explicitly expects category rules to define timing boundaries and gameplay restrictions, and moderators/community feedback participate in category/rule organization.

Thus one base videogame artifact can support multiple distinct effective action problems:

```text
base artifact
+ category goal
+ allowed/disallowed techniques
+ timing semantics
+ version constraints
+ verification standards
→ one speedrun practice
```

The community can therefore create a new GamePractice / effective GameStructure without changing the executable game's basic code.

Strong law:

```text
EffectiveRuleTopology can be distributed across:
artifact + platform + community + participant + material/technical reality.
```

This substantially strengthens C0's coupled-factor form.

---

# 8. D7 — C0 survives because the factors really co-constitute one another

The earlier stack model was already rejected in B.

D provides more pressure for the coupled form:

```text
LudicConfiguration =
Behavior
× ParticipantMode
× Frame
× Practice
× EffectiveRuleTopology
× Artifact/Affordances
× Enactment
× ExternalCoupling
× CulturalCategory
```

Examples:

```text
speedrunning:
practice/community changes effective rules over a fixed artifact.

free sandbox:
participant projects alter local evaluation without changing base affordances.

professional esport:
external coupling changes while formal GameStructure remains recognizable.

gamified work:
overlay/frame/evaluation may alter experience while much of the underlying task remains identical.

animal social play:
interactional signals/frame-like regulation exists without a formal artifact.
```

Therefore the configuration is not merely descriptive convenience: different factors can vary somewhat independently and can causally modify the others.

But C0 still lacks a unique prediction that identifies GameCategory.

Status:

```text
C0 CoupledLudicConfiguration:
  working research framework → STRENGTHENED
  universal Game essence → NOT CLAIMED
  predictive theory → NOT YET SUFFICIENT
```

---

# 9. D8 — The crucial negative result: no current single mechanism is Game-specific

Cross-context pressure produces a very strong negative table:

```text
Process valuation
→ art/science/exercise also have it.

Frame / constitutive meaning
→ ritual/law/institution also have it.

AgencyScaffold
→ training/work/exam also have it.

Exploration / learning progress
→ science/research also have it.

Perturbation / recovery
→ training/rehabilitation also have it.

AgencySculpting / PolicyDifferentiation
→ professional decision/control tasks also have it.

Dynamic local evaluation
→ art/research/design also have it.
```

Therefore:

```text
NoCurrentSingleMechanism ⇒ GameIdentity
```

This is not a proof that no such mechanism can ever exist. It is a falsification result for the current candidate set.

---

# 10. Configuration-level specificity hypothesis

D now permits a stronger but still provisional inference:

> If Game has explanatory specificity beyond ordinary cultural labeling, it is more likely to arise from a **configuration of mechanisms and relations** than from one unique component.

Provisional form:

```text
GameLikeConfiguration ≈
AgencyScaffold
+ local/effective evaluation & rule authority
+ enactment/practice
+ participant relation to the scaffold
+ frame/category/history
+ characteristic consequence coupling
```

No conjunct is currently declared universally necessary in this exact form.

This hypothesis makes a useful prediction:

```text
Holding the underlying task mostly fixed,
changing frame/evaluation/practice can materially change experience/category;

holding the social category label fixed,
changing scaffold/rules/information can materially change gameplay.
```

Gamification studies where the underlying task remains the same while participants customize game elements supply partial pressure in the first direction: some participants report altered control/meaning/enjoyment, while others report that the task itself remains unchanged.

This is exactly why the hypothesis is **configuration-level** rather than `game elements magically create Game`.

Candidate:

```text
C12 ConfigurationLevelSpecificity = N1/N2 hypothesis candidate
```

It remains below N2 until D/E derive sharper interventions and category/experience predictions.

---

# 11. GameCategory after D

D increasingly supports a distinction between:

```text
mechanistic similarity
and
historical/cultural category identity.
```

A ritual, exam or work protocol may structurally resemble a Game without being culturally practiced as one.

A speedrun may be culturally recognized as a GamePractice even though much of its effective rule structure was added by community rather than original designer.

Therefore GameCategory may be partly:

```text
historical lineage
participant/community recognition
institutional naming
practice continuity
```

rather than a natural-kind boundary derivable from mechanics alone.

This is compatible with family-resemblance pressure but does **not** imply Game science is impossible.

Game science can still study:

```text
agency structures
challenge
skill
feedback
play-mode coupling
value mechanisms
social practice
rule authority
```

without pretending `game` must be one natural biological kind.

---

# 12. Agent-era pressure

## 12.1 Dynamic rules

`Baba is LLM` evaluates language models in Baba Is You, where rule statements are themselves manipulable game state. The reported difficulty around dynamic rule reasoning and use/mention distinctions is useful pressure for GDF0:

```text
RuleContent_t
RuleAuthority_t
RuleChangeAction
Currentness
Object-level action
Meta-level rule action
```

must remain distinguishable.

No new F1–F9 primitive is required; F4/F5/F6/F7/F9 already support these distinctions.

## 12.2 Production Agent vs Runtime player

RuleSmith uses multi-agent LLM self-play plus optimization to search rule/balance parameters in a design loop.

This is an Agent acting at the **production/meta-design locus**, not evidence that the shipped Game requires a runtime synthetic subject.

Strong law retained:

```text
ProductionAgentNeed != RuntimeAgentNeed
```

## 12.3 Structural/experiential dissociation

Synthetic game players can expose:

```text
rule comprehension
policy quality
strategy diversity
reachability
exploitability
```

while remaining silent on subjective PlayExperience.

D therefore strengthens rather than weakens C11.

---

# 13. Status changes after D

## Strengthened

```text
C0 CoupledLudicConfiguration
C4 EvaluationLayering
C11 Structural/Experiential Dissociation
EffectiveRuleTopology
ConsequenceCoupling
```

## Retained but narrowed/domain-general

```text
C5 AgencySculpting
C8 PolicyDifferentiation / AdaptivePolicyGain
C9 DynamicEvaluationTopology
E Exploration / LearningProgress
R Perturbation / Recovery
```

## Rejected as Game-specific discriminator

```text
AgencyScaffold alone
AgencySculpting alone
PolicyDifferentiation alone
DynamicEvaluation alone
Frame alone
ProcessValue alone
Exploration alone
Perturbation/Recovery alone
```

## New provisional synthesis

```text
C12 ConfigurationLevelSpecificity
```

Status:

```text
N1/N2 boundary
```

No N3 claim.

---

# 14. Discovery ledger after D

## N0 — external/rediscovered pressure

```text
- animal social play uses signalling, reciprocity and self-handicapping;
- sandbox games can lack predefined winning states/goals;
- long-horizon game practice can continue refining complex sensorimotor performance;
- professional gaming contains mixed intrinsic/extrinsic/career motives;
- speedrunning communities maintain category-specific effective rules;
- synthetic agents can execute/reason about dynamic rules without experiential evidence;
- Agent self-play can be used in production/design optimization.
```

## N1 — Ordivon synthesis retained/strengthened

```text
C0 CoupledLudicConfiguration
C3 ModelConflictProtocol
C4 EvaluationLayering
C6 AgencyScaffold as domain-general substrate
C7 MechanismFamilyView
C10 ProgressSeparation
C11 Structural/ExperientialDissociation
```

## N1 operational/domain-general

```text
C5 AgencySculpting
C8 PolicyDifferentiation / AdaptivePolicyGain
C9 DynamicEvaluationTopology
```

D explicitly removes Game-specific novelty pressure from these.

## N1/N2 hypothesis candidate

```text
C12 ConfigurationLevelSpecificity
```

## N3

```text
NONE
```

---

# 15. Machine-readable audit result

Running:

```text
node scripts/gdf0-d/audit-cross-context.mjs
```

must show explicit non-game/play counterpressure for every C mechanism that had tempted category-specific interpretation.

The intended conclusion is negative but useful:

```text
single-mechanism Game specificity was not earned.
```

This protects later GDF rounds from rebuilding a new AgentWorld-like ontology around `Agency` simply because it is elegant.

---

# 16. FoundationReopenCondition audit

D still requires no new semantic coordinate.

The cross-context model uses combinations of:

```text
F1 Entity / Reference
F2 State
F3 Relation
F4 Transition / Constraint
F5 Time
F6 Authority / Provenance
F7 Observation / Representation
F8 Evaluation / Motivation
F9 Action / Capability / Policy / Control
```

Even dynamic community/Agent rule change remains expressible through current state, authority, time, representation and transition semantics.

```text
FoundationReopenCondition = NOT TRIGGERED
```

---

# 17. Strongest GDF0-D laws

```text
1. High PolicyDifferentiation != Game.
2. AdaptivePolicyGain is a domain-general structural probe, not Ludicness.
3. NoFixedGlobalGoal != NoEvaluation, but DynamicEvaluation != Game.
4. Exploration != Play and PerformanceProgress need not track WorldModelProgress.
5. Perturbation/Recovery != Play; social Play additionally regulates perturbation through signals/reciprocity/restraint.
6. GameGoal != ParticipationPurpose != PlayerValue != ExternalStake remains robust under professional play.
7. PlayFrame != ConsequenceIsolation remains robust under high-stakes play.
8. GameArtifact != CompleteGameStructure is strongly supported by community rule overlays such as speedrunning.
9. EffectiveRuleTopology can be distributed across artifact, participant, community, institution and material reality.
10. GameExecution != PlayExperience remains robust in both human motivational variation and synthetic-Agent cases.
11. No current single mechanism earns Game-specific category authority.
12. If Game-specificity has a mechanistic basis, current evidence points toward configuration-level coupling rather than one hidden Game atom.
13. GameCategory may remain partly historical/cultural even when causal Game mechanisms are real.
```

---

# 18. GDF0-E exact frontier

D does **not** justify reconstruction/freeze yet.

The strongest remaining unresolved problem is now sharper:

> What changes when the same underlying AgencyScaffold is enacted as work, training, ritual, art, free play or Game — and which of those changes are causal rather than merely labels?

GDF0-E should therefore run **Matched-Structure / Changed-Configuration** attacks.

Priority designs:

```text
E1 same task/scaffold × different framing/purpose/stakes
E2 same artifact × different community/player-authored rule overlays
E3 same challenge × voluntary/process-valued vs externally imposed participation
E4 same perturbation × playful reciprocity vs training optimization
E5 same sandbox affordances × free creation vs imposed objective
E6 same synthetic policy competence × human experiential evidence boundary
```

The aim is to determine whether C12 can make discriminating predictions or must be reduced to family-resemblance/configuration bookkeeping.

Only after this should GDF0 move toward final cross-cultural/Agent-era reconstruction and freeze.

---

# External pressure anchors used in D

- Fröhlich et al. (2016), *Play-solicitation gestures in chimpanzees in the wild: flexible adjustment to social circumstances and individual matrices*, Royal Society Open Science. PMC5108953.
- Pellis/play-literature pressure summarized in comparative work on social play signalling, reciprocity, role reversal and self-handicapping.
- Clemenson et al. (2019), *Improving Hippocampal Memory Through the Experience of a Rich Minecraft Environment*, Frontiers in Behavioral Neuroscience 13:57. The experimental description treats Minecraft as an open sandbox without one specific goal and manipulates directed vs free building/exploration.
- Stafford & Dewar (2021), *Long-Term Motor Learning in the “Wild” With High Volume Video Game Data*, Frontiers in Psychology / PMC8720934.
- Bányai et al. (2020), *Career as a Professional Gamer: Gaming Motives as Predictors of Career Plans to Become a Professional Esport Player*, Frontiers in Psychology 11:1866.
- Speedrun.com, current official moderation rules, category/rule guidance (accessed 2026-08-17).
- van Wetten, Plaat & van Duijn (2025), *Baba is LLM: Reasoning in a Game with Dynamic Rules*, arXiv:2506.19095.
- Zeng et al. (2026), *RuleSmith: Multi-Agent LLMs for Automated Game Balancing*, arXiv:2602.06232.
- Tondello et al./related personalized-gamification user-study pressure retained from GDF0 evidence: underlying task and game-element configuration can diverge in subjective effect.
