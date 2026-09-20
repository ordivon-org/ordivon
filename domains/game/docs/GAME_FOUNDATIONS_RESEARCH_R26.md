---
schema_version: 1
id: game.foundations-research.r26
title: Ordivon Game Foundations Research R26 — Emotion, Affect, Feeling, Mood, Valence, Arousal, Appraisal, Regulation, Empathy and Expression
type: research
profile: research
lifecycle: active
source_role: canonical
visibility: public
owners:
  - ordivon-game
audience:
  - designer
  - researcher
  - builder
  - agent
updated: 2026-08-17
summary: First-principles decomposition of affective processes and states for Game foundations; separates affective significance, emotion episodes, feeling, mood, appraisal, action readiness, expression, regulation and social emotion without selecting a product or one universal psychological theory.
evidence_status: derived
readiness: CANONICAL
applies_to:
  - ordivon-game
related:
  - game.foundations-research.r18
  - game.foundations-research.r21
  - game.foundations-research.r22
  - game.foundations-research.r24
  - game.foundations-research.r25
  - game.foundations-research.map
---
# R26 — Emotion, Affect, Feeling, Mood, Valence, Arousal, Appraisal, Regulation, Empathy and Expression

## 0. Research question

R25 asked what persistent relational structure exists between Subjects. R26 asks:

> What changes inside a Subject when an event is affectively significant, and how do those changes alter perception, attention, memory, action readiness, regulation, relationship and expression?

The round is not an attempt to choose a psychology engine. It is an ontology and causality audit for Game foundations.

The first conclusion is already negative:

```text
Emotion != one scalar
Emotion != sentiment label
Emotion != reward
Emotion != valence
Emotion != arousal
Emotion != expression
Emotion != feeling
```

## 1. Why emotion cannot be one primitive

Three major families are useful as pressure tests rather than mutually exclusive implementation mandates:

```text
Discrete/basic-emotion approaches
→ useful when stable emotion categories predict distinct action/recognition patterns.

Dimensional/core-affect approaches
→ useful when continuous pleasantness/unpleasantness and activation/deactivation explain graded states.

Appraisal/component/process approaches
→ useful when the same event produces different emotional consequences because goals,
  concerns, agency, control, novelty, norms, identity or relationship differ.
```

The literature does not justify collapsing the field to one representation. Scherer & Moors emphasize an unfolding process in which appraisal differentiates action tendencies, physiological responses and expressions, followed by conscious feeling and emotion labeling. citeturn1search17 Russell-style circumplex work provides a useful low-dimensional representation of core affect using valence and arousal, but this is not sufficient to explain why two equally unpleasant/high-arousal events generate different emotions or actions. citeturn0search3turn0search8 Contemporary reviews continue to debate discrete, dimensional and constructionist representations, which is precisely why Game foundations should preserve representational pluralism until causal tests compress it. citeturn0search72turn0search73

## 2. Affect

Use **Affect** as the broad family of value-laden / feeling-related organismic phenomena rather than a synonym for a named emotion.

A useful Game-level abstraction is:

```text
AffectiveState(S) =
current affective configuration of S
across relevant dimensions/components
```

It may include:

```text
pleasantness / unpleasantness
activation / deactivation
approach / withdrawal bias
salience / urgency
bodily activation
subjective feeling
emotion-specific appraisal consequences
```

But not every affective state is a full emotion episode.

```text
Affect != Emotion
```

A calm pleasant baseline, diffuse irritability, bodily activation, or an undifferentiated bad feeling can be affectively real without a clean object-directed emotion label.

## 3. Valence

```text
Valence = direction of affective evaluation
         toward pleasant / beneficial / attractive
         versus unpleasant / aversive / undesirable
```

Valence is useful but radically lossy.

```text
joy     → positive
relief  → positive
love    → positive
anger   → negative
fear    → negative
sadness → negative
```

Yet equal valence does not imply equal:

```text
action tendency
arousal
attention
social meaning
memory effect
relationship consequence
```

Therefore:

```text
Valence != EmotionIdentity
Valence != Utility
Valence != Value
Valence != Reward
```

R18 Value is a broader evaluative structure about what matters; valence is an affective polarity. A player can value a difficult goal while feeling bad during its pursuit.

## 4. Arousal

```text
Arousal = activation / mobilization level of the affective system
```

High arousal and low arousal can occur at either valence:

```text
positive + high → excitement
positive + low  → calm/contentment
negative + high → panic/rage
negative + low  → sadness/dejection
```

Therefore:

```text
Arousal != EnergyResource
Arousal != Motivation
Arousal != Action
```

