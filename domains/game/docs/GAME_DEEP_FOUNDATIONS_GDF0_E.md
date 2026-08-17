---
schema_version: 1
id: game.deep-foundations.gdf0-e
title: Ordivon Game Deep Foundations — GDF0-E Matched Structure × Changed Configuration
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
updated: 2026-08-17
summary: Matched and quasi-matched intervention round testing whether configuration-level changes can alter motivation, behavior, enactment or effective GameStructure while underlying task/artifact remains substantially fixed. Finds real configuration causality but rejects any monotonic 'more game elements → more play' rule; splits same-task experiential change from same-artifact structural change and retains C12 only as an empirically pressured N1 causal-factorization framework, not an N2 novel Game theory.
evidence_status: mixed
readiness: ACTIVE
applies_to:
  - ordivon-game
related:
  - game.deep-foundations.gdf0-a
  - game.deep-foundations.gdf0-b
  - game.deep-foundations.gdf0-c
  - game.deep-foundations.gdf0-d
  - game.foundations-research.r29
---
# Ordivon Game Deep Foundations — GDF0-E

## 0. Question

D produced the strongest negative result so far:

```text
no current single mechanism earns Game identity.
```

The remaining candidate was C12:

```text
ConfigurationLevelSpecificity:
if Game has mechanistic specificity beyond cultural labeling,
it may arise from relations among scaffold, evaluation/rule authority,
participant mode/purpose, practice, external coupling and category/history.
```

But that formulation is still dangerously close to a descriptive checklist.

E therefore asks an intervention question:

> If we hold substantial parts of the task/scaffold/artifact fixed and change configuration, what actually changes?

And the inverse:

> If we hold the artifact fixed and change rule/practice configuration, can the effective GameStructure itself change?

Canonical evidence ledger:

```text
evidence/gdf0-e/matched-configuration-evidence.json
scripts/gdf0-e/audit-matched-configurations.mjs
```

---

# 1. Evidence classes

E does not pretend all `same task` evidence is equally clean.

```text
M1 strong task match
   underlying task/scaffold substantially fixed;
   bounded configuration manipulation.

M2 near match
   core cognitive/action task held fixed;
   several presentation/motivation variables bundled.

M3 same artifact/affordance family
   objective, practice or rule overlay changes;
   strong for enactment/structure, weaker for subjective causal attribution.

M4 protocol only
   desired matched falsifier has not yet been adequately run/admitted.
```

This distinction prevents `quasi same` from silently becoming exact causal evidence.

---

# 2. E1 — Same cognitive task, different motivational/game configuration

Dörrenbächer et al. (2014) provides one of the best near-matched cases for C12.

The experiment separately manipulated:

```text
Training Type:
  single-task vs task-switching

Training Setting:
  low-motivational standard setting
  vs
  high-motivational game setting
```

The core categorization tasks remained the same within the training-type comparison, adaptive feedback existed in both settings, and the motivational manipulation changed story/context, labels, reward/progression presentation and choice-related game affordances.

Results included:

```text
high-motivational setting
→ greater willingness / intrinsic interest in additional practice

within task-switching training
→ some additional training and near-transfer benefits

far transfer
→ limited / not broad
```

## 2.1 What this earns

It supports:

```text
BareTaskDemand alone
!= ParticipantMotivationalOutcome
```

A largely similar cognitive scaffold can be experienced/enacted differently when frame/evaluation/presentation configuration changes.

This is real configuration causality.

## 2.2 What it does NOT earn

The manipulation bundled multiple variables:

```text
story
contextualized stimuli
labels
virtual reward/progression
collection/choice
feedback presentation
```

Therefore E cannot say:

```text
Story caused the effect
or
Points caused the effect
or
Frame alone caused the effect.
```

Nor did the study test whether the high-motivational condition became a culturally recognized Game in the philosophical sense.

So the result supports C0/C12 at configuration level, not a new Game essence.

---

# 3. E1b — Same task + game elements can change performance without changing intrinsic motivation

Mekler et al. (2017) supplies the critical opposite result.

Participants performed an image-annotation task. Points, levels and leaderboard elements were manipulated against a control condition.

Reported result:

```text
game elements
→ more tags / increased performance quantity

but
→ no significant intrinsic-motivation increase
→ no significant competence-need-satisfaction increase
```

