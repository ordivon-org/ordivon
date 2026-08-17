# Ordivon Media Foundations — MF8-F Learning, Adaptation, Development & Plasticity

**Date:** 2026-08-18  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 53 at start  
**Input:** MF0–MF7 frozen; MF8-A/B/C/D/E complete/provisional.  
**Status:** **MF8-F COMPLETE / PROVISIONAL LEARNING-ADAPTATION ONTOLOGY. MF8 Agency Foundations are not frozen yet.**  
**Next:** MF8-G — Responsibility, Accountability, Credit, Blame & Liability.

---

# 0. Purpose

MF8-A already established:

```text
Learning ≠ Agency
Adaptation ≠ Agency
```

MF8-E added `SelfRevisionAutonomy?` as an autonomy dimension but deliberately deferred the ontology of update, learning and structural change.

MF8-F now reconstructs:

```text
Change / Update
Retention / Memory Acquisition
Learning
Training
Adaptation
Adaptability
Plasticity
Development
Maturation
Conditioning / Habituation / Skill Acquisition
Model / Policy / Value / Goal / Norm Learning
Self-Modification
Meta-Learning
Biological Evolution
Transfer / Forgetting / Interference
```

The central questions are:

1. What turns mere state change into learning?
2. Does learning require improvement?
3. Can adaptation occur without learning?
4. Can learning be maladaptive?
5. Is plasticity a change or a capacity for change?
6. Is development just slow learning?
7. What is the relation between training and learning?
8. If training occurred before deployment, did the deployed bearer itself learn?
9. Is changing a `value function` the same as changing values?
10. When is parameter change self-modification rather than externally imposed modification?
11. How do path dependence, forgetting and sensitive periods alter agency over time?
12. Does agency require any learning capacity at all?

---

# 1. Frozen substrate consumed, not reopened

MF8-F preserves:

```text
State ≠ History
Dynamics ≠ Learning
StateTransition ≠ Action
Adaptation ≠ Agency
Learning ≠ Agency
Policy ≠ Goal
RLValueFunction ≠ ValueStanding
WorldModel ≠ World
SelfModel ≠ Self
Autonomy ≠ Independence
```

MF7 supplies state, continuation, identity and stability. MF8-B/C/D/E supply action, evaluative orientation, policy/plan/decision, autonomy and world/self-model standings.

### F8-001
**No MF0–MF7 FoundationReopenCondition is triggered at MF8-F entry.**

---

# 2. ChangeStanding and UpdateStanding come before learning

A system can change for many reasons that have nothing to do with learning.

Neutral primitive:

```text
UpdateStanding(U, B, D | Σ)
```

holds when occurrence/process `U` changes some state, parameter, representation, disposition, structure, policy, memory, model, resource allocation or other declared domain `D` of bearer/system `B` under a preserved identity/continuation criterion.

Examples:

```text
clock increment
random bit flip
configuration overwrite
firmware replacement
parameter gradient step
memory append
synaptic change
policy table edit
model update
structural growth
```

### F8-002
**UpdateStanding ≠ LearningStanding.**

### F8-003
A change can be externally imposed, random, maturational, developmental, regulatory, degenerative, adversarial or purely mechanical.

### F8-004
The update domain, source, rule, evidence/history dependence and persistence must therefore be typed before calling a change learning.

---

# 3. Update provenance and authority

MF8-F introduces an update provenance profile:

```text
UpdateProvenance = <
  Trigger Source,
  Information/Experience Source,
  Update Executor,
  Update Rule Source,
  Update Target,
  Objective/Criterion Source?,
  Authorization Route?,
  Bearer Attribution?,
  Persistence / Reversibility,
  Scope
>
```

This allows:

```text
external trainer computes update
internal optimizer executes update
bearer selects data but not update rule
bearer selects update rule but not terminal objective
fully external parameter overwrite
self-directed structural revision
```

to remain distinct.

### F8-005
**Internal execution ≠ self-authored learning.**

### F8-006
**Externally caused update ≠ no learning**: learning is not restricted to autonomous agents. A passive/adaptive learner can undergo genuine learning under an externally supplied training process.

### F8-007
Self-modification and learning therefore require separate attribution analyses.

---

# 4. LearningStanding — provisional core

MF8-F defines:

```text
LearningStanding(L, B, D | H, Σ)
```

when a history/input/experience/training/evidence stream `H` non-trivially produces a **relatively persistent** update in bearer/system B's organization or dispositions in domain D such that B's future discrimination, representation, prediction, recall, evaluation, action selection, skill, control, or other relevant response/use is history-dependent in a way grounded in that update.

Key terms:

- `history/input/experience` is broad enough for sensory exposure, rewards, labels, demonstrations, self-generated data, training examples or interactions;
- `relatively persistent` means the update survives beyond the immediately eliciting event at the declared timescale/scope;
- the changed capability need not improve;
- generalization is optional, not constitutive;
- consciousness and agency are not required.

### F8-008
**Learning ≠ Improvement.**

### F8-009
**Learning ≠ Generalization.** One-shot episodic acquisition can count when retained and future-recruited.

### F8-010
**Learning ≠ ParameterChange.** Parameters may change without history-grounded learning; learning may occur through non-parameter memory or structural change.

### F8-011
**Learning ≠ MemoryAppend by identity.** A log write that never changes future bearer-relative use/response may be mere storage.

---

# 5. Persistence is scope-relative

If persistence required lifelong retention, short-term learning would be excluded.

MF8-F therefore distinguishes:

```text
TransientResponse
Context/Episode Retention
Short-Term Learning
Long-Term Learning
Developmentally Stabilized Learning
Cross-Instance/Persistent Artifact Learning
```