A highly aroused Subject can freeze, hesitate or suppress action; a low-arousal state can still encode a strong persistent preference or commitment.

## 5. Emotion

The strongest R26 compression is to treat **Emotion** as a temporally unfolding, object-/event-/concern-related affective episode rather than a permanent scalar state.

```text
EmotionEpisode(S, X, t0..t1) =
coordinated change across some subset of:

appraisal
attention
action readiness
physiology
expression
subjective feeling
memory/learning bias
social signaling

in response to X being evaluated as relevant to S's concerns,
goals, values, identity, relationships or needs.
```

This is intentionally componential and sparse: not every emotion must visibly instantiate every component. Scherer & Moors explicitly frame emotion as a process involving appraisal, action tendencies, physiological responses, expression and conscious feeling, rather than merely a categorical endpoint. citeturn0search0

Thus:

```text
Emotion = coordinated affective episode
not merely
Emotion = label
```

## 6. Appraisal

Appraisal is not simply “thinking about an event.” It is evaluation of an event with respect to the Subject's current concerns and action possibilities.

A minimal appraisal vector can contain:

```text
relevance          → does this matter to me?
valence             → is it beneficial/aversive?
goal congruence     → does it help/hurt a goal?
novelty             → is it unexpected/new?
agency              → who/what caused it?
control             → can I influence it?
certainty           → how predictable is it?
urgency             → how soon does it matter?
norm compatibility  → does it violate a norm/value?
relationship meaning→ what does it imply about another Subject?
identity meaning   → what does it imply about who I am?
```

This immediately connects R18–R25:

```text
Need / Value / Goal / Preference
        ↓
Appraisal of event
        ↓
Affective significance
        ↓
Emotion episode
        ↓
Action readiness / attention / memory / expression
        ↓
new world + relationship state
        ↓
new appraisal
```

Appraisal is therefore recursive, not a one-time classifier. Scherer/Sander work explicitly treats appraisal and emotional components as dynamically interacting. citeturn0search15

## 7. Action tendency

Emotion often changes what actions become locally ready, salient or prioritized.

```text
ActionTendency(S) =
change in readiness / priority for classes of action
```

Examples:

```text
fear   → avoid / escape / seek safety
anger  → confront / remove obstacle / punish
care   → protect / support
curiosity → approach / inspect
shame  → hide / repair / withdraw
pride  → maintain / display / invest
```

But:

```text
ActionTendency != Action
```

Action still depends on:

```text
capability
resources
cost
norms
competing goals
control
available repertoire
```

Frijda's action-readiness tradition is especially useful here: emotion changes readiness to maintain or change a relation to an object/event, but actual behavior depends on available action repertoire and competing costs. citeturn0search14

## 8. Emotion is not motivation, but it modifies motivation

R18 established:

```text
Need
Want
Desire
Goal
Preference
Value
Utility
Commitment
```

R26 should not replace these with emotion.

Instead:

```text
Emotion
→ changes salience / action readiness / attention / valuation dynamics
→ influences motivation
```

For example:

```text
Goal: defeat boss
Value: mastery
Emotion: fear
```

Fear does not become the Goal. It changes:

```text
perceived risk
attention
avoidance tendency
information seeking
confidence
willingness to commit
```

Likewise:

```text
Goal: save companion
Emotion: grief
```

does not mean grief is the goal. Grief changes the trajectory through which the goal is pursued.

## 9. Feeling

```text
Feeling = Subject-accessible / consciously experienced representation
of some ongoing affective organization
```

This keeps feeling distinct from the full emotion process.

A Subject can have:

```text
physiological activation
+
action readiness
+
expression
```

without fully identifying or articulating what it feels.

Conversely, feeling language can be generated or reported without proving the underlying world state.

Therefore:

```text
Feeling != Emotion as a whole
Feeling != Expression
FeelingReport != InternalAffectiveTruth
```

Scherer's component-process account explicitly places conscious feeling alongside, rather than identical to, physiological, motivational and expressive components. citeturn0search0turn0search16

## 10. Mood

Mood should be modeled as a more persistent, diffuse affective background than an event-specific emotion.

```text
Mood(S, t) =
relatively persistent affective context
that may have weak / ambiguous object direction
and biases subsequent appraisal and action
```

A useful distinction is:

```text
Emotion → usually event/object/concern-linked, comparatively acute
Mood    → more diffuse, persistent, less tightly object-bound
```

The distinction is not absolute, but this direction is useful for simulation. Reviews commonly characterize moods as more enduring and diffuse while emotions are more intense and tied to specific objects/events. citeturn1search42

Crucially:

```text
Mood != LongEmotion
```

because mood can alter the appraisal of subsequent unrelated events.