This is one of GDF0-E's strongest falsifiers.

## 3.1 It kills a tempting monotonic theory

Reject:

```text
MoreGameElements
→ MorePlayMode
→ MoreIntrinsicMotivation
```

Even holding the underlying task substantially fixed, a configuration overlay can alter **behavior** without the hypothesized **experience/motivation** change.

Therefore:

```text
BehavioralEffect
!= ExperientialEffect
```

again strengthening C11.

## 3.2 Game elements are causal operators, not gameness particles

Points/levels/leaderboards can operate as:

```text
progress cues
extrinsic incentives
comparison signals
feedback
status information
```

without transforming the underlying activity into Play.

Strong law:

```text
GameElement != PlayMechanism by identity.
```

The effect depends on what the element changes in the participant/task coupling.

---

# 4. E1c — Different game-element configurations route through different mediators

Sailer et al. (2017) is useful because it does not treat gamification as one binary switch.

Different configurations produced different reported psychological effects:

```text
badges + leaderboards + performance graphs
→ competence satisfaction / perceived task meaningfulness effects

avatars + meaningful story + teammates
→ social relatedness effects

decision freedom
→ not changed as intended
```

This gives E a stronger causal-routing principle:

```text
ConfigurationElement
→ changes some mediator/relation
→ may change some outcome
```

not:

```text
ConfigurationElement
→ adds generic Gameness
→ everything improves
```

Therefore gamification is not one causal treatment.

This is closely aligned with C0's factorization and is a warning against any future `ludic score` scalar.

---

# 5. E3 — Same activity, changed external purpose/reward relation

Classic Deci (1971) and Lepper, Greene & Nisbett (1973) experiments provide another matched pressure.

Within each experiment, the target activity remained substantially the same while expected/contingent external reward changed.

Classic reported result under tested conditions:

```text
expected/contingent external reward
→ lower subsequent free-choice / intrinsic-interest measures
```

while Deci also found a different pattern for positive verbal feedback.

## 5.1 Strongest lesson

The same activity can acquire a different participant relation when:

```text
ParticipationPurpose
ExternalStake / RewardExpectation
Perceived control / informational feedback
```

change.

Therefore C4 remains robust:

```text
Task/GameGoal
!= ParticipationPurpose
!= ProcessValue
!= ExternalStake
```

## 5.2 Important anti-overreach

The reward literature contains boundary conditions and contrary results. E therefore rejects a universal formula such as:

```text
ExternalReward always destroys Play.
```

The stronger surviving statement is only:

```text
participant-purpose / external-reward configuration can causally alter
later participant relation to a substantially unchanged activity,
and effect direction depends on reward/context properties.
```

That is enough for C12 pressure.

---

# 6. E5 — Same game technology, different directiveness/objective topology

Clemenson et al. (2019) supplies a useful quasi-matched Minecraft intervention.

Groups used the same core Minecraft technology and controls, but conditions varied:

```text
free building
directed building
free exploration
explore + build
```

Within the building comparison, directed participants were assigned increasingly complex structures while free builders had resources without a specific prescribed construction target.

The groups developed materially different movement/building patterns, and the directed-building/exploration conditions showed different downstream hippocampal-associated memory outcomes from free building.

## 6.1 Strong lesson

```text
SameGameArtifact
!= SameEnactment
```

and:

```text
SameAffordanceFamily
+ different objective/directiveness
→ different behavior trajectory
```

This strengthens C9's no-fixed-goal distinction while again showing C9 is domain-general rather than specifically Game-defining.

## 6.2 Free is not structureless

Free building did not imply:

```text
no intention
no evaluation
no local project
```

It only removed a particular externally specified objective topology.

So E retains:

```text
AuthorGoal absent
!= ParticipantGoal absent
```

without inventing a hidden scalar utility.

---

# 7. E2 — Same artifact, different community rule overlay

Speedrunning provides the inverse intervention family.

Instead of holding task structure fixed and changing experience configuration, E holds the executable artifact fixed and changes effective rules/practice:

```text
same base game
× Any% / 100% / Glitchless / other category
× timing semantics
× technique restrictions
× version/verification requirements
```

The result is not merely a label change.

Different overlays can change:

```text
what counts as a valid run
what the goal is
which actions are admissible
what optimal policy is
when evaluation begins/ends
what evidence is required
```

Therefore:

```text
SameArtifact
!= SameEffectiveGameStructure
```

This is a structural/constitutive result, not an experiential one.

It strengthens:

```text
GameArtifact != CompleteGameStructure
Practice / community rule authority can be constitutive.
```

---

# 8. Two orthogonal non-identities now survive matched pressure

E produces a particularly useful pair.

## 8.1 Structure does not uniquely determine experience

Matched/near-matched task experiments show:

```text
substantially similar task/scaffold
+ changed configuration
→ motivation / behavior / performance can change
```

Therefore:

```text
BareTaskStructure != CompleteParticipantExperience
```

## 8.2 Artifact does not uniquely determine structure

Community/player rule overlays show:

```text
same artifact
+ changed effective rule/practice configuration
→ different effective GameStructure
```

Therefore:

```text
GameArtifact != CompleteGameStructure
```

These are independent directions.

Combined:

```text
Artifact
  does not fully determine
Structure
  does not fully determine
Experience.
```

This is one of GDF0's strongest architecture-level conclusions.

---

# 9. C12 is reconstructed, not promoted

D left:

```text
C12 ConfigurationLevelSpecificity = N1/N2 candidate
```

E now has actual intervention pressure.

But the evidence does **not** support the strong form:

```text
there exists one special configuration that converts an activity into Game/Play.
```

Instead it supports a weaker and more precise model:

```text
Outcome = f(
  Task/AgencyScaffold,
  EffectiveRuleTopology,
  Frame/Meaning,
  EvaluationLayering,
  ParticipantMode/Purpose,
  ExternalCoupling,
  Practice/History,
  Participant properties
)
```

with interactions.

Crucially:

```text
same element can affect different outcomes in different contexts;
different elements can affect different mediators;
some game elements alter performance without intrinsic motivation;
configuration effects need not be monotonic or additive.
```

## 9.1 New disposition

```text
C12:
  configuration-level causal dependence → RETAIN / empirically pressured
  Game-specificity claim → NOT EARNED
  N2 novel hypothesis → DO NOT PROMOTE
  status → N1 causal-factorization framework
```

This is a deliberate anti-novelty result.

Adjacent gamification, motivation and situated-play literatures already demonstrate important configuration/context effects. Ordivon's contribution at this stage is the integration and authority/target separation, not a claim to discovery.

---

# 10. What replaces the strong C12 idea?

Not another noun.

E retains three narrower laws.

## Law E-A — Configuration Mediation

```text
Configuration matters only through the distinctions/relations it actually changes:
meaning, evaluation, information, affordance, authority,
feedback, social relation, stakes, or participant purpose.
```

A decorative GameElement with no relevant coupling need not change PlayMode.

## Law E-B — Outcome-Specificity

```text
Performance change
!= Motivation change
!= Experience change
!= Category change
```

Any experiment must name which outcome changed.

## Law E-C — Constitutive Overlay

```text
A practice/rule overlay is constitutive when changing it changes
admissible action, goal/evaluation, transition interpretation,
or valid history/evidence under the activity.
```

This distinguishes a merely decorative label from a genuine effective-structure change.

These are currently N1 syntheses/operational rules, not N2 scientific novelty claims.

---

# 11. E4 — Playful perturbation versus training perturbation remains unresolved

D showed:

```text
PerturbationRecovery != Play
```

E wanted a matched experiment:

```text
same physical perturbation distribution
same difficulty
same participant capability

× playful reciprocal framing / role reversal / continuation signals
vs
× explicit optimization/training instruction
```

No sufficiently clean admitted study currently isolates this contrast.

Therefore:

```text
E4 = M4 protocol only
```

This is a useful unknown rather than a gap to fill with inference.

Future outcome measures should separate:

```text
recovery performance
self-handicapping
reciprocity
continuation choice
reported PlayMode/process value
social signalling
transfer
```

The same perturbation could improve skill in both conditions while differing strongly in PlayMode.

---

# 12. E6 — Human versus synthetic execution remains an epistemic protocol

A synthetic Agent can be matched to a human on parts of:

```text
observation interface
action interface
GameStructure
performance / policy quality
```

But subjective PlayExperience cannot be symmetrically measured because synthetic phenomenology is not established.