### F8-012
A history-dependent change can be genuine learning within a declared episode even if it disappears after reset.

### F8-013
But `current response depends on the immediately present input` is not sufficient; some retained/modified organization across relevant events must mediate future response.

### F8-014
Learning claims must state the retention horizon and reset boundary.

---

# 6. Learning without improvement

Several hard cases force this result.

## 6.1 Incorrect association

A system can acquire a false predictive relation.

## 6.2 Maladaptive conditioning / addiction-like learning

Learned cue/action structures can worsen long-term viability or reflective goals.

## 6.3 Overfitting

Training performance can improve while out-of-sample performance deteriorates.

## 6.4 Catastrophic interference

McCloskey & Cohen (1989) showed that new sequential learning in connectionist networks can severely disrupt previously learned mappings.

Therefore:

### F8-015
**LearningStanding does not imply monotonic capability growth.**

### F8-016
Learning can simultaneously create one capability and destroy another.

### F8-017
`More learning` is meaningless without domain, criterion and retained-capability profile.

---

# 7. Retention / memory acquisition

MF8-F needs only a narrow relation, not a full Memory ontology.

```text
RetentionStanding(R, B, X | H, Σ)
```

holds when information/organization X acquired/modified through history H remains available for future bearer-relative recruitment across the declared horizon.

### F8-018
**Retention ≠ Learning by identity.** Retention is one profile/condition of many learning routes.

### F8-019
A copied external record can persist without changing the learner's own practical/representational organization.

### F8-020
Conversely, synaptic/policy change can constitute learning without an explicit retrievable episodic record.

Kandel's work on memory storage and synaptic plasticity provides a strong biological route in which experience-dependent synaptic changes can support short- and long-term memory, while cell-biological work distinguishes structural/molecular plasticity from the behavioral phenomenon it helps realize.

---

# 8. Habituation and sensitization

Thompson & Spencer's classic habituation program establishes a minimal non-associative learning route in which repeated stimulation can produce systematic response decrement under diagnostic conditions, while sensitization can increase responsiveness.

MF8-F uses:

```text
HabituationStanding
SensitizationStanding
```

as typed learning routes rather than universal learning definitions.

### F8-021
**Learning does not require explicit reward, utility or goal.**

### F8-022
**Habituation ≠ fatigue/sensory adaptation by identity.** Diagnostic recovery, stimulus specificity and related tests matter because mere response decline can arise through non-learning mechanisms.

### F8-023
This demonstrates why observed behavior change alone does not ground LearningStanding without mechanism/history alternatives being tested.

---

# 9. Associative learning / conditioning

Provisional broad relation:

```text
AssociativeLearningStanding(R, B | H, Σ)
```

holds when history H changes bearer B so that relations among cues, actions, outcomes, events or contexts gain grounded predictive/evaluative/action-guiding standing for future use.

Possible routes include:

```text
Pavlovian / classical
instrumental / operant
action-outcome
stimulus-response
cue-value
social/observational
supervised statistical association
```

### F8-024
Associative learning ≠ all learning.

### F8-025
Acquiring predictive association ≠ adopting a goal or value by identity.

### F8-026
Reward-based training can alter policy/value estimates without creating intrinsic value provenance.

MF8-C remains binding.

---

# 10. SkillAcquisitionStanding

Learning can alter action organization without being primarily propositional/model learning.

```text
SkillAcquisitionStanding(S, B | H, Σ)
```

holds when training/practice/history produces relatively persistent improvement or restructuring in reliable action performance organization over a declared task/domain, potentially including speed, precision, robustness, sequencing, coordination or reduced deliberative burden.

Unlike LearningStanding generally, `skill acquisition` conventionally carries a competence/performance orientation.

### F8-027
**Skill acquisition is one learning profile, not the definition of learning.**

### F8-028
Skill execution can become automatic/habitual while remaining attributable to a higher-level intentional action, as established in MF8-B/E.

---

# 11. TrainingStanding

Training is an intervention/process, not the learning result.

```text
TrainingStanding(T, B | D, K, Σ)
```

holds when process T systematically structures exposures, examples, feedback, demonstrations, rewards, practice, curricula or update opportunities for bearer/system B in order to induce or shape learning in domain D under criterion K.

### F8-029
**Training ≠ Learning.** Training can fail.

### F8-030
**Learning ≠ Training.** Learning can occur incidentally, through exploration, interaction or self-generated experience without an externally organized training process.

### F8-031
Training objective/provenance must remain distinct from the learner's own values/goals.

---

# 12. Learning domain taxonomy

`Learning` is incomplete without saying **what changed**.

MF8-F distinguishes at least:

```text
Perceptual / Discrimination Learning
Representation Learning
Memory / Episodic Learning
World-Model Learning
Self-Model Learning
Predictive Model Learning
Policy Learning
Action-Value / Return-Estimate Learning
Reward-Model Learning
Preference Inference Learning
Preference Change
Goal Learning / Goal Discovery
Goal Adoption
Norm Learning / Norm Inference
Norm Internalization / Norm Change
Skill Learning
Habit Formation
Meta-Learning
Learning-Rule Adaptation
Structural / Architecture Learning
```

### F8-032
These update domains must not be collapsed.

---

# 13. `Value learning` is dangerously overloaded

In reinforcement learning:

```text
ValueFunctionLearning
```

usually means learning/estimating expected return under a formal reward structure.

That is not the same as:

```text
EvaluativeValueChange
```

where what actually matters to the bearer changes.

Nor is it the same as:

```text
PreferenceInference
```

where one system estimates another bearer's preferences.

### F8-033
**ValueFunctionLearning ≠ ValueStanding change.**

### F8-034
**Learning another agent's preferences ≠ changing one's own preferences.**

