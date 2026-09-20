---
schema_version: 1
id: game.foundations-research.r27
title: Ordivon Game Foundations Research — R27 Learning, Adaptation and Persistent Subject Change
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
summary: Canonical R27 synthesis of experience-driven persistent Subject change: learning, adaptation, memory, belief revision, skill, habit, generalization, forgetting, personality, self-model and meta-learning, with explicit separation from performance change and product selection.
evidence_status: derived
readiness: READY
applies_to:
  - ordivon-game
related:
  - game.foundations-research.r1-r17
  - game.foundations-research.r18
  - game.foundations-research.r19
  - game.foundations-research.r20
  - game.foundations-research.r21
  - game.foundations-research.r22
  - game.foundations-research.r23
  - game.foundations-research.r24
  - game.foundations-research.r25
  - game.foundations-research.r26
  - game.foundations-research.map
  - game.foundations-research.continuation
  - game.core-research.reset
---
# Ordivon Game Foundations Research — R27 Learning, Adaptation and Persistent Subject Change

## 0. Status and boundary

R27 follows R1–R26 but does **not** assume that the next missing foundation is `Memory` merely because Memory appears throughout the corpus.

R26 left the synthesis frontier:

```text
Learning
Adaptation
Memory
Belief Revision
Personality
Self-model
```

R27 first asks whether these are actually independent primitives.

The result is:

```text
R27 is fundamentally about Persistent Subject Change.
```

`Learning` is the central experience-linked change process. `Memory`, `Belief Revision`, `Skill`, `Habit`, `Personality`, `Self-model` and `Meta-learning` occupy different roles inside that process rather than forming one flat list of equivalent faculties.

Starting warnings:

```text
Experience != Learning
Exposure != Learning
Feedback != Learning
StateChange != Learning
PerformanceChange != Learning
Improvement != Learning
Learning != Adaptation
Adaptation != Improvement
Learning != Memory
Memory != Storage
Memory != History
Memory != Retrieval
Retrieval != Replay
Forgetting != Deletion
BeliefRevision != InformationAcquisition
BeliefRevision != TruthConvergence
Learning != BeliefRevision
PredictionError != Learning itself
Reward != Learning
Skill != Knowledge
Habit != Goal
Habit != Permanence
Personality != Identity
Personality != Mood
Personality != one current Policy
Personality != ImmutableTraitVector
SelfModel != Self
SelfModel != IdentityAuthority
SelfModel != WorldTruth
ModelFineTuning != CharacterLearning by default
LongContext != FunctionalMemory
OutputChange != Learning without retained causal update
```

No product is selected by R27.

---

# 1. Why R27 is not simply “Memory”

R13 already established:

```text
Progression != Persistence != Memory != History != Learning

Memory = past information available to future cognition
Learning = experience changes future policy/model
```

R17 already owns the epistemic chain:

```text
WorldTruth
→ Signal
→ Observation
→ Interpretation
→ Belief
→ Policy
```

R21 already defines Skill as learned ability. R24 already defines SelfModel as a potentially false model of the Subject's own identity/history/roles/capabilities/commitments. R25 uses compressed relationship history, and R26 sends emotion through memory/learning feedback.

Therefore the true remaining gap is not “what is a memory store?” It is:

> **How can past experience produce retained changes in a Subject such that future perception, inference, evaluation, control or policy becomes counterfactually different?**

That is the R27 foundation.

---

# 2. External pressure tests

R27 uses learning science, memory neuroscience, motor adaptation, personality and self-efficacy as falsifiers. No one biological architecture is imported wholesale into Game.

## 2.1 Tolman — learning can precede visible performance advantage

Tolman's cognitive-map / latent-learning tradition is a strong counterexample to:

```text
Learning = immediate rewarded performance improvement
```

A Subject may acquire useful environmental structure before that knowledge is expressed in current behavior.

Game lesson:

```text
Learning can be latent.
Performance is an observation channel for learning, not learning itself.
```

## 2.2 Rescorla — mere co-occurrence is weaker than informative contingency

Rescorla's 1968 conditioning experiments showed that the contingency between cue and outcome mattered: when shock probability was equal with and without the cue, conditioning was greatly reduced despite cue–shock pairings.

Game lesson:

```text
ExposureCount != EvidenceQuality
```

Repeated events need not teach a useful predictive distinction.

## 2.3 Balleine & Dickinson — learned action can be goal-directed or habit-like

Instrumental behavior can reflect action–outcome/value-sensitive control or stimulus–response habit-like control. The distinction is important because both can be learned while relying on different retained structures.

R27 therefore rejects:

```text
all learned action = explicit belief + goal deliberation
```

Recent work also warns that devaluation-insensitivity can be methodologically misclassified as habit, so Game should use habit as an operational causal pattern, not a magic internal label.

## 2.4 Cohen & Squire / Knowlton — learning can survive impaired declarative memory

Amnesic participants can acquire and retain pattern-analysis skills or probabilistic classification performance despite severe impairment in explicit memory for training episodes.

Game lesson:

```text
Learning != DeclarativeRecollection
```

A Subject can change future policy/capability without retaining an episodic story of how it learned.

## 2.5 Constructive memory — remembering is not database replay

Schacter and colleagues characterize human episodic memory as constructive and therefore capable of distortion; encoding, retrieval cueing, monitoring and reconstruction all matter.

Game lesson:

```text
Memory != ImmutableEventLog
Retrieval != ByteReplay
```

## 2.6 Reconsolidation — retrieval can participate in updating

Nader/Schafe/LeDoux and later human episodic work show that reactivated memories can under some conditions become modifiable and integrate later information.

Game lesson:

```text
ReadMemory
need not be semantically equivalent to
ReadOnlyStorage
```

A Game does not need biological reconsolidation, but should not assume memory must be immutable to be coherent.

## 2.7 Motor adaptation — adaptation tasks contain multiple learning processes

Shadmehr & Mussa-Ivaldi demonstrated adaptive internal representations during motor learning. Later work shows that visuomotor “adaptation” behavior can combine internal-model adaptation, use-dependent plasticity and operant reinforcement, and that savings/relearning need not be reducible to one error-based process.

Game lesson:

```text
Adaptation != one LearningAlgorithm
```

and:

```text
same observed performance trajectory
can arise from different retained mechanisms.
```

## 2.8 Volatility-sensitive learning — evidence weight should be context-sensitive

Behrens and colleagues showed that participants changed how strongly outcomes influenced future choices as environmental volatility changed.

Game lesson:

```text
LearningRate != universal constant
```

Subjects can learn not only values/models, but how quickly current evidence should update them.

## 2.9 Personality — stability and change coexist