So E6 is not an experiment comparing `who has more fun`.

It tests a cleaner epistemic prediction:

```text
Comparable structural competence
can exist while evidence access to subjective PlayExperience differs radically.
```

Current Agent results already make this plausible, but E keeps it at protocol level because it is not a phenomenology experiment.

C11 remains strongly retained.

---

# 13. A more precise causal graph after E

GDF0 no longer uses a vertical Game stack.

A better provisional graph is:

```text
GameArtifact / Material Affordance
           │
           ├──────────────┐
           ▼              ▼
EffectiveRuleTopology   Practice / Community
           │              │
           └──────┬───────┘
                  ▼
          AgencyScaffold / Task
                  │
        ┌─────────┼──────────┐
        ▼         ▼          ▼
      Frame    Evaluation   ExternalCoupling
        │         │          │
        └─────────┼──────────┘
                  ▼
       Participant Interpretation /
       Purpose / Process Valuation
                  │
          ┌───────┴────────┐
          ▼                ▼
      Enactment          Experience
          │                │
          └───────┬────────┘
                  ▼
          Practice / History update
```

Feedback is bidirectional:

```text
practice can change rules;
experience can change participation;
community can change category;
artifact updates can change affordances;
participant goals can change local evaluation.
```

This remains a research graph, not a frozen ontology.

---

# 14. GameCategory is even less likely to be recoverable from mechanics alone

E's matched evidence creates an important asymmetry.

We can experimentally show that changing configuration changes:

```text
willingness
performance
motivation
behavior
practice
valid action structure
```

But none of these measurements automatically decides:

```text
"this is now culturally a Game"
```

Thus GameCategory increasingly looks like a target requiring:

```text
history
community recognition
institutional practice
linguistic/cultural classification
```

in addition to mechanics.

Strong consequence:

```text
MechanisticGameScience
and
GameCategoryTheory
should remain related but non-identical programmes.
```

This may eventually let GDF0 stop trying to solve lexical category membership with causal mechanics.

---

# 15. Discovery ledger after E

## N0 — external empirical pressure

```text
- game-setting configuration can alter willingness/intrinsic interest and some performance while core task demand remains similar;
- points/levels/leaderboards can alter performance quantity without increasing intrinsic motivation;
- different gamification configurations can target different psychological mediators;
- expected/contingent reward can alter later intrinsic-interest/free-choice measures under some matched-task conditions;
- directed vs free Minecraft configurations alter enactment and downstream learning outcomes;
- same videogame artifact can support community-defined effective rule structures.
```

## N1 — retained Ordivon synthesis

```text
C0 CoupledLudicConfiguration
C3 ModelConflictProtocol
C4 EvaluationLayering
C7 MechanismFamilyView
C10 ProgressSeparation
C11 Structural/ExperientialDissociation
C12 Configuration causal-factorization framework — reconstructed/downscoped

E-A ConfigurationMediation
E-B OutcomeSpecificity
E-C ConstitutiveOverlay
```

## N1/N2

```text
none newly promoted in E.
```

C12 is deliberately removed from N1/N2 candidate status because the broad configuration-dependence insight has substantial precedent in existing literature; the remaining Ordivon value is integration, precision and falsifier routing.

## N3

```text
NONE.
```

---

# 16. Major falsifications/demotions from E

```text
More game elements → more Play
REJECTED.

Game overlay → intrinsic motivation
REJECTED as universal.

Same task → same experience
REJECTED.

Same artifact → same GameStructure
REJECTED.

External rewards always destroy Play
REJECTED as universal.

ConfigurationLevelSpecificity as novel Game essence
NOT EARNED / DOWNSCOPED.
```

---

# 17. FoundationReopenCondition audit

E still does not require any new R29 semantic coordinate.

All matched interventions are changes in existing dimensions:

```text
State / artifact
Relations
Constraints / transition semantics
Time / history
Authority / provenance
Observation / representation
Evaluation / motivation
Action / capability / policy / control
```

The fact that these dimensions interact causally does not require a new primitive.

```text
FoundationReopenCondition = NOT TRIGGERED
```

---

# 18. Strongest GDF0-E laws