### F8-035
**Reward-model learning ≠ reward provenance change.**

This is one of MF8-F's most important artificial-agent firewalls.

---

# 14. Goal and norm learning are also overloaded

`Goal learning` can mean:

```text
infer what target another bearer pursues
learn a representation of an assigned goal
discover useful subgoals
adopt a new goal through decision/commitment
change one's evaluative goal organization
```

These are different.

Likewise `norm learning` can mean:

```text
infer a social rule
memorize policy text
learn to predict enforcement
internalize a norm into action guidance
revise one's own evaluative/norm standing
```

### F8-036
**GoalRepresentationLearning ≠ GoalAdoption ≠ GoalAutonomy.**

### F8-037
**NormInference ≠ NormInternalization ≠ NormAutonomy.**

---

# 15. Policy learning

```text
PolicyLearningStanding(Δπ, B | H, Σ)
```

holds when experience/training history changes the grounded conditional action-selection organization of B.

This can occur through:

```text
reinforcement learning
imitation
habit formation
supervised action prediction adopted as policy
evolutionary or search-based policy optimization
manual policy edits — only if the target bearer/lineage standing supports a learning route
```

### F8-038
**Policy change ≠ PolicyLearning automatically.** A human operator replacing one fixed rule file with another may be configuration change rather than learning of the deployed bearer.

### F8-039
Policy learning does not entail goal learning or goal autonomy.

---

# 16. Model learning

```text
ModelLearningStanding(ΔM, B | H, Target, Σ)
```

holds when history H produces persistent update in a grounded representation/model M of target structure.

Examples:

```text
transition model learning
system identification
world-model learning
self-model learning
other-agent model learning
uncertainty/calibration learning
```

### F8-040
**Model learning ≠ world change.**

### F8-041
**Prediction improvement ≠ model learning by identity** if improvement comes from a non-model cached mapping or policy.

MF3/MF8-E representation firewalls remain active.

---

# 17. AdaptationStanding

`Adaptation` must be criterion-relative.

Provisional:

```text
AdaptiveAdjustmentStanding(A, B | E, K, H, Σ)
```

holds when change/regulation A in bearer/system B, under environment/condition E, **preserves or improves** fit, viability, task performance, functional adequacy, norm satisfaction or another declared criterion K over horizon H relative to an appropriate baseline/counterfactual.

### F8-042
**Adaptation ≠ Change.**

### F8-043
**Adaptation ≠ Learning.**

### F8-044
`Adaptive` is meaningless without criterion K and horizon H.

---

# 18. Adaptation without learning

Examples:

```text
fixed homeostatic feedback
pupil constriction
prewired stress response
morphological response from an inherited reaction norm
thermostatic compensation
fixed controller selecting a condition-dependent mode
```

can preserve function/viability under changing conditions without history-dependent persistent learning.

Biological allostasis/homeostatic research similarly shows active regulatory change used to maintain viability or functional ranges under challenge; such regulatory adaptation need not itself be learning.

### F8-045
**Adaptive regulation can be memoryless/history-light at the relevant learning timescale.**

### F8-046
A fixed reaction mechanism can generate adaptive state changes without modifying its own policy/model/organization.

---

# 19. Learning without adaptation

Examples include:

```text
false association
addiction-like cue learning
maladaptive habit
overfitting
catastrophic forgetting
learning obsolete rules
socially learned harmful norm
```

### F8-047
**Learning can be maladaptive relative to one or more criteria.**

### F8-048
A learning process can be adaptive at one horizon and maladaptive at another.

### F8-049
`learning rate` and `adaptation quality` therefore belong to different profiles.

---

# 20. AdaptabilityStanding

Capacity for adaptation is not a realized adaptation.

```text
AdaptabilityStanding(B | D, K, Σ)
```

is the bearer/system's capacity to generate criterion-preserving/improving adjustments across a declared variation domain D.

### F8-050
**Adaptability ≠ AdaptationOccurrence.**

### F8-051
Adaptability may be supplied by fixed regulation, plasticity, learning, redundancy, planning, resource reserves or combinations thereof.

---

# 21. PlasticityStanding

`Plasticity` is primarily a capacity/susceptibility for change.

```text
PlasticityStanding(B, D | C, Σ)
```

holds when bearer/system B has a grounded capacity for its organization/phenotype/connection structure/parameters/behavior or other domain D to vary systematically under conditions/history C within a declared range/timescale.

Plasticity dimensions include:

```text
Target Domain
Trigger Conditions
Magnitude / Range
Rate
Reversibility
Persistence
Sensitive/Critical Window
Local/Global Extent
Cost
Constraint
Stability Tradeoff
Path Dependence
```

### F8-052
**PlasticityStanding ≠ PlasticChangeOccurrence.**

### F8-053
**Plasticity ≠ Learning.** Learning often consumes/uses plasticity but plastic changes can be developmental, regulatory or non-informational.

### F8-054
**Plasticity ≠ Adaptiveness.** Plastic responses can be neutral or harmful.

Neural literature explicitly treats synaptic plasticity as experience-dependent change in connectivity believed to underlie learning/memory, which supports mechanism/phenomenon separation rather than identity. Phenotypic-plasticity literature likewise studies environmentally responsive phenotype change, including cases that may or may not be adaptive.

---

# 22. Stability–plasticity tension

Learning systems face a nontrivial tradeoff:

```text
high plasticity
→ rapid incorporation of new structure
→ greater interference / instability risk

high stability
→ retention / robustness
→ slower adaptation to change
```

Catastrophic interference is an extreme artificial case of this general problem.

### F8-055
Plasticity and retention must be profiled jointly.

### F8-056
A system can be highly plastic yet poor at cumulative learning because new updates erase prior organization.