Longitudinal personality research finds both substantial stability and meaningful change over adulthood. Experience-sampling work also shows large within-person state variation alongside stable individual differences in behavioral distributions.

Game lesson:

```text
PersonalityStability != BehavioralRigidity
```

Personality can be modeled as a slower statistical regularity over context-conditioned behavior rather than one immutable state.

## 2.10 Self-efficacy — self-belief can be causally important without changing objective capability

Bandura's self-efficacy experiments support a useful counterfactual: beliefs about one's own capability can alter persistence and approach behavior.

Game lesson:

```text
ObjectiveCapability
!=
BeliefAboutOwnCapability
```

A self-model can therefore matter causally even when world capability is unchanged.

### Reference anchors used in this round

- Tolman, E. C. (1948), *Cognitive Maps in Rats and Men*, DOI 10.1037/h0061626.
- Rescorla, R. A. (1968), *Probability of Shock in the Presence and Absence of CS in Fear Conditioning*, DOI 10.1037/h0025984.
- Cohen, N. J. & Squire, L. R. (1980), *Preserved Learning and Retention of Pattern-Analyzing Skill in Amnesia*, DOI 10.1126/science.7414331.
- Shadmehr, R. & Mussa-Ivaldi, F. A. (1994), *Adaptive Representation of Dynamics during Learning of a Motor Task*, DOI 10.1523/JNEUROSCI.14-05-03208.1994.
- Knowlton, B. J., Mangels, J. A. & Squire, L. R. (1996), *A Neostriatal Habit Learning System in Humans*, DOI 10.1126/science.273.5280.1399.
- Squire, L. R. & Zola, S. M. (1996), *Structure and Function of Declarative and Nondeclarative Memory Systems*, DOI 10.1073/pnas.93.24.13515.
- Balleine, B. W. & Dickinson, A. (1998), *Goal-directed Instrumental Action*, DOI 10.1016/S0028-3908(98)00033-1.
- Schacter, D. L., Norman, K. A. & Koutstaal, W. (1998), *The Cognitive Neuroscience of Constructive Memory*, DOI 10.1146/annurev.psych.49.1.289.
- Nader, K., Schafe, G. E. & LeDoux, J. E. (2000), *Fear Memories Require Protein Synthesis in the Amygdala for Reconsolidation after Retrieval*, DOI 10.1038/35021052.
- Fleeson, W. (2001), *Traits as Density Distributions of States*, PMID 11414368.
- Hupbach, A. et al. (2007), *Reconsolidation of Episodic Memories*, DOI 10.1101/lm.365707.
- Behrens, T. E. J. et al. (2007), *Learning the Value of Information in an Uncertain World*, DOI 10.1038/nn1954.
- Roberts, B. W. & Mroczek, D. (2008), *Personality Trait Change in Adulthood*, DOI 10.1111/j.1467-8721.2008.00543.x.
- Huang, V. S. et al. (2011), *Rethinking Motor Learning and Savings in Adaptation Paradigms*, DOI 10.1016/j.neuron.2011.04.012.
- Bandura, A. (1977), *Self-efficacy: Toward a Unifying Theory of Behavioral Change*, DOI 10.1037/0033-295X.84.2.191.

---

# 3. Core term separation

| Term | Working meaning | Not equivalent to |
| --- | --- | --- |
| **Experience** | Event/observation/action/outcome encountered by a Subject. | Learning. |
| **Exposure** | Opportunity for experience/information to occur. | Encoding or update. |
| **Feedback** | Evidence about consequence, error, success, attribution or discrepancy relative to action/expectation. | Learning itself. |
| **Update** | Difference between internal state at two times produced by some transition. | Necessarily learning. |
| **Learning** | Experience/evidence-linked retained update that changes future inference, prediction, evaluation, selection, control or policy in a relevant context. | Improvement, memory, reward. |
| **Adaptation** | Change in actor–environment fit or behavior appropriate to current conditions. | Necessarily durable learning. |
| **Retention** | Persistence of a learned trace/change across a specified boundary. | Perfect retrieval. |
| **Memory** | Past-derived trace/information/state that can be made functionally available to influence present/future cognition or action. | Storage or history alone. |
| **Trace** | Retained present state whose causal origin includes prior experience. | Full episode replay. |
| **Retrieval** | Process making retained past-derived information/state usable in the current context. | Truth or exact reproduction. |
| **Reconstruction** | Current construction of a usable remembered representation from traces + cues + current model/context. | Fabrication by default. |
| **Forgetting** | Reduction/loss of accessibility or future influence of past-derived information. | Physical deletion necessarily. |
| **Belief Revision** | Experience/evidence-linked change to epistemic belief/model state. | Information acquisition or truth convergence. |
| **Generalization** | Learned change influences contexts/items beyond the exact training instance. | Always beneficial transfer. |
| **Transfer** | Learned structure from one context/task becomes useful or influential in another. | Generalization necessarily symmetric. |
| **Skill** | Learned ability to produce more reliable/better task-relevant action or decision. | Knowledge alone. |
| **Habit** | Learned cue/context-linked response policy relatively less sensitive to current outcome value/goal reasoning. | Permanent behavior. |
| **Meta-learning** | Experience changes how future learning/update itself operates. | Merely learning more facts. |
| **Personality** | Relatively stable cross-situational/time distribution or regularity of appraisal, affect, motivation and policy. | Identity, mood, current behavior. |
| **Self-model** | Self-referential belief/model of own identity, capability, state, history, roles, commitments or likely behavior. | Authoritative self/identity truth. |
| **Development** | Longer-horizon structured change of a Subject across multiple dimensions. | Monotonic improvement. |

---

# 4. Learning — experience-linked future difference

R13's early definition was:

```text
Learning = experience changes future policy/model
```

R27 generalizes it:

```text
Learning(S, E) occurs when
an experience/evidence-linked update is retained enough
that a relevant future inference, prediction, evaluation,
selection, control mapping or policy is counterfactually different.
```

The causal test:

```text
Past experience E happened
vs
counterfactual E did not happen

after transient state differences have been controlled

→ does future Subject state/policy differ?
```

If yes, E is learning-causal at that boundary.

## 4.1 Learning can be good or bad

```text
Learning != Improvement
```

A Subject can learn:

```text
false causal association
maladaptive avoidance
superstition
bad opponent model
overfit policy
self-defeating habit
misinformation
```

Learning is a change relation, not a quality judgment.

## 4.2 Learning can remain latent

```text
Learning != immediate PerformanceChange
```

A world model may update now and affect action only when a later opportunity appears.

## 4.3 Performance can change without learning

Examples:

```text
fatigue
injury
luck
temporary arousal
external hint
new equipment
one-off buff
changed opponent
changed environment
```