## 11. Affect → cognition and memory

Emotion is causally important because it changes information processing.

Affective cognition research identifies effects on attention, memory and categorization, while emotional arousal can enhance encoding/consolidation under some conditions and impair retrieval under high/chronic stress. citeturn0search6turn0search1

Therefore the Game model should allow:

```text
Affect
→ attention bias
→ encoding bias
→ consolidation bias
→ retrieval bias
→ interpretation bias
→ learning
```

But not:

```text
Emotion = memory priority
```

Memory quality and affective salience remain distinct.

## 12. Emotion × uncertainty / risk

R22 established uncertainty as structural. R26 adds:

```text
uncertainty → appraisal
appraisal → affect
affect → attention / exploration / avoidance
→ information acquisition
→ uncertainty update
```

Thus emotion can participate in a closed loop:

```text
uncertainty
   ↓
appraisal of threat/opportunity
   ↓
affective activation
   ↓
attention / information seeking / avoidance
   ↓
new evidence
   ↓
uncertainty update
```

Fear can increase information seeking in one context and avoidance in another. Curiosity can increase exploration despite uncertainty. Confidence can reduce information acquisition and therefore sometimes increase error.

So:

```text
Emotion != RiskPreference
```

but emotion can dynamically alter risk processing.

## 13. Regulation

Emotion regulation is not “make emotion smaller.” It is the process of changing some aspect of the emotion-generating trajectory or its consequences.

Gross' process model provides a useful decomposition:

```text
1. Situation selection
2. Situation modification
3. Attentional deployment
4. Cognitive change / reappraisal
5. Response modulation
```

These can target different points in the emotional process. citeturn1search1turn1search2

Therefore:

```text
Regulation != Suppression
```

Suppression is only one possible response-focused strategy.

Regulation can mean:

```text
avoid
approach
change environment
redirect attention
seek information
reinterpret event
seek social support
express
suppress
rehearse
wait
recover
```

## 14. Regulation is not universally good

R26 rejects:

```text
more regulation = better
less emotion = better
suppression = bad
expression = good
```

The effect depends on:

```text
person
situation
strategy
timing
emotion
goal
social context
cost
```

Research explicitly warns that regulation strategies can have contradictory consequences depending on context. citeturn1search6

For Game design this is critical: a character who suppresses fear may gain short-term task performance but lose social information or later recovery; a character who expresses anger may change another Subject's behavior while worsening the relationship.

## 15. Recovery

Emotion has temporal dynamics.

```text
Trigger
→ appraisal
→ escalation / differentiation
→ peak
→ regulation / action / feedback
→ decay / transformation / recovery
```

Recovery should not be a fixed timer:

```text
EmotionDecay != constantTimer
```

Recovery can depend on:

```text
continued threat
rumination
new evidence
sleep/rest
social support
successful action
unresolved goal
relationship repair
memory reactivation
regulation strategy
```

This is important for persistent Agents: “anger +10 for 30 seconds” is not an adequate relational emotion model when the cause remains unresolved.

## 16. Expression

Expression is an observable behavior/signaling channel, not proof of internal emotion.

```text
Expression = behavior that changes what an observer can infer / feel / do
```

It may be:

```text
spontaneous
regulated
strategic
culturally learned
role-constrained
ambiguous
misleading
```

Therefore:

```text
InternalAffect != Expression
Expression != EmotionTruth
```

Research on facial/vocal expression explicitly challenges the assumption that expressive behavior simply “contains” or transparently reveals an inner emotion; expressions are directed at receivers and can have communicative and strategic functions. citeturn1search7turn0search2

## 17. Observer emotion reasoning

An observer does not simply decode an emotion label.

```text
ObservedSignal
+ context
+ prior relationship
+ beliefs
+ norms
+ body/voice/text cues
→ EmotionInference / EmotionAttribution
```

So:

```text
EmotionRecognition != EmotionAccess
```

Recent developmental work even argues that “emotion recognition” can be misleading when the real capability is reasoning about another's likely emotional state from incomplete evidence. citeturn1search16

This aligns directly with R12 Information:

```text
WorldTruth
→ Signal
→ Observation
→ Interpretation
→ Belief
```

Emotion inference belongs in the interpretation layer.

## 18. Empathy decomposition

R26 separates at least four processes:

```text
Emotional contagion
→ observer's affect changes in response to another's affect

Perspective taking
→ representing / reasoning about another's point of view

Empathic concern / compassion
→ other-oriented concern for another's welfare

Care
→ persistent welfare of the other entering one's evaluative/action structure
```

They can dissociate.