### F8-057
Learning capacity therefore cannot be inferred from update speed alone.

---

# 23. DevelopmentStanding

Development is not merely slow learning.

Provisional:

```text
DevelopmentStanding(P, B | O, H, Σ)
```

holds when process P constitutes an organized, identity-continuous transformation of bearer B across an ontogenetic/developmental horizon H, changing morphology, organization, capabilities, regulatory structure, representational/action possibilities or other developmental domain O under endogenous maturation and/or environment-dependent processes.

### F8-058
**Development ≠ Learning.**

### F8-059
**Development ≠ Growth.** Growth can be one component; development can involve differentiation, pruning, reorganization and capability loss/gain.

### F8-060
Development is bearer-history organized and stage/horizon sensitive, but not every developmental change is learned from idiosyncratic experience.

---

# 24. Maturation versus learning

```text
MaturationStanding
```

refers to developmentally organized change whose primary standing derives from bearer-internal/developmental program and expected environmental support rather than individual-specific acquired information.

```text
ExperienceDependentLearningStanding
```

is driven by individual-specific history/input.

Greenough, Black & Wallace's distinction between `experience-expectant` and `experience-dependent` information storage is especially useful here: development can require species-typical environmental input while remaining different from idiosyncratic individual learning.

### F8-061
**Experience dependence does not automatically make every developmental process `learning` in the narrow individual-specific sense.**

### F8-062
Development and learning can be deeply coupled while remaining distinct standing routes.

---

# 25. Sensitive and critical periods

Plasticity can itself change across development.

```text
PlasticityWindowStanding(W, B, D | Σ)
```

holds when domain D has an age/stage/condition-dependent interval W with substantially different susceptibility to experience-driven organization change.

### F8-063
Learning capacity is temporally structured, not fixed.

### F8-064
The same experience can have radically different effects at different developmental stages.

### F8-065
Development can therefore alter the future learning operator itself.

This is one route from development to meta-learning-like capacity change without collapsing the two.

---

# 26. Development can reduce capabilities

Development is not necessarily monotonic improvement.

Examples can include:

```text
synaptic pruning
loss of juvenile plasticity
specialization
tradeoff-driven capability narrowing
senescence-related later development/aging trajectories
```

### F8-066
**DevelopmentStanding ≠ capability increase.**

### F8-067
Maturation can close option/plasticity domains while improving efficiency/specialization elsewhere.

---

# 27. Ontogeny versus biological evolution

MF7 uses `EvolutionStanding` generically for state evolution. MF8-F must not confuse that with biological evolution.

Define separately:

```text
PopulationEvolutionStanding(Pop, G | Generations, Σ)
```

for cross-generational change in inherited population structure/trait distributions through selection, drift, mutation, recombination and related population processes.

### F8-068
**Individual Learning ≠ Biological Population Evolution.**

### F8-069
**Development ≠ Biological Evolution.**

### F8-070
An evolved learning/plasticity mechanism can shape individual development, while individual learning can alter selection pressures without acquired parameter changes being genetically inherited.

Baldwin's 1896 `new factor` and later developmental-plasticity work provide historical routes for exactly this interaction without Lamarckian identity.

---

# 28. Evolutionary adaptation versus adaptive adjustment

The word `adaptation` itself is overloaded.

Distinguish:

```text
AdaptiveAdjustmentStanding
  current bearer/process changes relative to criterion K

AdaptedStateStanding
  current configuration fits declared conditions/criterion

EvolutionaryAdaptationStanding
  trait/structure has historical standing as shaped/maintained by selection for relevant effects
```

### F8-071
**Current usefulness ≠ evolutionary adaptation by identity.**

### F8-072
**Evolutionary adaptation ≠ online adaptive adjustment.**

### F8-073
A trait can be historically selected yet maladaptive in a novel environment; a current adjustment can be adaptive without being inherited/evolutionary.

---

# 29. Training provenance versus deployed-bearer learning

This is a major artificial-agent boundary.

Consider:

```text
pretraining
→ frozen model artifact
→ deployment instance created
```

Did the deployment instance `learn` the training corpus?

The answer depends on bearer identity and standing route.

MF8-F distinguishes:

```text
TrainingHistoryStanding
LearnedArtifactStanding
Inherited/MaterializedCapabilityStanding
CurrentBearerLearningOccurrence
OnlineLearningCapacity
```

### F8-074
**Training occurred in the artifact lineage ≠ a learning occurrence happened in the current deployment episode.**

### F8-075
A deployed bearer can possess capabilities whose provenance is prior learning/training without itself currently learning.

### F8-076
If identity/continuation is explicitly drawn across training and deployment, historical learning may legitimately be attributed to the persistent artifact/system bearer; if a deployment instance is a new bearer, it inherits learned organization rather than re-performing the learning.

MF7 identity/continuation criteria therefore matter directly.

---

# 30. Fine-tuning, online learning and configuration update

Examples:

```text
post-deployment SGD update
persistent memory update
retrieval-index update
policy update from reward
manual prompt/config edit
human hotfix
model replacement
```

must be typed separately.

### F8-077
An externally applied fine-tune can constitute LearningStanding of a persistent model/artifact lineage while having low SelfRevisionAutonomy.

### F8-078
A manual configuration edit can change behavior without being learning of the bearer.

### F8-079
Replacing the entire model may be lineage/configuration change rather than learning of the previous bearer if identity continuity is not preserved.

---

# 31. In-context / episodic adaptation

A system can alter later responses based on earlier examples in the same context while frozen long-term parameters remain unchanged.

MF8-F therefore permits a typed route:

```text
ContextualLearningStanding(L, B | Episode, Σ)
```