Thus:

```text
PerformanceChange != Learning
```

---

# 5. Experience, exposure, feedback and attribution

A strong learning pipeline is not:

```text
repeat event N times → learn
```

It is closer to:

```text
Experience
→ Observation
→ Attribution / discrepancy / evidence relevance
→ Learning target selection
→ Update
→ Retention
→ Future use
```

R12 established that feedback must make causality sufficiently legible when mastery matters. R27 adds:

```text
FeedbackQuality matters because
Subjects update from interpreted evidence,
not from designer ground truth automatically.
```

## 5.1 Feedback != attribution

Same observed outcome can support different updates:

```text
“I failed because my timing was wrong.”
“I failed because the weapon is weak.”
“I failed because the game cheated.”
```

Only the first necessarily trains timing.

## 5.2 Attribution can be false yet causal

R17 applies:

```text
WorldTruth != Belief
```

A false causal attribution can produce real future policy change.

---

# 6. Learning Target Topology

R27 introduces:

```text
LearningTargetTopology =
which Subject layers can be changed by experience,
through which evidence/update rules,
at which timescales.
```

Targets include:

```text
World model / Belief
Value / Incentive representation
Preference calibration
Goal proposal / selection policy
Action policy
Skill / Control mapping
Habit / cue-response mapping
Attention / salience allocation
Risk / uncertainty calibration
Relationship expectation / trust
Identity content / self-model
Affective appraisal tendency
Emotion-regulation strategy
Meta-learning / update rate/rule
```

The target matters more than the generic label “learned.”

---

# 7. Update operator

A generic learning transition can be represented as:

```text
S_(t+1) = Update(S_t, Evidence_t, Context_t, Rule_t)
```

where `Update` may modify only selected layers.

R27 does **not** require a universal delta rule.

Possible update families include:

```text
associative update
prediction-error update
Bayesian/evidence-weighted belief revision
rule induction
map/model construction
reinforcement
imitation/social learning
instruction
practice / control calibration
habitization
reflection/reappraisal
institutional teaching
model-mediated synthesis
```

---

# 8. Prediction error — powerful signal, not Learning itself

```text
PredictionError = observed outcome - predicted outcome
```

in an appropriate represented space.

Prediction error can help determine update magnitude/direction, but:

```text
PredictionError != Learning
```

because:

- some errors are ignored;
- update can be gated by attention/confidence/context;
- latent/map learning need not be described solely as scalar reward prediction;
- instruction may update a model before direct prediction error;
- habit/skill/model/value systems can use different signals.

Never replace the whole R27 layer with one RL scalar.

---

# 9. Learning rate — evidence weighting, not intelligence

```text
LearningRate =
how strongly current evidence changes a specified target
under a specified context/model.
```

Behrens-style volatility results motivate:

```text
highly volatile environment
→ newer evidence may deserve greater weight
```

while a stable environment may justify slower revision.

Thus:

```text
HighLearningRate != Smarter
LowLearningRate != Stubborn by definition
```

Both can be appropriate or maladaptive depending on environmental change rate and noise.

---

# 10. Belief Revision — epistemic learning

R17 already defines Belief as a Subject's epistemic state.

R27 defines:

```text
BeliefRevision =
Learning whose target is Belief / WorldModel / hypothesis state.
```

## 10.1 Information acquisition != revision

```text
new signal observed
```

does not guarantee:

```text
belief changed
```

because evidence may be considered unreliable, redundant, irrelevant or deceptive.

## 10.2 Revision != truth convergence

A well-formed update can still move away from truth under misleading evidence.

```text
BeliefRevision != TruthConvergence
```

## 10.3 Revision should retain provenance where stakes require

Useful state may include:

```text
claim
source
evidence
confidence
timestamp
contradictions
update history
```

not because every Game needs Bayesian inference, but because update causes can matter strategically.

---

# 11. Learning under uncertainty

R22 becomes directly relevant:

```text
Evidence
+ uncertainty about state/model/source
→ weighted update
```

The Subject may need to distinguish:

```text
outcome noise
model error
opponent adaptation
hidden state
one-off anomaly
structural regime change
```

The same surprise should not always produce the same update.

## 11.1 Volatility

```text
Volatility = how quickly the relevant process/model is changing
```

High volatility can justify faster belief/policy revision.

## 11.2 Noise

High noise can justify **slower** reaction to individual samples.

Therefore:

```text
Uncertainty != Volatility != Noise
```

and learning rate should not be hard-coded from surprise alone.

---

# 12. Memory — past-derived functional availability

R13's definition remains strong:

```text
Memory = past information available to future cognition
```

R27 sharpens it:

```text
Memory =
past-derived traces / information / retained state
that can become functionally available
and change current/future cognition or action.
```

The key word is **functional**.

```text
StoredPast != FunctionalMemory
```

## 12.1 Database storage is not enough

A million archived messages that are never retrieved at the right time do not provide functional memory.

## 12.2 Memory can be implicit in policy

A learned motor/behavioral policy can carry past influence without explicit episode retrieval.

This is why:

```text
Memory != EpisodicRecall
```

---

# 13. Memory roles rather than one universal memory system

For Game foundations, distinguish functional roles:

```text
Active / working state
Episodic event trace
Semantic/world knowledge
Procedural/skill trace
Habit/policy trace
Affective trace
Relational trace
Identity/self trace
Institutional/external memory
```

These are not mandatory biological modules.

The point is that:

```text
what past information must influence what future operation?
```

should be answered before choosing storage architecture.

---

# 14. Encoding, trace, retrieval, reconstruction

Useful pipeline:

```text
Experience
→ Encoding / trace formation
→ Consolidation / compression / integration
→ Retained trace
→ Retrieval cue
→ Reconstruction / activation
→ Current use
→ possible update / re-storage
```

## 14.1 Encoding != storage

Not every observed detail becomes a retained trace.

## 14.2 Retrieval != replay

Retrieval may be partial, cue-dependent and reconstructive.

## 14.3 Reconstruction != arbitrary hallucination

A reconstructive system can still be constrained by provenance/evidence.

---

# 15. Memory can change when used

Reconsolidation/reconstruction evidence falsifies an overly simple model:

```text
write once
read forever unchanged
```

R27 permits:

```text
retrieval
→ current interpretation/context
→ update/integration
→ modified future memory
```

when the intended Subject model needs it.

Do not infer that every Game memory read should mutate state. The lesson is only that immutability is an implementation choice, not the essence of memory.

---

# 16. Forgetting — reduced influence, not necessarily deletion

```text
Forgetting =
reduction or loss of accessibility / retrievability / future influence
of a past-derived trace.
```