```text
contagion without understanding
understanding without shared feeling
shared feeling without concern
concern without strong emotional matching
```

Empathy research describes a progression from state-matching toward more complex concern and perspective-taking, supporting the need to avoid a single empathy scalar. citeturn1search19

Thus:

```text
Empathy != Contagion
Empathy != PerspectiveTaking
Empathy != Compassion
Empathy != Care
```

## 19. Relational emotions

R25 makes emotions relationally structured.

Examples:

```text
jealousy
= affective response to perceived threat to a valued relationship / position

betrayal anger
= emotion shaped by prior trust/commitment/expectation

gratitude
= positive response to perceived intentional benefit from another

guilt
= self-evaluation against a norm/obligation involving another

shame
= negative self-relevant evaluation with social/identity exposure

grief
= affective process following loss of a valued person/relationship/state
```

The important point is not the labels. It is:

```text
RelationalEmotion
= Emotion whose appraisal space includes relational state/history
```

So R25 changes R26 causality:

```text
same event
+
different relationship state
→ different emotion
```

## 20. Emotion × identity

R24 identity means emotional appraisal can depend on:

```text
who I believe I am
who I am trying to become
what threatens identity continuity
what confirms identity
```

Therefore:

```text
same defeat
```

can generate:

```text
anger      if identity = “I am superior”
shame      if identity = “I failed the group”
curiosity  if identity = “I am a learner”
grief      if defeat destroys a valued future
relief     if defeat ends an unwanted commitment
```

This is another reason emotion cannot be a fixed event→label table.

## 21. Expression creates social causality

Expression is not merely UI decoration.

```text
InternalState
→ Expression
→ Observer inference / affect
→ Observer action
→ Relationship / group state
→ future appraisal
```

Emotional expressions have documented effects on observers' affect, inference and behavior across relationships, negotiation and group contexts. citeturn1search0

Therefore:

```text
Expression can be gameplay
```

when other Subjects react to it causally.

A facial animation that looks angry but changes nothing is presentation.

A restrained expression that causes an ally to misread the protagonist and withdraw support is a game mechanic.

## 22. Emotion gameplay test

Emotion belongs in gameplay when changing it changes counterfactual futures:

```text
If the Subject had felt differently,
would the available / selected / perceived future differ?
```

Useful tests:

```text
fear changes exploration route
anger changes negotiation
shame changes disclosure
trust changes interpretation of expression
mood changes appraisal of ambiguous events
regulation changes action availability
empathy changes help / harm decisions
expression changes another Subject's policy
```

If removing emotion changes none of these, emotion is likely presentation rather than foundational gameplay state.

## 23. Minimum affective machinery by role

### Pattern enemy

Usually enough:

```text
threat appraisal
activation
action tendency
simple expression
recovery
```

### Authored character

May need:

```text
event appraisal
emotion episodes
mood
regulation
memory bias
expression
relationship-linked emotion
```

### Social Subject

Needs stronger:

```text
other-model inference
relational appraisal
emotion regulation
expression interpretation
social emotion
repair / norm interaction
```

### Generative Persona

Requires:

```text
authoritative affective facts/state
salient episode history
soft interpretation/expression
continuity constraints
```

Generated language alone is insufficient.

### Persistent autonomous Agent

Potentially requires:

```text
persistent affective state
appraisal process
regulation policy
memory interaction
uncertainty interaction
relationship interaction
expression
recovery dynamics
```

But only if those dimensions materially alter behavior.

## 24. Generative emotion debt

Generated emotion claims create future obligations just as R25 relationship claims did.

```text
“I am terrified.”
→ should constrain subsequent behavior / memory / interpretation

“I feel betrayed.”
→ requires relational history capable of supporting betrayal

“I am calm now.”
→ should be compatible with recovery / regulation evidence

“I care about you.”
→ creates relational and behavioral continuity debt
```

Therefore:

```text
GeneratedEmotionExpression
!=
AuthoritativeInternalAffect
```

A system may generate an expression as a hypothesis, roleplay line or communication act without mutating authoritative internal state.

## 25. Affective architecture candidate

R26 does not freeze a single implementation, but a strong causal candidate is:

```text
World / Body / Memory / Relationship / Goal / Norm / Uncertainty
                         ↓
                    Appraisal
                         ↓
               Affective significance
                         ↓
      ┌──────────┬─────────┬──────────┬─────────┐
      ↓          ↓         ↓          ↓         ↓
   Attention   Action    Physiology  Feeling  Expression
      ↓          ↓         ↓          ↓         ↓
      └──────────┴────── feedback ────┴─────────┘
                         ↓
                    Regulation
                         ↓
                  Action / Learning
                         ↓
                 World / Relation change
                         ↓
                     Re-appraisal
```