when retained episode/context state causes history-sensitive future behavior beyond immediate stimulus response.

### F8-080
**Parameter update is not required for all learning.**

### F8-081
Contextual learning must declare reset horizon; session reset can destroy the learned standing beyond that scope.

### F8-082
Demonstration-sensitive behavior is not automatically learning if it can be explained as a purely stateless mapping from the entire current input; the relevant history/retention/bearer boundary must be made explicit.

This keeps `in-context learning` as a legitimate operational standing route without forcing one philosophical verdict on every transformer behavior.

---

# 32. Memory systems and external memory

External storage complicates bearer boundaries.

```text
Agent writes durable note
→ later retrieves note
→ behavior changes
```

This can participate in bearer-level learning if the storage/retrieval system is operationally recruited as persistent memory under the declared bearer boundary.

### F8-083
**Internal storage location is not constitutive to learning.**

### F8-084
But an external database the bearer never reads does not become its memory/learning merely because an analyst can access it.

MF8-E's internal/external/shared model rule generalizes here.

---

# 33. SelfModificationStanding

Self-modification is not mere internal update.

Provisional:

```text
SelfModificationStanding(M, B, D | Σ)
```

holds when bearer B's own agential/decision organization has grounded source/authority standing over the initiation and/or rule/target selection of an update that modifies B's own relevant organization in domain D.

Possible levels:

```text
Update Execution Autonomy
Update Target Autonomy
Update Rule Autonomy
Learning Objective Autonomy
Architecture/Structure Revision Autonomy
Verification/Rollback Autonomy
```

### F8-085
**Learning ≠ SelfModification.**

### F8-086
A model can learn under an external trainer with no self-modification standing.

### F8-087
A system can self-modify a configuration randomly/poorly without LearningStanding.

### F8-088
MF8-E's SelfRevisionAutonomy is therefore a vector over update governance, not `weights changed internally`.

---

# 34. Meta-learning

`Learning to learn` is also overloaded.

MF8-F uses:

```text
MetaLearningStanding(ΔΛ, B | Tasks, Σ)
```

when cross-task/history experience modifies B's learning organization `Λ`—priors, update rules, representation initialization, exploration strategy, curriculum sensitivity, adaptation rate or other learning-process structure—so subsequent learning dynamics differ systematically.

### F8-089
**Meta-learning ≠ ordinary task learning.**

### F8-090
Externally performed meta-training can produce a deployed bearer with rapid adaptation capability without giving the deployment episode autonomous control over its learning rule.

### F8-091
Fast adaptation after meta-training and self-authored learning-rule revision are different standings.

---

# 35. Learning rate, sample efficiency and learning quality

Keep distinct:

```text
UpdateRate
LearningRate parameter
SampleEfficiency
WallClockEfficiency
Retention
Generalization
Transfer
Robustness
Calibration
AdaptationQuality
```

### F8-092
A large optimizer `learning rate` is merely a formal update parameter; it does not mean the system learns more effectively.

### F8-093
Sample efficiency is task/model-relative and does not imply broad developmental flexibility.

### F8-094
Learning quality is multidimensional.

---

# 36. TransferStanding

```text
TransferStanding(B, D1, D2 | H, Σ)
```

holds when learning/history in domain D1 systematically affects acquisition/performance in D2.

Possible profiles:

```text
Positive Transfer
Negative Transfer
Zero Transfer
Near/Far Transfer
Forward Transfer
Backward Transfer / Interference
```

### F8-095
Transfer ≠ learning by identity; it is a cross-domain consequence/profile of learning history.

### F8-096
Positive transfer can increase future learning capability without changing the ontology of learning itself.

---

# 37. Forgetting and interference

```text
ForgettingStanding(F, B, X | H, Σ)
```

holds when previously available learned/retained organization X becomes less retrievable, less effective or unavailable over the declared horizon.

Possible causes include:

```text
decay
interference
overwrite
context shift
retrieval failure
structural damage
active suppression
model replacement
```

### F8-097
**Forgetting ≠ erasure by identity.** Retrieval failure and destructive overwrite differ.

### F8-098
**New learning can cause forgetting.**

### F8-099
Catastrophic interference demonstrates that learning and retention must be jointly modeled rather than assuming monotonic accumulation.

---

# 38. PathDependenceStanding

Learning/developmental outcomes can depend on order, not merely multiset of exposures.

```text
PathDependenceStanding(B, D | H, Σ)
```

holds when different histories/orderings through otherwise related input/experience domains produce materially different later organization/capabilities that are not reducible to current external conditions alone.

### F8-100
**History order can be constitutive to learned state.**

### F8-101
Curriculum, initialization and sensitive periods are therefore not incidental metadata when they alter reachable learning/development trajectories.

---

# 39. Developmental lock-in and canalization

Some developmental trajectories change future plasticity/reachability.

Provisional profiles:

```text
DevelopmentalLockIn
Canalization
SensitiveWindowClosure
Specialization
IrreversibleDifferentiation
```

### F8-102
Development can reshape the future option space of learning and agency.

### F8-103
Reduced plasticity can be adaptive through stability/specialization while also reducing future adaptation capacity.

This is a time-dependent capability tradeoff, not a contradiction.

---

# 40. Learning and identity continuity

Extreme updates can threaten the identity criterion of the learner.

If an update replaces enough organization that the declared bearer no longer satisfies MF7 continuation/identity criteria, then:

```text
old bearer learns radically
```

may be the wrong claim.

It may instead be:

```text
old bearer terminates
→ new bearer initialized from transformed artifact
```

### F8-104
Learning claims require bearer identity continuity across the update.

### F8-105
This is especially important for model replacement, fork/merge, destructive self-modification and institutional restructuring.