Possible mechanisms:

```text
physical deletion
decay
interference
retrieval failure
context mismatch
compression into abstraction
overwrite/reconsolidation
intentional suppression/pruning
```

Therefore:

```text
Forgetting != Deletion
```

## 16.1 Forgetting can be useful

Long-lived systems need:

```text
salience
compression
pruning
contextual retrieval
```

not infinite equal-weight accumulation.

Forgetting can protect current relevance and reduce stale-policy interference.

---

# 17. Generalization and transfer

```text
Generalization =
learned change affects cases beyond the exact experienced instance.
```

```text
Transfer =
learned structure from one context/task influences another.
```

## 17.1 Exact memorization is not always learning depth

A Subject can remember one exact puzzle solution without learning a transferable principle.

## 17.2 Generalization can be wrong

```text
one hostile merchant
→ “all merchants are hostile”
```

is learning plus overgeneralization.

Thus:

```text
Generalization != Improvement
```

---

# 18. Contextual learning

Many learned policies should be context-bound.

```text
Policy(context A) != Policy(context B)
```

A Subject can learn:

```text
this person is reliable in combat
but unreliable with secrets
```

or:

```text
this movement mapping applies only while wearing equipment X
```

Context specificity is not necessarily failure to generalize.

---

# 19. Skill — learned capability / control structure

R21 defines Skill as:

```text
learned ability to produce reliably better task-relevant action/decision
```

R27 places Skill as one learning target/outcome.

```text
Learning
→ control mapping / prediction / decision structure changes
→ Skill
```

## 19.1 Skill != knowledge

A player can explain a timing mechanic but fail execution.

## 19.2 Knowledge != skill

A Subject can acquire semantic knowledge without improved action capability.

## 19.3 Skill can exist without episodic memory of training

Amnesia studies make this a high-value falsifier.

---

# 20. Habit — learned policy compression

Use `Habit` cautiously:

```text
Habit =
learned cue/context-linked response policy
relatively less dependent on current explicit goal/outcome-value reasoning.
```

The term is useful when it creates a causal distinction such as devaluation sensitivity.

Do not assume:

```text
habit = repeated behavior
habit = permanent behavior
habit = irrational behavior
```

R18 already warned that reactive/habit-like action need not require deliberative motivational machinery.

---

# 21. Goal-directed learning versus habit learning

Goal-directed action can depend on:

```text
Action → Outcome model
+
current Outcome Value
```

Habit-like action can depend more strongly on:

```text
Cue / Context → Response mapping
```

This yields a useful Game distinction:

```text
same past practice
→ two Subjects may produce similar current action
but respond differently after value/contingency changes.
```

The difference becomes playable only when such changes are observable and consequential.

---

# 22. Adaptation — fit change, not necessarily durable learning

R27 defines:

```text
Adaptation =
change in behavior/state/configuration that alters actor–environment fit
under current conditions.
```

Examples **with** learning:

```text
learn enemy pattern
calibrate motor control
update opponent model
learn new language convention
```

Examples that can adapt performance **without** internal durable learning:

```text
temporary equipment assistance
external advisor
automatic difficulty compensation
context switch to existing policy
physiological acclimation at another modeled layer
one-session cached state that is discarded
```

Thus:

```text
Learning != Adaptation
```

---

# 23. Learning without adaptation; adaptation without learning

## 23.1 Learning without immediate adaptation

```text
latent world knowledge
learned but currently unused strategy
memorized clue before it becomes relevant
learned opponent tendency while still losing
```

## 23.2 Adaptation without learning

```text
activate pre-existing cold-weather policy
receive aim assist
borrow better tool
change role assignment
```

The system fits current conditions better, but no durable experience-driven internal update is required.

---

# 24. Adaptation can be maladaptive elsewhere

A policy optimized for one environment can reduce fitness/value in another.

```text
LocalAdaptation != GlobalImprovement
```

Examples:

```text
stealth habit harms open combat
high-volatility learning rate overreacts in stable world
relationship defensiveness learned after betrayal harms new friendships
```

This links learning to R22 uncertainty and R25 relationship history.

---

# 25. Relearning and savings

```text
Savings =
faster/easier reacquisition after apparent loss of prior performance
because some past-derived structure remains.
```

Savings demonstrates:

```text
CurrentPerformanceBaseline
!= NoMemory
```

A Subject may appear “back to zero” behaviorally while latent trace/strategy selection remains changed.

This is another reason to avoid inferring internal learning state from current performance alone.

---

# 26. Meta-learning — changing the update process

```text
MetaLearning =
experience changes how future learning itself operates.
```

Possible targets:

```text
learning rate
attention to evidence
exploration policy
source trust
feature selection
strategy selection
memory allocation
transfer rule
```

Volatility-sensitive evidence weighting is one modest example:

```text
learn not only “what is valuable?”
but “how quickly should I revise value here?”
```

Do not require meta-learning in ordinary NPCs.

---

# 27. Personality — slow regularity, not immutable essence

R27 defines:

```text
Personality =
relatively stable cross-situational/time distribution or regularity
of appraisal, affect, motivation and policy.
```

This is deliberately distributional.

## 27.1 Personality != current behavior

A normally cautious Subject can act recklessly in one emergency.

## 27.2 Personality != Mood

Mood is a more transient affective background from R26.

## 27.3 Personality != Identity

R24 identity concerns continuity/referent and identity content. Personality concerns recurring behavioral/internal-state patterns.

## 27.4 Personality can change

Longitudinal research falsifies:

```text
Personality = fixed forever
```

but substantial stability falsifies:

```text
Personality = current context only
```

---

# 28. Personality as compression versus causal state

A trait can be used in two ways:

```text
Descriptive personality:
observed distribution → trait summary

Causal personality:
trait variable → biases appraisal/motive/policy generation
```

These must not be conflated.

Game rule:

> Do not add a causal personality variable merely because a descriptive label sounds plausible.

If lower-level state already produces the intended regularity, the trait may be redundant compression.

---

# 29. Personality Causality test

A personality variable is causally justified when:

```text
same immediate world
same current goal
same information

but different slow trait/disposition state
→ systematically different appraisal / policy distribution
```

and that distinction matters to play.

Otherwise personality can remain descriptive lore.

---

# 30. Personality development

Personality change can arise through:

```text
repeated learning
role investment
relationship history
identity change
habit formation/extinction
skill development
affective regulation changes
institutional/social environment
major events
```

R27 therefore treats personality as potentially **emergent from persistent multi-layer change** rather than an isolated learning subsystem.

---

# 31. Self-model — self-referential epistemic model

R24 defined:

```text
SelfModel =
Subject's model of own identity/history/roles/capabilities/commitments
```