This is a **candidate causal grammar**, not yet a product architecture.

## 26. Core falsifications

R26 rejects these shortcuts:

```text
Emotion = sentiment polarity
Emotion = valence
Emotion = valence + arousal
Emotion = reward
Emotion = utility
Emotion = action
Emotion = feeling report
Emotion = facial expression
Emotion = physiological activation
Mood = long-duration emotion
Empathy = emotional contagion
Empathy = perspective taking
Care = empathy
Expression = internal truth
Suppression = regulation as a whole
Regulation = making emotion weaker
Generated emotion words = internal emotion state
```

## 27. R26 durable laws

```text
Affect != Emotion
Emotion != OneScalar
Valence != Value
Valence != Reward
Arousal != Motivation
Emotion != Action
ActionTendency != Action
Feeling != EmotionWhole
FeelingReport != InternalAffectiveTruth
Mood != LongEmotion
Appraisal != GenericThought
EmotionRegulation != Suppression
Regulation != AlwaysGood
Expression != InternalAffect
Expression != EmotionTruth
EmotionRecognition != EmotionAccess
Empathy != Contagion
Empathy != PerspectiveTaking
Empathy != Compassion
Empathy != Care
RelationalEmotion depends on relational appraisal/history
Emotion can causally alter attention, memory, uncertainty processing and action readiness
Emotion becomes gameplay when affective counterfactuals change meaningful futures
```

## 28. R26 compression

The minimum useful abstraction is not “emotion state.” It is:

```text
Affective substrate
+
Appraisal
+
temporally unfolding EmotionEpisode
+
ActionTendency
+
optional Feeling
+
optional/strategic Expression
+
Regulation
+
Recovery
+
observer-side EmotionInference
```

with:

```text
Valence / Arousal = useful dimensions
Emotion labels     = useful semantic categories
Appraisal          = causal differentiation mechanism
```

This lets the model use a 2D affect representation where it is sufficient, a discrete label where it is useful, and a richer component/process representation where causal fidelity requires it.

## 29. What R26 changes about Game

R25 showed that a relationship is real when it changes future relational affordances.

R26 generalizes the same criterion inward:

```text
Affective state is gameplay-relevant
when it changes the Subject's future
perception / interpretation / action / memory / relation.
```

Thus the real question is not:

> “Does the NPC have emotions?”

but:

> “Does affective significance create stable counterfactual differences in what this Subject perceives, values, remembers, attempts, expresses, regulates and causes next?”

That is the Game-foundations level question.

## 30. Next frontier

R26 does not select a product.

The next research problem should connect affect to the remaining foundations and ask how internal dynamics become a persistent **Subject trajectory**:

```text
R18 Motivation / Value
R21 Embodiment / Control
R22 Uncertainty / Risk
R23 Time / Change
R24 Identity / Continuity
R25 Relationship / Social structure
R26 Affect / Emotion
        ↓
next frontier:
Learning / Adaptation / Memory / Belief revision / Personality / Self-model
```

The next round should be selected only after checking the remaining canonical map rather than assuming a predetermined product path.

## 31. Research evidence base

Key pressure-test sources used in R26:

- Scherer & Moors, *The Emotion Process: Event Appraisal and Component Differentiation* — emotion as unfolding appraisal/component process. citeturn0search0turn1search17
- Russell/circumplex tradition — core affect represented through valence and arousal. citeturn0search3turn0search8
- Frijda/action-readiness tradition — emotion changes readiness while action remains constrained by repertoire and costs. citeturn0search14
- LaBar & Cabeza — emotional arousal interacts with attention, encoding, consolidation and retrieval. citeturn0search1
- Gross process model and subsequent work — regulation targets situation, attention, appraisal and response at different stages. citeturn1search1turn1search2
- Barrett/modern affective-science debate — dimensional, discrete and constructionist representations remain active theoretical alternatives. citeturn0search72turn0search73
- Facial/vocal expression research — expression is not a transparent readout of internal emotion and has receiver-directed/social effects. citeturn1search7turn1search0
- Empathy research — emotional state matching, concern and perspective-taking should not be collapsed. citeturn1search19

## 32. Status

```text
R26 research: complete
Product selection: none
Canonical boundary: frozen pending repository integration
Next: synthesize remaining foundations after verifying map/frontier
```

> R26 establishes affect as a causal family, emotion as a coordinated temporal episode, appraisal as a differentiating process, feeling as subjective access, mood as persistent background, expression as socially consequential behavior, regulation as trajectory control, and empathy as a family of separable other-related processes. None should be collapsed into a single emotion scalar.