```text
1. SameTaskStructure != SameParticipantExperience.
2. SameArtifact != SameEffectiveGameStructure.
3. GameElement != PlayMechanism by identity.
4. Configuration effects are mediator-specific and outcome-specific.
5. PerformanceEffect != MotivationEffect != ExperienceEffect != CategoryEffect.
6. MoreGameElements does not monotonically imply MorePlay.
7. GameGoal != ParticipationPurpose != ProcessValue != ExternalStake remains robust under matched manipulations.
8. NoFixedGlobalGoal != NoParticipantEvaluation remains robust under sandbox manipulation.
9. Practice/community overlays can be constitutive when they change admissibility, goal/evaluation, timing or valid evidence/history.
10. C12 survives only as a causal-factorization framework; it does not earn a novel Game-specific essence.
11. Mechanistic Game science and cultural Game-category theory should not be collapsed.
12. Structural and experiential evidence must remain separate even when the underlying task is closely matched.
```

---

# 19. What E changes about GDF0's deepest question

Before E:

> Why does the same action problem become Game/Play rather than work/training/ritual?

After E, that question must be split.

## Question A — causal participant relation

```text
What configuration changes motivation, meaning, continuation,
attention, effort and experience while structure remains similar?
```

This is experimentally tractable and clearly real.

## Question B — effective structure

```text
What practice/rule overlays genuinely change the action problem
while the material artifact remains fixed?
```

This is also tractable and clearly real.

## Question C — cultural category

```text
Why does a community/history call one configuration a Game,
another training, another ritual, another work?
```

This may not be reducible to A or B.

That three-way split is more useful than continuing to hunt one `Game atom`.

---

# 20. GDF0-F exact frontier

E does not yet justify final reconstruction/freeze because two major areas remain under-attacked:

```text
1. cultural / historical / cross-cultural GameCategory and PlayPractice;
2. social vs solitary frame construction, especially how PlayMode is negotiated or self-generated.
```

The next round should therefore be:

# GDF0-F — Social, Cultural and Historical Constitution of Play/Game

F should test:

```text
- whether GameCategory has stable cross-cultural invariants or mostly historical family structure;
- how folk games persist without a single artifact/designer;
- how social signals establish/repair PlayFrame;
- how solitary pretend/object play creates frame without social negotiation;
- how ritual, sport, gambling, festival and work/game boundaries vary historically;
- whether institutionalization transforms PlayPractice into Game/Sport without changing core mechanics;
- how communities create legitimacy, rule authority and category identity;
- whether Agent participants can enter these social/category processes without any assumption of phenomenology.
```

F should use anthropology/history/developmental/social-play evidence and should be willing to conclude that `GameCategory` is partly conventional while Game mechanisms remain causal and real.

Only after F and an Agent-era boundary round should GDF0 attempt final falsification/reconstruction/freeze.

---

# Primary evidence anchors used in E

- Dörrenbächer, Müller, Tröger & Kray (2014), *Dissociable effects of game elements on motivation and cognition in a task-switching training in middle childhood*, Frontiers in Psychology 5:1275, DOI 10.3389/fpsyg.2014.01275.
- Mekler, Brühlmann, Tuch & Opwis (2017), *Towards understanding the effects of individual gamification elements on intrinsic motivation and performance*, Computers in Human Behavior 71:525–534, DOI 10.1016/j.chb.2015.08.048.
- Sailer, Hense, Mayr & Mandl (2017), *How gamification motivates: An experimental study of the effects of specific game design elements on psychological need satisfaction*, Computers in Human Behavior 69:371–380, DOI 10.1016/j.chb.2016.12.033.
- Deci (1971), *Effects of externally mediated rewards on intrinsic motivation*, Journal of Personality and Social Psychology 18(1):105–115, DOI 10.1037/h0030644.
- Lepper, Greene & Nisbett (1973), *Undermining children's intrinsic interest with extrinsic reward: A test of the overjustification hypothesis*, Journal of Personality and Social Psychology 28(1):129–137, DOI 10.1037/h0035519.
- Clemenson et al. (2019), *Improving Hippocampal Memory Through the Experience of a Rich Minecraft Environment*, Frontiers in Behavioral Neuroscience 13:57, DOI 10.3389/fnbeh.2019.00057.
- Current Speedrun.com moderation/category-rule practice retained as structural, not experimental, evidence.