R27 generalizes:

```text
SelfModel =
self-referential belief/model state about
own identity, body, capability, current state,
history, motives, roles, relationships,
commitments and likely future behavior.
```

It belongs primarily to the epistemic/model layer.

---

# 32. Self-model != Self / Identity Authority

```text
SelfModel != Self
SelfModel != EntityIdentity
SelfModel != IdentityAuthority
SelfModel != WorldTruth
```

A Subject can be wrong about itself.

Examples:

```text
“I cannot win this fight.”
“I am still a novice.”
“I never break promises.”
“I am hated by the guild.”
```

All may be false yet behaviorally causal.

---

# 33. Self-efficacy as a minimal self-model case

Self-efficacy provides a useful minimal example:

```text
BeliefAboutOwnCapability
→ effort / persistence / approach policy
```

while:

```text
ObjectiveCapability
```

may remain unchanged.

Thus self-model is not merely introspective lore.

```text
SelfModelCausality =
same objective capability/world
+ different self-belief
→ different reachable chosen futures
```

---

# 34. Self-model updating

Possible evidence:

```text
success/failure
social feedback
body state
role change
new capability
comparison
institutional recognition
memory retrieval
reflection
```

Possible failures:

```text
underconfidence
illusion of control
overconfidence
identity lag
learned helplessness
false autobiographical belief
```

Self-model learning is therefore a special case of Belief Revision with `Self` as the modeled object.

---

# 35. Self-model minimum complexity

## SM0 — none

Fixed reactive policy. No explicit self-reference.

## SM1 — local capability estimate

```text
Can I execute action X?
```

## SM2 — state / resource / role awareness

```text
What can I do now and under what constraints?
```

## SM3 — history / commitment / relationship self-model

```text
What have I done / promised / become?
```

## SM4 — reflective model revision

```text
How should evidence change what I think about myself?
```

This is not a maturity ladder. Use the cheapest level that creates the intended counterfactual.

---

# 36. Development — structured change across targets

R27 uses:

```text
Development =
longer-horizon structured Subject change
across one or more layers.
```

It may include:

```text
skill growth
belief revision
habit formation
value change
relationship development
identity transformation
personality shift
self-model revision
physical decline
specialization
```

Therefore:

```text
Development != Progression
Development != Improvement
```

A tragedy can produce coherent development with worse capabilities or relationships.

---

# 37. Persistent Subject Change

This is R27's main synthesis abstraction:

```text
PersistentSubjectChange =
retained change to one or more Subject layers
whose causal effects survive the immediate episode
and alter later state transitions or reachable policies.
```

Possible layers:

```text
Belief
Value
Goal-selection policy
Skill
Habit
Attention
Risk calibration
Relationship expectation
Identity content
Self-model
Affective baseline
Regulation policy
Meta-learning rule
```

Learning is the experience-linked subset of Persistent Subject Change.

---

# 38. Persistent Change Topology

R27 introduces:

```text
PersistentChangeTopology =
which experiences can update which Subject layers,
which layers influence which others,
which persistence boundaries apply,
and which authorities may perform the update.
```

Example:

```text
Failure
→ belief about boss pattern
→ self-efficacy
→ fear appraisal
→ approach policy
→ new experience
```

or:

```text
Betrayal
→ trust evidence
→ relationship state
→ generalized social belief
→ defensive habit
→ personality-like distribution shift
```

This is more informative than one `XP` variable.

---

# 39. Update Authority

Not every actor may mutate every layer.

```text
UpdateAuthority(target) =
which process/entity is allowed to authoritatively change target state.
```

Examples:

```text
World evidence      → candidate belief update
Player command      → goal/intention, not direct trust mutation
Institution         → role/status/record
Subject learning    → own belief/policy
Designer script     → authored development transition
Model provider      → implementation behavior, not character state automatically
```

This extends R24 Identity Authority and R25 Relational Authority.

---

# 40. Learning provenance

Persistent change should be explainable enough when continuity matters:

```text
UpdateProvenance =
what experience/evidence/rule caused this retained change?
```

Useful for:

```text
belief corrections
trust changes
skill acquisition
identity development
self-model revision
Agent migration
```

Without provenance, generative systems can retroactively invent “learning” to justify arbitrary drift.

---

# 41. Learning timescales

Different targets should update on different timescales.

```text
working belief / local estimate    fast
opponent model                     fast-medium
skill calibration                  medium
habit                              medium-slow
trust                              evidence-dependent
identity content                   slow/event-driven
personality regularity             slow/statistical
meta-learning rule                 slow/contextual
```

No universal rates.

R23 applies:

```text
UpdateTimescale should match
how quickly the modeled causal structure can actually change.
```

---

# 42. Fast adaptation versus slow identity/personality change

A persistent Agent can switch tactics immediately without “becoming a different person.”

```text
PolicyAdaptation fast
IdentityChange slow
PersonalityChange slower/statistical
```

But major events can cause discontinuous changes when supported by causal history.

The important rule is:

```text
RateOfChange != OntologicalLayer
```

Do not derive personality from one emotional turn.

---

# 43. Player learning versus Subject learning

These must remain separate:

```text
PlayerLearning
!=
CharacterLearning
!=
AgentImplementationLearning
```

## 43.1 Player learning

Human player improves model/skill across play.

## 43.2 Character/Subject learning

Diegetic entity retains changed belief/policy/capability.

## 43.3 Implementation learning

Underlying ML model/fine-tuning/provider behavior changes.

These can occur independently.

---

# 44. Roguelike falsifier

World state resets:

```text
WorldMemory ≈ reset
Character maybe reset
PlayerLearning persists
```

Player can become dramatically better without any persistent character progression.

Refutes:

```text
Learning requires persistent in-world state.
```

---

# 45. Pattern boss falsifier

Boss uses fixed deterministic policy.

Player learns:

```text
pattern
windows
risk
control
```

Boss never adapts.

Strong game learning does not require adaptive enemies.

```text
PlayerLearningDepth != OpponentLearningComplexity
```

---

# 46. Stealth guard falsifier

Guard may only need:

```text
observation
→ belief update
→ search policy
```

No personality, episodic autobiography or meta-learning required.

This is enough for meaningful epistemic adaptation.

---

# 47. Authored character falsifier

A fully scripted character can diegetically learn if:

```text
experience state A
→ authored persistent transition
→ later policy/dialogue/relationship differs because of A
```

Online ML is not required.

```text
DiegeticLearning != MachineLearning
```

---

# 48. Generative Persona falsifier

A Persona can produce apparently adaptive language from a long prompt/context while retaining no durable state after reset.

Therefore:

```text
ContextualResponseVariation != PersistentLearning
```