No MF7 reopen is needed; MF8-F consumes MF7 identity criteria.

---

# 41. Learning and autonomy

Learning capacity and autonomy are orthogonal dimensions.

Examples:

```text
externally trained adaptive filter:
  learning high
  goal autonomy low
  decision autonomy possibly none

fixed-policy autonomous controller:
  learning zero
  action autonomy high within domain

self-modifying agent:
  learning + self-revision autonomy potentially high
```

### F8-106
**LearningCapacity ≠ Autonomy.**

### F8-107
**SelfRevisionAutonomy ≠ LearningCapability.**

### F8-108
A bearer may be an agent with no online learning whatsoever.

---

# 42. Minimal agency does not require learning

Hard cases from MF8-A/E remain decisive:

- fixed but context-sensitive organisms/controllers can act without online learning;
- deterministic learned policies can continue acting after learning is disabled;
- delegated agents can retain agency standing under frozen policy/model organization.

### F8-109
**LearningStanding is NOT a universal constituent of minimal AgencyStanding.**

### F8-110
Learning is instead an agency capability/richness profile that can expand, reshape or degrade action/choice/model/evaluative organization over time.

---

# 43. Learning does not require agency

Conversely:

- a supervised classifier can learn parameters;
- an adaptive filter can learn coefficients;
- a biological circuit can habituate;
- a passive predictor can update a model;

without establishing the full bearer/action/evaluative/choice organization of AgencyStanding.

### F8-111
**LearningStanding does not imply AgencyStanding.**

This preserves MF8-A's original firewall.

---

# 44. Hard-case audit

## HC-F1 — Clock counter increments
Update yes; no input/history-sensitive learned disposition. **PASS:** update ≠ learning.

## HC-F2 — Random parameter mutation
Persistent change may occur; no grounded learning route by itself. **PASS.**

## HC-F3 — Supervised neural-network training
History/examples + parameter update + future behavior change: formal LearningStanding yes, despite no intrinsic goals or agency. **PASS:** learning ≠ agency.

## HC-F4 — Training run fails to improve
TrainingStanding yes; LearningStanding may still occur if persistent history-dependent organization changed. Adaptive/performance benefit may be absent. **PASS:** training ≠ learning ≠ improvement.

## HC-F5 — Catastrophic interference
New mapping learned while prior mapping collapses. **PASS:** learning ≠ monotonic capability growth.

## HC-F6 — Habituation
Repeated exposure changes future response under diagnostic criteria. **PASS:** learning without reward/goal.

## HC-F7 — Sensory fatigue
Response falls while transducer temporarily fatigues, without retained learned organization. **PASS:** response change ≠ habituation/learning automatically.

## HC-F8 — Thermostat compensates for cold
AdaptiveAdjustmentStanding relative to temperature criterion; no LearningStanding required. **PASS:** adaptation without learning.

## HC-F9 — Maladaptive habit/addiction-like cue learning
Learning yes; adaptation relative to long-term health/reflective goals can be negative. **PASS:** learning without adaptation.

## HC-F10 — Phenotypic plastic response
Environment triggers morphology/phenotype change via inherited reaction norm. Plastic change/adaptation possible; individual learning not required. **PASS.**

## HC-F11 — Child maturation with experience-expectant input
DevelopmentStanding yes; some experience-shaped organization is developmental rather than idiosyncratic learning. **PASS:** development ≠ learning.

## HC-F12 — Adult skill practice
Experience-dependent retained action-performance change. SkillAcquisition + LearningStanding. **PASS.**

## HC-F13 — Pretrained frozen model deployed
LearnedArtifact/TrainingHistoryStanding yes; current deployment episode may have no LearningOccurrence. **PASS:** provenance ≠ current learning.

## HC-F14 — Same model with persistent episodic memory
If memory writes are recruited across future episodes under bearer boundary, online LearningStanding may exist even with frozen weights. **PASS:** parameter update not required.

## HC-F15 — In-context adaptation reset after session
Contextual learning candidate within episode; no cross-session retention. **PASS:** learning scope matters.

## HC-F16 — Manual configuration edit
Behavior changes, but update may be externally imposed configuration rather than learner history-based update. **PASS.**

## HC-F17 — Agent chooses to rewrite own policy
SelfModificationStanding candidate; whether it is learning depends on history/evidence-sensitive update organization. **PASS:** self-modification ≠ learning.

## HC-F18 — Externally fine-tuned model
Learning of persistent model/artifact lineage possible; self-revision autonomy low. **PASS.**

## HC-F19 — Model learns reward/value estimate
Formal ValueFunctionLearning yes; no necessary change in intrinsic/evaluative ValueStanding. **PASS.**

## HC-F20 — System infers user's preference
PreferenceInference learning yes; system's own PreferenceStanding need not change. **PASS.**

## HC-F21 — Evolved fixed reflex
Evolutionary/population adaptation route possible; no individual learning required. **PASS.**

## HC-F22 — Baldwin-style interaction
Individual plasticity/learning alters survival/behavioral landscape and thereby selection; learned parameter itself need not be inherited. **PASS:** learning ≠ evolution.

---

# 45. Provisional LearningProfile v0

```text
LearningProfile = <
  Bearer/System,
  Learning Domain,
  Input/Experience/History Source,
  Update Target,
  Update Rule,
  Update Executor,
  Training Route?,
  Supervision/Reward/Demonstration Route?,
  Persistence Horizon,
  Reset Boundary,
  Generalization?,
  Retention?,
  Transfer?,
  Interference/Forgetting?,
  Adaptation Criterion/Benefit?,
  Online/Offline/Contextual?,
  SelfRevision Autonomy?,
  Developmental Stage/Plasticity Window?,
  Evidence/Provenance,
  Uncertainty,
  Scope
>
```