Conversely, a simple structured memory/policy update can create genuine persistent learning without model fine-tuning.

---

# 49. Model fine-tuning and provider updates

If the underlying model is retrained:

```text
Implementation changed
```

but this does not automatically mean:

```text
Character learned from its diegetic experience.
```

Need explicit provenance/mapping from diegetic experience to model change.

Thus:

```text
ModelTraining != CharacterLearning by default
```

---

# 50. Retrieval-augmented memory

External retrieval can provide functional memory when:

```text
Past trace
→ selected/retrieved at relevant time
→ changes current model/policy
```

But:

```text
VectorStoreExists != MemoryWorks
```

and:

```text
RetrievalHit != CorrectMemory
```

Provenance, relevance, recency and conflict handling remain important.

---

# 51. Generative learning debt

```text
Generated “I learned X”
→ update/provenance debt

Generated memory
→ trace/history debt

Generated changed belief
→ evidence/revision debt

Generated new skill
→ capability/practice debt

Generated habit
→ history/context-sensitivity debt

Generated personality shift
→ slow-pattern/development debt

Generated self-realization
→ self-model evidence/continuity debt

Generated “I have changed”
→ persistent-change debt
```

Language can cheaply claim transformations that future behavior cannot support.

---

# 52. Learning Causality

R27 introduces:

```text
LearningCausality =
a past experience/evidence difference
counterfactually changes a later Subject state transition,
prediction, choice, control or policy
through a retained update.
```

Test:

```text
same current world
same capabilities
same immediate input

but different relevant prior experience
→ different later behavior/model?
```

If yes, learning is causal.

---

# 53. Adaptation Causality

```text
AdaptationCausality =
change in actor–environment fit
counterfactually depends on a changed configuration/policy/state
relative to current conditions.
```

Learning may or may not be the source.

This lets Game distinguish:

```text
learned adaptation
temporary compensation
external assistance
context switching
```

without semantic collapse.

---

# 54. Playable Learning

R27 adds:

```text
PlayableLearning =
learning structure whose relevant evidence,
retained changes, transfer limits and future policy effects
can be observed/inferred/tested/influenced enough
that learning itself becomes part of meaningful play.
```

Possible forms:

```text
player mastery
teaching an NPC
training companion skill
shaping opponent expectation
socializing trust/norms
learning enemy patterns
building a world model
```

Learning need not be visible as XP.

---

# 55. Playable Adaptation

```text
PlayableAdaptation =
adaptive response whose cause/scope/limits
can be understood and strategically used or countered.
```

Examples:

```text
enemy changes tactic after repeated exploitation
world ecology responds to extraction
companion develops trust-specific behavior
```

Unplayable adaptation:

```text
system silently counters whatever the player does
with no stable evidence or exploitable structure
```

This becomes opaque difficulty, not adaptive depth.

---

# 56. Learning Contract

R27 introduces:

```text
LearningContract = {
  WhatCanChange,
  FromWhatEvidence,
  WhoCanUpdateIt,
  UpdateTimescale,
  RetentionBoundary,
  GeneralizationScope,
  ForgettingRule,
  ResetRule,
  Observability,
  Reversibility
}
```

This is analogous to R22 UncertaintyContract and R23 TemporalContract.

A player-facing adaptive system becomes more legible when this contract is stable enough to infer.

---

# 57. Teaching as action on another Subject's learning

Teaching is not just communication.

```text
Teaching =
action intended to cause another Subject's retained model/policy/capability update.
```

Possible mechanisms:

```text
instruction
demonstration
feedback
practice design
reward/punishment
scaffolding
questioning
```

Teaching becomes gameplay when learner update has causal future consequences.

---

# 58. Adversarial teaching / manipulation

R17 deception and R19 strategy apply:

```text
Signal
→ other Subject update
→ future policy
```

A player can deliberately teach a false model:

```text
repeat feint
→ opponent learns expectation
→ exploit learned expectation later
```

This is strategic action on LearningCausality.

---

# 59. Exploration and learning

R22 information value becomes:

```text
Action
→ evidence
→ retained update
→ improved/different future policy
```

Exploration is valuable when its information can update something useful.

```text
InformationGain without retention/use
!= LearningValue
```

---

# 60. Learning and emotion

R26 connects bidirectionally:

```text
Emotion
→ attention / encoding / interpretation / regulation
→ Learning

Learning
→ new appraisal / expectation
→ Emotion
```

A fear response can itself be learned; learned safety can change future fear appraisal.

Do not collapse emotion into reinforcement signal.

---

# 61. Learning and relationships

R25:

```text
Past treatment
→ trust / expectation / commitment
→ future relationship policy
```

This is relational learning.

But relationship state is not merely a learning variable because shared/institutional relationship facts can exist independently of one Subject's learned attitude.

---

# 62. Learning and identity

R24:

```text
Identity != Memory
```

R27 adds:

```text
identity content / self-model
can change through learning
without numerical identity break.
```

A Subject can learn something about itself and transform identity content while remaining the same entity.

---

# 63. Learning and institutions/culture

R15 showed:

```text
Norm = SharedExpectation + DistributedEnforcement
Institution = history compressed into future interaction structure
```

R27 adds that subjects can learn norms/institutional expectations.

But collective culture is not reducible to individual learning alone:

```text
shared symbols
public practices
transmission
ritual
collective memory
legitimacy
```

may have external/public structure.

This residual is important for the next frontier.

---

# 64. Minimum persistent-change complexity

Not a maturity ladder.

## PC0 — Fixed policy

No experience-linked retained change.

## PC1 — Single targeted trace/update

```text
simple association
counter
last-known state
```

## PC2 — Context-sensitive belief/policy/skill learning

Different evidence can update different targets.

## PC3 — Multi-timescale memory + generalization

```text
episodic/semantic/procedural-like roles
context transfer
forgetting
```

## PC4 — Relational/self-development

```text
trust
self-model
identity content
regulation strategy
```

## PC5 — Meta-adaptive persistent Subject

```text
multiple targets
changing update rules
personality-like slow regularities
persistent cross-session ecology
```

Core rule:

```text
Increase persistent-change complexity
only when it creates a new playable learning/adaptation counterfactual.
```

---

# 65. Cross-form falsification tests

## 65.1 Chess

The game itself need not learn. Human learning can create enormous mastery depth.

Refutes:

```text
A deep game needs adaptive game Subjects.
```

## 65.2 Pattern action boss

Fixed boss + player learning can produce high skill.

## 65.3 Roguelike

World resets while player learning persists.

```text
Persistence boundary differs by layer.
```

## 65.4 Mystery / Casefile

Player and investigator Subject can acquire evidence and revise beliefs without changing personality.

## 65.5 Stealth guard

One local belief update is enough for search adaptation.

## 65.6 Motor/action skill

Player can acquire skill not reducible to declarative rule knowledge.

## 65.7 Social-deduction opponent

Belief/type learning matters; exact reward learning may be irrelevant.

## 65.8 Rival

Opponent-specific learning can coexist with stable personality.

## 65.9 Companion

Relationship history can update trust and behavior while identity remains stable.

## 65.10 Amnesiac character

Can retain procedural/skill dispositions without episodic recollection.

Refutes:

```text
No episodic memory → no learning.
```

## 65.11 Authored RPG

Scripted persistent transitions can be diegetic learning without ML.

## 65.12 Creative sandbox

Player learns material/tool grammar; game world need not adapt.

## 65.13 Generative Persona

Long context can imitate short-term adaptation without durable persistent change.

## 65.14 Persistent Agent

Needs explicit target/update/retention/provenance semantics if it is claimed to learn across sessions.

## 65.15 Same model, separate Agents

Shared model weights do not imply shared learned character state.

## 65.16 Model migration

Character learning can persist across provider/model migration if canonical learned state is external/portable.

---

# 66. Major failure modes

## 66.1 Experience = learning

Repeated exposure assumed to produce update.

## 66.2 Performance = learning

Luck, fatigue or assistance misread as retained change.

## 66.3 Improvement = learning

Maladaptive or false learning becomes impossible to model.

## 66.4 Learning = reward update

Belief, skill, imitation, instruction and map learning disappear.

## 66.5 Prediction error = universal learning

All update mechanisms forced into one scalar discrepancy.

## 66.6 Memory = database

Stored data that never influences current cognition is called functional memory.

## 66.7 Memory = history

World event log and Subject-accessible past collapse.

## 66.8 Retrieval = replay

Reconstruction/context/provenance ignored.

## 66.9 Forgetting = deletion

Interference, retrieval failure and compression become unrepresentable.

## 66.10 More memory = smarter

Salience and relevance disappear under accumulation.

## 66.11 Belief acquisition = belief revision

Signals silently overwrite epistemic state.

## 66.12 Belief revision = truth convergence

Misleading evidence cannot create learned false belief.

## 66.13 High learning rate = intelligence

Noise causes catastrophic overreaction.

## 66.14 Low learning rate = stubbornness

Stable environments cannot reward conservative updating.

## 66.15 Adaptation = learning

Temporary compensation becomes permanent internal development.

## 66.16 Learning = adaptation

Latent knowledge is ignored because performance has not improved.

## 66.17 Skill = knowledge

Motor/timing/control learning collapses into facts.

## 66.18 Habit = repetition

Any frequent action mislabeled habit.

## 66.19 Habit = permanent

Context/value change cannot alter learned policy.

## 66.20 Personality = trait vector

One static set of scores becomes the character.

## 66.21 Personality = current behavior

Contextual variation appears as identity/personality instability.

## 66.22 Personality = identity

Referent continuity and behavioral regularity collapse.

## 66.23 Personality = mood

Temporary affect becomes long-term character change.

## 66.24 Self-model = world truth

False confidence/amnesia/mistaken identity become impossible.

## 66.25 Self-model = identity

Believing “I am king” changes numerical identity automatically.

## 66.26 Model output drift = development

LLM variation is retrospectively justified as learning.

## 66.27 Long context = memory

Prompt length substitutes for selective past→future causality.

## 66.28 Fine-tune = character learning

Implementation update is mistaken for diegetic experience-linked change.

## 66.29 Generated memory = learned history

Language invents unsupported traces.

## 66.30 Generated self-realization = development

One line rewrites personality/identity without causal bridge.

## 66.31 Every NPC learns

Adaptive complexity is added where fixed readable policy would create more mastery.

## 66.32 Perfect opponent adaptation

Opponent counters every strategy immediately, destroying learnability and stable skill.

## 66.33 No forgetting

Stale interactions accumulate indefinitely.

## 66.34 Universal generalization

One experience updates every similar context.

## 66.35 Zero generalization

Every instance must be relearned from scratch.

## 66.36 Hidden adaptation

System silently changes without evidence, producing perceived cheating.

## 66.37 Learning without provenance

Persistent drift cannot be distinguished from bug/random generation.

## 66.38 One timescale

Beliefs, habits, trust, identity and personality all update equally fast.

---

# 67. R27 connections back to R1–R26

## R1–R4 — game form / mechanics / loops

Learning is already embedded in `Question → Choice → Consequence → Learning → Changed State → New Question`. R27 specifies what “Learning” must causally mean.

## R5–R7 — motivation / engagement / tension

Learning can create mastery and anticipation but does not itself guarantee fun/value.

## R8 — narrative

Character development can be experience-linked persistent change, but narration of change is not change itself.

## R9 — world

World truth and Subject learned model remain separate.

## R10 — Subject / Agent

Learning complexity should scale with role; Agent != adaptive learner by default.

## R11 — agency

Past learning changes current reachable/selected futures; adaptation must not remove meaningful player control.

## R12 — feedback

Learning depends on causal evidence/attribution being sufficiently legible when intended as mastery.

## R13 — history/memory

R27 expands the early definitions but preserves `StoredPast != FunctionalMemory` and `History becomes structure`.

## R14 — resources

Learning can alter resource valuation/allocation without becoming an economy variable.

## R15 — society/institutions

Subjects learn norms/roles; institutions can preserve shared change beyond individual memory.

## R16 — topology

Exploration grows usable world models; learned topology can differ from authoritative topology.

## R17 — information/belief

Belief Revision is an update process over the existing epistemic layer.

## R18 — motivation

Learning can change incentive value, preference calibration, goals and self-model, but reward/utility does not define all learning.

## R19 — strategy

Repeated games produce opponent-model learning, reputation and adaptation; hidden adaptive opponents can destroy readable strategy.

## R20 — creation

Creative learning can be skill/model development without changing the world authoring ontology.

## R21 — control/skill

Skill is one persistent-change target; fast sensorimotor adaptation and slow strategic learning can coexist.

## R22 — uncertainty

Noise/volatility/model uncertainty govern evidence weighting; learning itself can be uncertain and miscalibrated.

## R23 — time

Learning requires persistence across some temporal boundary; target-specific timescales matter.

## R24 — identity

Self-model and identity content can learn/change without breaking numerical identity.

## R25 — relationships

Trust, attachment-related expectations and relational contracts can be learned from history but shared relationship facts exceed one Subject's learning.

## R26 — affect

Affect influences encoding/attention/learning; learned expectations reshape future appraisal and emotion.

---