### F8-112
Bare `B learns` is under-specified without learning domain, history/update route and retention scope.

---

# 46. Provisional AdaptationProfile v0

```text
AdaptationProfile = <
  Bearer/System,
  Environment/Challenge Domain,
  Criterion K,
  Horizon H,
  Baseline/Counterfactual,
  Adjustment Mechanism,
  Learning-Mediated?,
  Regulatory/Plastic/Developmental?,
  Benefit Magnitude?,
  Tradeoffs/Costs?,
  Short-vs-Long Horizon Effects?,
  Reversibility?,
  Evidence/Provenance,
  Scope
>
```

### F8-113
`Adaptive` claims without criterion/horizon are ontologically incomplete.

---

# 47. Provisional PlasticityProfile v0

```text
PlasticityProfile = <
  Bearer/System,
  Plastic Domain,
  Trigger Conditions,
  Range/Magnitude,
  Rate,
  Reversibility,
  Persistence,
  Sensitive/Critical Windows?,
  Path Dependence?,
  Cost,
  Stability/Interference Tradeoff,
  Developmental Stage,
  Evidence/Provenance,
  Scope
>
```

### F8-114
Plasticity is capacity for organization change, not a synonym for intelligence or learning quality.

---

# 48. Provisional DevelopmentProfile v0

```text
DevelopmentProfile = <
  Bearer/Lineage,
  Identity/Continuation Criterion,
  Developmental Horizon/Stage,
  Endogenous Maturation Components,
  Experience-Expectant Components?,
  Experience-Dependent Learning Components?,
  Morphological/Structural Changes,
  Capability Gains/Losses,
  Plasticity-Window Changes,
  Canalization/Lock-In?,
  Environmental Dependencies,
  Path Dependence,
  Evidence/Provenance,
  Scope
>
```

### F8-115
Development should record both capability acquisition and loss, and how future learning possibilities change.

---

# 49. Revised AgencyStanding candidate v0.6

MF8-F yields:

```text
AgencyStanding(B | Σ)
 = Individuated/Persistent Bearer
 + Persistent Agential Source Organization
 + EvaluativeOrientationStanding
 + Choice/Practical-Selection Organization
 + Action Domain/Repertoire
 + Capacity to instantiate AgentialActionStanding tokens
 + AutonomyProfile
 + Decision/Policy/Plan Profiles as applicable
 + Standing Route
 + Scope
```

with optional/richness profiles now including:

```text
Initiative/Proactivity
Intention
WorldModel
SelfModel
Learning
Adaptation
Plasticity
Development
SelfModification / MetaLearning
```

### F8-116
Learning/adaptation/plasticity/development are **not added to the minimal constitutive core**.

### F8-117
They describe how agency organization can change across history and how capable the bearer is of maintaining/expanding/restructuring agency under changing conditions.

---

# 50. Final MF8-F non-collapse stack

```text
Update ≠ Learning
Change ≠ Learning
MemoryAppend ≠ Learning
Training ≠ Learning
Learning ≠ Improvement
Learning ≠ Generalization
Learning ≠ Agency
```

```text
Learning ≠ Adaptation
Adaptation ≠ Learning
Adaptability ≠ AdaptationOccurrence
Plasticity ≠ Learning
Plasticity ≠ Adaptiveness
PlasticityStanding ≠ PlasticChangeOccurrence
```

```text
Development ≠ Learning
Development ≠ Growth
Maturation ≠ Learning
Development ≠ Biological Evolution
Individual Learning ≠ Population Evolution
```

```text
ValueFunctionLearning ≠ ValueStandingChange
PreferenceInference ≠ OwnPreferenceChange
GoalRepresentationLearning ≠ GoalAdoption
GoalAdoption ≠ GoalAutonomy
NormInference ≠ NormInternalization
```

```text
PolicyChange ≠ PolicyLearning
ModelLearning ≠ WorldChange
PredictionImprovement ≠ ModelLearning
```

```text
TrainingHistory ≠ CurrentBearerLearningOccurrence
LearnedArtifactCapability ≠ OnlineLearning
ParameterUpdate ≠ Learning
FrozenWeights ≠ NoContextualLearning
```

```text
Learning ≠ SelfModification
InternalUpdate ≠ SelfModification
SelfRevisionAutonomy ≠ LearningCapability
```

```text
NewLearning ≠ MonotonicAccumulation
Forgetting ≠ Erasure
FastUpdate ≠ GoodLearning
```

---

# 51. FoundationReopen audit

MF8-F attacks FRC-A1 through historical change of agency organization.

No MF7 revision is required:

- `UpdateStanding` is a typed change over MF7 ConfigurationStanding/EvolutionStanding;
- learning requires history-sensitive persistent organization change but does not redefine State or Dynamics;
- adaptation is criterion-relative evaluation of adjustment, layered over dynamics/control;
- plasticity is a capacity/profile for possible organization change;
- development consumes identity/continuation and temporal scope;
- biological population evolution is explicitly separated from MF7's generic EvolutionStanding by route/scope;
- identity-break cases use MF7 bearer continuation rather than weakening it.

MF3 also survives:

- model/value/preference learning separates represented estimate from target value/preference/world;
- learning a representation does not create its referent;
- analyst inference remains distinct from bearer standing.

### F8-118
**FRC-A1 is NOT triggered.**

### F8-119
No MF0–MF7 FoundationReopenCondition is currently demonstrated.

---

# 52. Evidence anchors

Primary/authoritative anchors used in MF8-F:

1. **Eric R. Kandel (2001), `The molecular biology of memory storage: a dialogue between genes and synapses`, Science 294, DOI `10.1126/science.1067020`.** Experience-dependent short/long-term memory storage and synaptic/gene-expression changes; used to separate behavioral learning/memory from implementation/plasticity while grounding persistent experience-driven change.
2. **Citri & Malenka (2008/2011 lineage; Malenka/Bear/Kandel-related synaptic-plasticity literature) and `The cell biology of synaptic plasticity`, Science, DOI `10.1126/science.1209236`.** Synaptic plasticity as experience-dependent connectivity change believed to underlie learning/memory; supports PlasticityStanding ≠ LearningStanding while providing an implementation route.
3. **Richard F. Thompson & William A. Spencer (1966), `Habituation: a model phenomenon for the study of neuronal substrates of behavior`, Psychological Review 73, DOI `10.1037/h0022681`.** Canonical non-associative-learning criteria; used against `response decrement = learning` and against reward/goal requirements for learning.
4. **William T. Greenough, James E. Black & Christopher S. Wallace (1987), `Experience and brain development`, Child Development 58, DOI `10.2307/1130197`.** Experience-expectant versus experience-dependent neural organization; used to separate development/maturation from idiosyncratic learning while preserving interaction.
5. **Michael McCloskey & Neal J. Cohen (1989), `Catastrophic Interference in Connectionist Networks: The Sequential Learning Problem`, Psychology of Learning and Motivation 24, DOI `10.1016/S0079-7421(08)60536-8`.** New learning can catastrophically disrupt prior learning; decisive falsifier against monotonic learning/capability accumulation.
6. **Richard S. Sutton & Andrew G. Barto (2018), `Reinforcement Learning: An Introduction`, 2nd ed., MIT Press.** Formal policy/value/model learning routes; used to separate formal value-function learning from broad evaluative ValueStanding and policy/model learning from goals.
7. **Bruce S. McEwen (1998), `Stress, adaptation, and disease. Allostasis and allostatic load`, Annals of the New York Academy of Sciences.** Regulatory adaptation/allostasis can preserve function through change while creating longer-horizon costs; used for criterion/horizon-relative adaptation.
8. **Peter Sterling (2012), `Allostasis: a model of predictive regulation`, Physiology & Behavior 106, DOI `10.1016/j.physbeh.2011.06.004`.** Regulation as predictive adjustment rather than simple constancy; reinforces adaptation ≠ learning and horizon/criterion dependence.
9. **Mary Jane West-Eberhard (1989), `Phenotypic Plasticity and the Origins of Diversity`, Annual Review of Ecology and Systematics 20, DOI `10.1146/annurev.es.20.110189.001341`; and later developmental-plasticity work.** Phenotypic/developmental plasticity as environmentally responsive phenotype generation affecting evolutionary trajectories; used to separate plasticity, development and population evolution.
10. **James Mark Baldwin (1896), `A New Factor in Evolution`, American Naturalist 30, DOI `10.1086/276408` and continuation `10.1086/276428`.** Historical route for interaction between individual plasticity/learning and selection without identifying learned individual change with inherited population evolution.

The literature does not supply one universally accepted essence of `learning`; MF8-F therefore uses cross-domain non-collapse and falsification rather than forcing neuroscience, psychology, RL, development and evolution into one disciplinary definition.

---

# 53. MF8-F verdict

The deepest reconstruction is:

```text
UPDATE
 = some organization/state changed

LEARNING
 = history/input-sensitive relatively persistent update
   that changes future bearer-relative use/response

ADAPTATION
 = criterion-relative adjustment that preserves/improves fit
   over a declared horizon

PLASTICITY
 = capacity/susceptibility for organization to vary
   under declared conditions/history

DEVELOPMENT
 = organized identity-continuous transformation of the bearer
   across an ontogenetic/developmental horizon
```

Consequently:

> **Learning is not inherently beneficial. A system can learn the wrong thing, overfit, become addicted, forget previous skills, or reduce long-term adaptability while still genuinely learning.**

> **Adaptation requires a criterion and horizon. Fixed regulation can adapt without learning; learning can occur without adaptive benefit.**

> **Plasticity is the possibility structure for change, not the change itself and not intelligence. Development changes both the bearer and often the future plasticity/learning landscape.**

> **For artificial systems, `this model was trained` does not by itself mean the current deployed bearer is learning now. Training history, inherited learned capability, online learning, contextual adaptation and self-modification are different standings.**

> **Learning a value function, reward model, user preference or goal representation does not automatically change what the learner itself values, prefers or autonomously wants.**

And for Agency Foundations:

```text
Agency can exist without learning.
Learning can exist without agency.
```

Learning/adaptation/plasticity/development describe the **historical mutability and maintenance of agency organization**, not the minimal constitution of agency itself.

---

# 54. Next frontier

Proceed directly to:

```text
MF8-G — Responsibility, Accountability, Credit, Blame & Liability
```

Primary questions:

1. What is causal responsibility versus agential responsibility?
2. Responsibility ≠ authorship—what extra normative/role conditions are required?
3. Accountability ≠ responsibility—who must answer, explain, repair or bear consequences?
4. How should delegation distribute responsibility among principal, recommender, decision-maker, authorizer and executor?
5. Does coercion reduce authorship, responsibility, or both—and through which route?
6. How do competence, knowledge, foreseeability, control and authority affect responsibility standing?
7. Can a non-conscious artificial agent possess operational/role responsibility without moral responsibility?
8. How should legal liability, institutional accountability and moral blame remain separate?
9. How do failed attempts, omissions, accidental outcomes and side effects change attribution?
10. What is credit for beneficial outcomes versus blame for harms, and can both diverge from causal contribution?

MF0–MF7 remain frozen unless a named concrete FoundationReopenCondition is demonstrated.