# 68. New high-yield abstractions

## 68.1 Learning Target Topology

```text
what layer changes from what experience/evidence?
```

## 68.2 Persistent Subject Change

```text
retained multi-layer change that alters later transitions/policies
```

## 68.3 Persistent Change Topology

```text
experience → target → update → persistence → downstream target
```

## 68.4 Update Authority

```text
who/process may authoritatively mutate which Subject layer?
```

## 68.5 Update Provenance

```text
which experience/evidence/rule caused the retained change?
```

## 68.6 Learning Causality

```text
past experience difference → retained later Subject difference
```

## 68.7 Adaptation Causality

```text
actor–environment fit difference caused by configuration/policy change
```

## 68.8 Learning Contract

```text
what can change / from what / how fast / how long / how generally / who can change it?
```

## 68.9 Playable Learning / Adaptation

Learning/adaptation becomes play when its evidence, boundaries, persistence and policy effects can be inferred and acted around.

---

# 69. Direct answers to the R27 synthesis questions

### Is Memory the missing foundation?

No. Memory was already partially founded in R13. R27 reveals the broader missing layer: persistent experience-driven Subject change. Memory is one mechanism/interface by which the past becomes available to current/future cognition.

### What is Learning?

Experience/evidence-linked retained update that causes a future inference, prediction, evaluation, control or policy to differ.

### Does learning require performance improvement?

No. Learning can be latent or maladaptive; performance can change through luck, fatigue, assistance or context without learning.

### Learning versus Adaptation?

Learning is experience-linked retained internal change. Adaptation is actor–environment fit change and can be temporary, external or pre-existing-policy selection. They overlap but are not equivalent.

### Memory versus storage/history?

Memory is functionally available past-derived influence. Storage is retained bytes/state. History is authoritative causal past. A stored event may never become functional memory; a learned skill can carry memory without episodic recall.

### Belief Revision versus Learning?

Belief Revision is epistemic learning. Learning also targets skill, habit, policy, value, regulation, relationships and self-model.

### Is prediction error the foundation of learning?

No. It is one powerful update signal. Instruction, model construction, imitation, habitization, practice and other processes need not reduce to one reward-prediction-error scalar.

### Personality primitive or emergent?

Usually treat it first as a slow distributional regularity/compression over appraisal, affect, motive and policy. Make a trait causally primitive only when it creates a necessary counterfactual not already produced by lower layers.

### Personality versus Identity?

Personality describes stable behavioral/internal-state patterns. Identity concerns referent continuity and identity content. Either can change while the other remains stable.

### Self-model independent foundation?

It is best treated as a self-referential Belief/Model subspace. It is important because false self-beliefs can change policy, but it is not world identity authority.

### What does a persistent Agent need to “learn” truthfully?

Explicit target state, evidence/update rule, retention boundary, provenance and downstream policy effect. Merely changing model outputs or retaining long context is insufficient.

### Can authored characters learn?

Yes, diegetically. If experience authoritatively changes later state/policy, the character learned even if the transition was scripted rather than produced by online ML.

### Does every adaptive enemy improve a game?

No. Hidden/instant counter-adaptation can destroy player learning. Adaptation must itself be legible/playable if it is a value-bearing mechanic.

---

# 70. Residual-dimension audit after R27

R27 resolves the major Subject-internal persistent-change cluster:

```text
Learning
Adaptation
Memory
Belief Revision
Skill / Habit
Personality
Self-model
Meta-learning
```

These no longer justify seven separate independent rounds by default.

However, one cross-Subject/world cluster remains noticeably under-founded.

R15 defined:

```text
Norm = SharedExpectation + DistributedEnforcement
```

but `Culture` itself remained mostly a named world dimension. R20 addressed taste/aesthetic judgment locally, R24 collective identity, R25 social bonds, and R27 learning/transmission, yet we still lack a first-principles account of:

```text
Culture
Convention
Tradition
Ritual
Symbol
Shared Meaning
Legitimacy
Custom
Collective Memory
Transmission
Cultural Change
Subculture
```

This is not reducible to Institution alone:

```text
Institution != Culture
Norm != Culture
CollectiveIdentity != Culture
RepeatedBehavior != Tradition
SharedBelief != SharedMeaning
Symbol != Meaning
Legality != Legitimacy
```

Therefore R27 identifies a credible remaining foundation frontier rather than entering product selection.

---

# 71. Exact next foundation round

The next round should be:

```text
R28 — Culture, Convention, Tradition, Ritual, Symbol, Shared Meaning, Legitimacy and Cultural Change
```

Transition:

```text
R27:
How does experience persistently change an individual Subject?

→ R28:
How do meanings, expectations, practices and symbols
become shared, transmitted and self-reproducing across Subjects and generations?
```

R28 should connect:

```text
R13 history/memory
R15 norm/institution
R17 information/communication
R18 value
R19 convention/strategy
R20 expression/taste
R23 time
R24 collective identity
R25 relationship/network
R27 learning/transmission
```

without collapsing culture into lore, norm, institution, aesthetics, ideology or population-wide prompt text.

Do not select a product before R28 and the subsequent whole-corpus synthesis/falsification pass.

---

# 72. R27 synthesis

The strongest compression is:

```text
Experience does not equal Learning.

Learning occurs when experience causes a retained change
that makes a relevant future Subject transition different.
```

A compact architecture is:

```text
World / Other Subjects
        ↓
Experience / Evidence / Feedback
        ↓
Observation + Attribution
        ↓
Learning Target
        ↓
Update Rule
        ↓
Retained Trace / Model / Policy / Skill / Relation / Self-model
        ↓
Retrieval / Activation / Generalization
        ↓
Future Appraisal / Prediction / Choice / Control
        ↓
Action / Outcome
        ↓
New Experience
        ↺
```

The strongest performance rule:

```text
PerformanceChange != Learning.
```

The strongest adaptation rule:

```text
Learning != Adaptation.
```

The strongest memory rule:

```text
Memory != Storage
and Retrieval != Replay.
```

The strongest epistemic rule:

```text
BeliefRevision != InformationAcquisition
and BeliefRevision != TruthConvergence.
```

The strongest personality rule:

```text
PersonalityStability != BehavioralRigidity.
```

The strongest self-model rule:

```text
SelfModel != WorldTruth / IdentityAuthority.
```

The strongest Agent rule:

```text
ModelFineTuning != CharacterLearning by default.
```

R27 adds:

```text
PersistentSubjectChange
LearningTargetTopology
PersistentChangeTopology
UpdateAuthority
UpdateProvenance
LearningCausality
AdaptationCausality
LearningContract
PlayableLearning
PlayableAdaptation
```

to the foundation vocabulary.
