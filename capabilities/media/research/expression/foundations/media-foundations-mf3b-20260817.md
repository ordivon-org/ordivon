# Ordivon Media Foundations — MF3-B Content, Correctness & Misrepresentation

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 5 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3-A Representation Ontology complete/provisional.  
**Status:** MF3-B complete as a provisional Representation round; Representation Foundations remain unfrozen.  
**Next:** MF3-C — Format, Code & Geometry.

---

# 1. Problem statement

MF3-A left a deliberately hard candidate:

`Representation = Vehicle + Target/Domain + Proxy Recruitment + Content-determining Grounding/Mapping + Correctness/Satisfaction Conditions`

MF3-B attacks the two least understood terms:

1. **Content:** why is a vehicle about `T` rather than some correlated cause, proximal stimulus, useful predictor, designer label or downstream consequence?
2. **Correctness / misrepresentation:** how can a token remain a representation *of T* while being wrong about T?

The round also tests whether one binary `correct/incorrect` relation can cover descriptive representations, goals/commands, probabilistic estimates, structural maps and hybrid signals.

The answer is not a single content theory. The strongest result is a **typed, plural grounding architecture with a shared evaluability requirement**.

---

# 2. A deeper decomposition: target, referent and content are not the same

MF3-A used `Target/Domain` as one slot. That is too coarse.

Consider:

- `There is a wolf nearby` when no wolf is present.
- a hallucinated voice when no speaker is present;
- a map of a fictional country;
- `unicorn`;
- a prediction of tomorrow's temperature;
- a goal state that has not yet been achieved.

A representation can have determinate content even when there is no actual current entity that serves as token referent.

Therefore distinguish:

```text
Domain D
  the space/type of things or possibilities the representation concerns

Content condition Φ
  what the vehicle represents as obtaining within D

Referent / satisfaction instance R
  an actual entity/state/trajectory that may instantiate or satisfy Φ; optional per token

Mode M
  how the content is normatively related to the target/world/action

Frame / Granularity G
  coordinate frame, level, precision, partition, scope or abstraction at which Φ is specified
```

Working content profile:

`Content(V | S,H) = <D, Φ, M, G>`

with actual token reference/satisfaction evaluated separately.

### Result

**RB-01 — Target domain ≠ actual token referent ≠ representational content.**

This is necessary to make false, fictional, predicted, hypothetical and directive representations coherent without pretending that nonexistent objects causally ground each token.

---

# 3. Candidate grounding family A — pure causal/informational semantics

## Candidate

A vehicle `V` represents `T` because instances/states of `T` reliably cause or covary with `V`.

This has major virtues:

- naturalistic;
- easy to measure;
- directly connected to sensing;
- compatible with learning and neural coding;
- can explain why a system's state carries information about distal variables.

But it fails as a complete content theory.

## Falsifier A1 — disjunction / false positives

If flies normally produce detector state `V`, but pellets sometimes also produce `V`, pure covariance tends toward content such as `fly-or-pellet` rather than allowing `pellet` to be a false positive for `fly`.

Fodor's asymmetric-dependence strategy attempts to privilege the correct causal route: erroneous causes produce the token only because the normal target causes can produce it, not vice versa. This is an important refinement, but the relevant asymmetry itself depends on background conditions and does not supply a universally clean target-selection rule.

## Falsifier A2 — proximal/distal ambiguity

A visual state may correlate with:

- retinal irradiance;
- edge orientation;
- surface reflectance;
- object identity;
- action affordance.

Correlation alone does not choose which level is content. MF2 already established that physical, signal, perceptual, semantic/task and action geometries must not be collapsed.

## Falsifier A3 — absent/nonexistent/counterfactual content

A representation can target fictional objects, future states, hypotheses or counterfactual possibilities for which no actual target token currently causes the vehicle.

## Verdict

**Pure causal/informational grounding rejected as universal.**

Retain:

> Causal/correlational relations are often important **grounding evidence** and may be constitutive in some representation types, but information alone cannot determine target, granularity or error conditions.

**RB-02 — Causal/informational dependence is neither universally sufficient nor universally necessary for representational content.**

---

# 4. Candidate grounding family B — teleosemantics / proper function

## Candidate

Content is fixed by what a representation-producing/consuming system has the biological proper function to indicate/use. Millikan's biosemantics shifts attention away from raw frequency to historically grounded proper function and producer–consumer organization; Dretske likewise combines indication with acquired function.

This directly addresses a core MF3 problem:

> A state can have a stable target even when a particular token was caused abnormally.

A frog's detector can continue to be about the functionally relevant prey condition even when an abnormal stimulus triggers it.

### Major success — error without content drift

Proper-function history can distinguish:

```text
content-fixing success condition
        ≠
current token-producing cause
```

This gives genuine misrepresentation room.

### Major success — distal relevance

Functional history can privilege ecologically/task-relevant distal conditions over arbitrary proximal correlates when the system's success historically depended on using the proximal relation to deal with the distal condition.

## Falsifier B1 — universal history requirement

Evolutionary proper function cannot be a universal requirement for representation because representation also occurs in:

- newly engineered devices;
- newly trained artificial systems;
- newly established conventions;
- deliberately constructed maps/models;
- rapidly learned internal proxies.

Historical/evolutionary grounding is therefore one route, not the ontology of all representation.

The Davidson-style `Swampman` thought experiment sharpens the issue: a molecule-for-molecule duplicate without the ordinary causal/social history pressures any theory that makes history absolutely necessary. MF3 does not resolve the Swampman intuition; it uses the case to reject **history as a universal necessary condition** across natural, artificial and conventional representation.

## Falsifier B2 — function indeterminacy / level plurality

A mechanism can participate in many nested functions. `Proper function` by itself does not guarantee a unique content grain unless the relevant task, consumer/use and exploitable relation are specified.

## Verdict

**Teleofunctional grounding survives as a strong typed grounding route, not a universal foundation.**

**RB-03 — Historical/proper function can ground content and stabilize error conditions in biological systems, but evolutionary history is not necessary for every representation.**

---

# 5. Candidate grounding family C — learning / training history

## Candidate

A learned state represents `T` because training shaped it to discriminate/predict/control `T`.

This generalizes historical grounding beyond biological evolution and applies naturally to animals and artificial systems.

## Falsifier C1 — training objective ≠ learned content

An image classifier trained on `cow` labels may solve the task by exploiting grass/background texture. A model can achieve low training/test loss using a shortcut that diverges from the intended human target. Deep learning's shortcut-learning failures make this distinction operationally important.

Therefore:

`designer/trainer intended variable ≠ automatically realized internal content`.

## Falsifier C2 — label correlation underdetermines internal role

Two hidden states can be equally predictive of the target label but play different downstream causal roles; one may encode a nuisance feature that happens to correlate with the label.

## Falsifier C3 — objective functions are not semantic norms by themselves

Gradient loss specifies an optimization relation. It does not automatically tell us which internal state represents what. Loss minimization can create useful control variables, shortcuts, caches and intermediate statistics that are not all representations of the supervised target.

## Verdict

**Learning history survives as grounding evidence but requires use/role and relation analysis.**

**RB-04 — Training objective, label and low loss do not by themselves fix internal representational content.**

**RB-05 — Learned content attribution requires evidence about what learned relation is actually exploited by downstream processing under intervention/counterfactual variation.**

---

# 6. Candidate grounding family D — structural correspondence

## Candidate

Vehicle structure represents target structure because relations among vehicle states correspond to relations in the target domain.

This is powerful for:

- maps;
- spatial models;
- diagrams;
- analogue magnitude systems;
- state-space models;
- latent world models;
- relational graphs;
- scientific simulations.

Shea's framework treats exploitable structural correspondence as a serious content-bearing relation when the system uses that correspondence in performing its task functions.

## Falsifier D1 — mapping abundance

Bare structures admit many possible homomorphisms/isomorphisms. Mathematical correspondence alone does not identify the intended/recruited target domain.

## Falsifier D2 — relevance selection

A London Underground map deliberately preserves connectivity while distorting metric distance. It is not simply `less structurally similar`; it preserves selected relations relevant to use.

Thus representation depends on **which structure is recruited as relevant**, not maximum global similarity.

## Falsifier D3 — nonstructural simple content

A binary alarm or conventional token can represent a condition without needing a rich internal structure homologous to the target domain.

## Verdict

**Structural correspondence is a representational format/grounding route, not a universal content theory.**

**RB-06 — Structural content requires a selected, exploitable correspondence relative to task/use; bare isomorphism or similarity is insufficient.**

---

# 7. Candidate grounding family E — inferential / consumer / use role

## Candidate

A state represents `T` because downstream processing treats it as `T`: inference/action patterns depend on it as a proxy.

This matches MF3-A's strongest surviving `proxy recruitment` idea.

### Major success

Use explains why external decodability is insufficient. A variable that an analyst can decode but the system never exploits is weak evidence for representation.

### Major success

Use handles decoupled cases naturally: memory, simulation and world-model states can influence reasoning/action when the target is absent.

## Falsifier E1 — internal circularity

If content is fixed only by relations among internal states, the system may never become anchored to any external/domain condition. Arbitrary symbol permutations could preserve internal transition structure.

## Falsifier E2 — success does not uniquely determine content

The same behaviour may be produced by many internal strategies. Successful action alone cannot decide whether a state represents object identity, affordance, value, policy state or a lower-level control variable.

## Falsifier E3 — no distinct homuncular consumer is required

Demanding one separate interpreting subsystem creates regress. Recurrent/distributed systems may recruit states through network-level transformations without a clean producer/consumer module boundary.

## Verdict

**Use/recruitment is close to constitutive, but it cannot alone ground external target/content.**

**RB-07 — Proxy recruitment/use is required for strong system-internal representation attribution, but target/content determination needs constraints beyond downstream causal use alone.**

**RB-08 — A consumer is a functional role, not necessarily a physically distinct module or conscious interpreter.**

---

# 8. Reconstruction — content grounding as constraint convergence

No tested grounding family survives as a universal single source.

The strongest reconstruction is therefore **typed constraint convergence**.

A content attribution is strongest when several independent constraint families converge:

```text
1. Relation constraint
   What causal / correlational / structural / conventional / inferential relation exists?

2. Recruitment constraint
   Which distinctions in V are actually exploited by the system/consumer?

3. Norm / task-function constraint
   What success, task, proper function, design purpose or conventional practice selects
   which relation matters?

4. History constraint
   How did learning, selection, design or convention establish/stabilize the relation?

5. Counterfactual/intervention constraint
   Does changing the proposed content variable or vehicle state alter downstream processing
   in the manner predicted by the representational attribution?

6. Contrastive constraint
   Why T rather than correlated T', proximal P, or disjunction T∨Q?

7. Error constraint
   Can content stay fixed across at least some false/noisy/malfunction-adjacent tokens?
```

This is not a vote-counting formula and does not require all seven in every representation type. External conventional symbols may lean heavily on design/convention; evolved perceptual states may lean on function/history + exploitable causal relation; artificial world models may lean on learned structure + intervention + decoupled downstream use.

### Core result

> **Representational content is role-grounded and typed: it is fixed by the particular relation(s) that a system/practice recruits as standing in for a target domain under a norm/task/history/context that selects which distinctions count.**

No universal scalar `content strength` is asserted.

**RB-09 — Content grounding is plural but constrained; pluralism does not mean arbitrary interpretation.**

---

# 9. Multi-level and consumer-relative content

A single physical vehicle can legitimately participate in several representational relations.

Example: an autonomous robot's internal state may simultaneously be used as:

- a pixel-space measurement by one subsystem;
- an estimated obstacle boundary by another;
- an affordance/collision risk by a planner;
- a debugging visualization for a human operator.

These need not compete for one metaphysically unique content if they correspond to different typed recruitment relations.

However, analyst-side interpretations with no system/practice recruitment remain weaker than actual system-relative contents.

Therefore:

**RB-10 — Representational content can be layered and consumer/recruitment-relative without becoming observer-arbitrary.**

This helps dissolve many proximal/distal disputes: proximal and distal content may both exist at different representational stages/uses rather than one always excluding the other.

---

# 10. Correctness cannot be one binary truth relation

MF3-A said representations need correctness/satisfaction conditions. MF3-B finds that this is still too narrow.

Different representation modes/formats support different **evaluation profiles**.

## 10.1 Descriptive representation

Examples: perceptual estimate, map assertion, belief-like state, measurement report.

Direction of fit:

`representation → should match world/target`

Evaluation may be:

- true/false;
- accurate/inaccurate;
- exact/approximate;
- structurally faithful/distorted.

## 10.2 Directive representation

Examples: goal, command, setpoint, desired trajectory.

Direction of fit:

`world/action → should be brought to match representation`

An unfulfilled goal is not simply a false description. The natural norm is:

- satisfied/unsatisfied;
- achieved/not achieved;
- complied with/violated.

Shea and Millikan's descriptive/directive analyses support keeping these modes distinct; Millikan's `pushmi-pullyu` cases show a single signal can simultaneously carry both descriptive and directive roles.

## 10.3 Probabilistic representation

A forecast `P(rain)=0.7` cannot be judged simply false if one particular day is dry. Its adequacy is distributional:

- calibration;
- proper scoring / log loss / Brier-type evaluation;
- likelihood assigned to realized outcomes;
- sharpness subject to calibration.

Therefore token-level binary truth cannot be the universal norm.

## 10.4 Approximate / structural representation

Maps, models and simulations may deliberately preserve selected relations while distorting others. Evaluation is typed by the represented structure and permissible tolerance/distortion.

### Reconstruction

Replace universal `correctness condition` with:

> **Representational evaluability: a representation type supplies content-relative norms under which tokens/trajectories can be assessed as fitting, failing, satisfying, distorting or being calibrated to the target/domain in the mode-appropriate way.**

Correctness and satisfaction are major subtypes.

**RB-11 — Representation requires typed evaluability, not necessarily binary truth.**

---

# 11. Direction of fit is a mode, not content itself

Two states may involve the same condition `door-open` while differing in representational mode:

```text
Descriptive:  <door state, OPEN, descriptive>
Directive:    <door state, OPEN, directive>
```

The first is wrong if the door is closed.

The second remains an unsatisfied directive when the door is closed; its point may be to cause the condition to become true.

A hybrid state can have both roles.

Therefore:

**RB-12 — Content condition and direction-of-fit/mode are distinct.**

**RB-13 — Descriptive error and directive non-satisfaction must not be collapsed into one notion of falsity.**

This will matter later for goals, plans, policies, UI controls, game states and agent intentions, but MF3-B does not yet classify all policies as representations.

---

# 12. Misrepresentation reconstructed

Misrepresentation should not mean simply `bad outcome`.

Minimal descriptive misrepresentation requires:

```text
1. a content-bearing vehicle V;
2. a stable enough grounded content <D, Φ, M, G>;
3. a token/context in which mode-appropriate evaluation fails with respect to D/Φ;
4. the content grounding does not collapse/redefine itself merely because this token is wrong.
```

Thus:

`wrong token ≠ new content`.

### Key distinction

- **Misrepresentation:** representational token exists but its content fails to fit its target/domain in the relevant mode.
- **Malfunction:** representational machinery fails to operate as specified; may or may not produce a misrepresentational token.
- **Misresponse:** representation may be correct but downstream consumer/action responds incorrectly.
- **No representation:** state may be mere noise, corruption or invalid token rather than a contentful false representation.

Millikanian producer/consumer analyses are especially useful for preserving this distinction: representational error and consumer failure are different failure loci.

**RB-14 — Misrepresentation ≠ malfunction ≠ misresponse ≠ noise.**

---

# 13. Error taxonomy

MF3-B needs a richer taxonomy than `true/false`.

### E1 — False positive / hallucinated presence

Vehicle represents `T present` when no matching current target instance exists.

### E2 — False negative / omission

System represents `T absent` when T is present. Mere failure to represent T at all is not automatically a false-negative representation; omission and explicit absence-content must be distinguished.

### E3 — Attribute/state error

Correct target, wrong property/state/value.

### E4 — Identity/reference error

A represented token is assigned to the wrong entity while the represented property may be accurate.

### E5 — Relational/structural error

Nodes/items may be correct but their represented relations are wrong.

### E6 — Metric/quantitative error

Magnitude/position/probability is biased or imprecise relative to the content's allowed tolerance.

### E7 — Calibration error

Distributional representation assigns systematically inappropriate probabilities/confidences even if many individual guesses are right.

### E8 — Frame/granularity error

A representation uses the wrong coordinate frame, abstraction level or partition for the recruited task.

### E9 — Directive non-satisfaction

Goal/command/setpoint condition is not realized. This is not necessarily descriptive misrepresentation.

### E10 — Hybrid divergence

A pushmi-pullyu/hybrid representation can be descriptively accurate but directive response fail, or vice versa.

**RB-15 — Representational failure is typed by content, format and mode; no single scalar error captures all cases.**

---

# 14. Hard falsifier — systematic bias

Suppose a thermometer reads `+5°C` across its range.

If content were whatever value its tokens most reliably indicate, systematic bias might redefine its content so that it is never wrong. But ordinary representational practice and engineered function allow us to say:

> the thermometer still represents temperature but is miscalibrated.

Why can content stay fixed?

Because target/use/design/calibration convention remain anchored to temperature while token mapping drifts.

The same pattern occurs in:

- sensory recalibration errors;
- biased estimators;
- misaligned robot localization;
- systematically shifted neural codes;
- dataset-shifted classifiers.

Therefore:

**RB-16 — Statistical reliability/current token frequency does not by itself determine content; systematic error can coexist with stable content when grounding remains anchored elsewhere.**

---

# 15. Hard falsifier — adversarial and shortcut artificial systems

Artificial neural networks are especially useful because designer intention and realized mechanism can diverge.

## Shortcut learning

A classifier trained for `object category` may actually exploit background texture or watermark-like cues. Good benchmark performance therefore does not prove that an internal state represents the intended object variable.

## Adversarial examples

Small perturbations can cause high-confidence category errors while human-recognized object identity is stable. This exposes a distinction among:

- designer/task target;
- learned decision boundary;
- internal exploited features;
- output label semantics.

### Result

A system can have **assigned/derived content** at its interface (`this output slot means cat`) while its internal states exploit quite different features. Therefore content attribution must preserve **grounding provenance**.

Provisional grounding provenance types:

```text
systemic / endogenous
  grounded in the system's own learned/functional recruitment

derived / designed
  grounded by artifact design and downstream institutional use

conventional / public
  grounded by shared practice

analyst-ascribed
  interpretation useful to an external observer but not yet shown to be systemically recruited
```

These can overlap.

**RB-17 — Designer-assigned content and system-realized internal content are distinct attribution layers.**

**RB-18 — Benchmark success and nominal training labels do not prove that internal variables carry the intended content.**

---

# 16. Fictional, nonexistent and counterfactual targets

Pure causal semantics struggles with `unicorn`, fictional maps and hypothetical simulations.

MF3-B resolves the ontology by refusing to require an actual token referent.

Representation can instead target:

- a constructed model domain;
- a possibility space;
- a conventionally defined fictional entity;
- a counterfactual state;
- a future unobserved state;
- a variable whose current extension is empty.

Correctness/evaluability is then relative to the appropriate domain/model/convention rather than necessarily current physical actuality.

Example:

`Sherlock Holmes lives at 221B Baker Street` can be evaluated relative to the Holmes fiction without requiring a causally interacting Sherlock Holmes.

This does **not** imply that all imagined structures automatically represent. Proxy recruitment + grounded domain/practice remains required.

**RB-19 — Actual causal referent is not necessary for content; representational domains may be actual, possible, predicted, fictional or constructed.**

---

# 17. Hallucination and perceptual false positives

MF2 preserved the distinction between perceptual content and evidence grounding. MF3-B sharpens it representationally.

A hallucination-like state may carry content such as `voice present at location L` even when there is no matching source. Its lack of current external evidence does not force content to disappear.

This is possible because:

- content can be grounded by learned/systemic representational organization;
- a token's causal production route can deviate from the normal/content-fixing route;
- actual referent is optional;
- evaluability can fail while content remains stable.

Therefore:

**RB-20 — Evidence grounding and representational content are independent axes; ungrounded current tokens can still misrepresent rather than become contentless by definition.**

This does not settle whether phenomenological hallucination counts as `perception` in MF9; it only clarifies representational content when such states are representational.

---

# 18. Novel systems and the history challenge

A universal teleosemantic theory risks saying a newly instantiated but functionally organized system lacks content until sufficient history accumulates.

MF3-B rejects that as a universal restriction.

Different systems can acquire grounding through different paths:

- evolution;
- individual learning;
- engineering design;
- copying from an established representational architecture;
- social convention;
- explicit calibration;
- task-coupled interaction.

History matters because it often selects why a relation is recruited, but `history` itself is typed.

A copied artificial model can inherit derived/systemic role through its architecture, weights, training lineage and deployment relation even if that physical token is newly instantiated.

**RB-21 — Grounding history is typed; evolutionary ancestry is one case, not the universal source of content.**

---

# 19. Content determinacy is not always maximal

The content question is often posed as if every representation must have one perfectly sharp proposition.

But real systems support:

- probabilistic content;
- coarse categories;
- partially specified spatial relations;
- ambiguous/multimodal hypotheses;
- context-dependent variables;
- distributed states whose content is only determinate at population level;
- representations deliberately abstracted over nuisance dimensions.

Therefore indeterminacy can arise at two levels:

1. **epistemic attribution uncertainty:** we do not yet know what the system represents;
2. **constitutive content breadth/underspecification:** the representation itself may be coarse/probabilistic/partially specified.

These must not be confused.

**RB-22 — Representational content need not be maximally precise or proposition-like; content granularity and uncertainty are first-class properties.**

---

# 20. Revised representational schema after MF3-B

MF3-A schema:

`Rep(V, T, C | S, G, U, K, H)`

is refined to:

```text
RepEpisode = <
  V : vehicle,
  D : target/domain,
  Φ : represented condition/structure,
  M : representational mode / direction of fit,
  G : frame/granularity,
  U : proxy recruitment/use,
  B : grounding basis/provenance,
  E : evaluation profile,
  H : history/context,
  S : system/practice/consumer-role
>
```

Optional per-token:

`R = actual referent / realized target instance / trajectory`

Grounding basis `B` may include typed combinations of:

- causal/correlational relation;
- structural correspondence;
- biological proper function;
- learned task function;
- design;
- convention;
- inferential/systematic role;
- interventionally verified downstream use.

Evaluation profile `E` may include:

- truth;
- accuracy;
- metric distortion;
- structural fidelity;
- calibration/scoring;
- satisfaction;
- compliance;
- goal achievement.

This remains provisional until MF3-I.

---

# 21. Revised minimal representation candidate

MF3-A's minimal definition is now reconstructed:

> **A representation is a grounded proxy relation in which a system or practice recruits a vehicle's distinctions/structure as standing in for distinctions/structure/conditions in a target domain, under a typed representational mode and an evaluation profile that makes success, fit, satisfaction, distortion or error non-arbitrary relative to that content.**

Important consequences:

- correlation alone is insufficient;
- use alone is insufficient to choose an external target;
- history alone is not universally required;
- truth is not the only norm;
- actual referent is not always required;
- error is possible without content drift;
- one vehicle can carry layered contents for different recruited consumers/practices;
- conventional and systemic content must preserve grounding provenance.

---

# 22. MF3-B provisional axioms

These refine, but do not freeze, MF3-A.

**RB-01** Target domain, actual token referent and content are distinct.

**RB-02** Pure causal/informational dependence is neither universally sufficient nor universally necessary for content.

**RB-03** Historical/proper function can ground stable biological content and error, but evolutionary history is not necessary for every representation.

**RB-04** Training objective, label and low loss do not by themselves determine internal content.

**RB-05** Learned content attribution requires evidence about the relation actually exploited by downstream processing under counterfactual/intervention tests.

**RB-06** Structural correspondence becomes representational only when a selected correspondence is grounded and exploited; bare similarity/isomorphism is insufficient.

**RB-07** Proxy recruitment/use is required for strong systemic representation attribution but cannot alone determine external target/content.

**RB-08** Consumer is a functional role, not necessarily a separate module or conscious interpreter.

**RB-09** Content grounding is plural but constrained; different representation types can use different grounding routes.

**RB-10** Content may be layered and recruitment-relative without becoming arbitrary observer interpretation.

**RB-11** Representation requires typed evaluability, not universal binary truth.

**RB-12** Content condition and representational mode/direction of fit are distinct.

**RB-13** Descriptive error and directive non-satisfaction are different evaluation failures.

**RB-14** Misrepresentation, malfunction, misresponse and noise are distinct failure loci.

**RB-15** Representational failure is typed by content, format and mode.

**RB-16** Systematic bias can coexist with stable content; present statistical reliability does not alone determine content.

**RB-17** Designer-assigned/derived content and system-realized/endogenous content are distinct attribution layers.

**RB-18** Benchmark success and nominal labels do not prove intended internal content.

**RB-19** Actual causal referent is not necessary; domains may be actual, possible, future, fictional or constructed.

**RB-20** Current evidence grounding and representational content are independent axes.

**RB-21** Grounding history is typed: evolutionary, learning, design, copying, convention and calibration histories differ.

**RB-22** Content granularity/uncertainty are first-class; content need not be maximally precise or proposition-like.

**RB-23** Strong content attribution should survive relevant contrastive tests: why T rather than correlated T', proximal P or a disjunctive alternative?

**RB-24** Genuine error requires enough content stability that a failed token is not automatically redefined as carrying a new content.

---

# 23. What MF3-B rejects

Reject as universal foundational claims:

- content is simply whatever normally causes the vehicle;
- content is whatever the vehicle statistically predicts best;
- content is fixed by current token frequency/reliability;
- content always requires evolutionary proper function;
- content is fixed by the training label/objective;
- structural isomorphism alone fixes target/content;
- downstream causal use alone fixes external content;
- every representation must have an actual referent;
- every representation is either literally true or false;
- an unsatisfied goal is simply a false description;
- probabilistic representations are wrong whenever the lower-probability event occurs;
- systematic bias automatically changes content so no error exists;
- all failures of representational systems are misrepresentations;
- malformed/noise tokens, misresponse and misrepresentation are the same;
- designer intent and realized internal representation are identical;
- a representation has exactly one unique content across every consumer/use level;
- ambiguity or coarse content means the state is not representational.

---

# 24. Remaining unresolved after MF3-B

1. Is proxy recruitment strictly necessary for every external/public representation, or can pure conventional status suffice until a token is used?
2. What exact minimum `evaluation profile` is necessary for the weakest representations?
3. Can a purely procedural policy be representational without an explicit state/domain proxy?
4. How should imperative/directive representation be distinguished from causal control signals with no proxy content?
5. What makes some learned task functions genuinely normative rather than merely optimization history?
6. How should multiple simultaneous valid contents be individuated across levels without overgeneration?
7. When is content genuinely indeterminate versus merely unknown to the analyst?
8. How do content and representational geometry relate in distributed/vector systems?
9. What compositional constraints allow content of parts to determine content of wholes?
10. Can conventional public representations and systemic natural representations be unified under one grounding graph without flattening their differences?
11. Do generative latent variables represent causes, sufficient statistics, predictive features or only model-relative coordinates?
12. What distinguishes a model/simulation from an arbitrary representational structure?

Most of these now move naturally to MF3-C–H.

---

# 25. MF3-C handoff — Format, Code & Geometry

MF3-B deliberately did **not** answer how content is physically/computationally organized inside a vehicle.

Next questions:

- localist vs distributed representation;
- sparse vs dense code;
- scalar/category/vector/tensor/graph/trajectory/distribution formats;
- population code;
- coordinate/frame dependence;
- representational similarity geometry;
- disentangled vs entangled factors;
- invariance/equivariance at the representation layer;
- code vs content;
- linear decodability vs nonlinear usability;
- topological/metric structure;
- whether geometry is intrinsic to content or merely one vehicle-level implementation;
- how transforms can preserve content while changing visible geometry;
- whether two representation spaces are equivalent up to invertible mappings, task-preserving mappings, or stronger causal structure.

This is **MF3-C — Format, Code & Geometry**.

---

# 26. Primary/original literature anchors

- Dretske, F. (1986), `Misrepresentation`, in *Belief: Form, Content, and Function*, pp. 17–36. Develops a naturalistic information/function account of how erroneous tokens can remain representational.
- Dretske, F. (1988), *Explaining Behavior: Reasons in a World of Causes*. Acquired functions and representational explanation.
- Fodor, J. A. (1990), *A Theory of Content and Other Essays*, MIT Press. Asymmetric dependence as a solution to disjunction/misrepresentation problems in causal semantics.
- Millikan, R. G. (1989), `Biosemantics`, *The Journal of Philosophy* 86(6), 281–297. Producer/consumer proper-function account; explicit attack on purely causal/informational false-representation solutions.
- Millikan, R. G. (2005), `Pushmi-pullyu Representations`, in *Language: A Biological Model*, pp. 166–186. Descriptive/directive hybrid representations.
- Davidson, D. (1987), `Knowing One's Own Mind`, *Proceedings and Addresses of the APA* 60(3), 441–458. Contains the Swampman history/externalism challenge.
- Cummins, R. (1989), *Meaning and Mental Representation*, MIT Press. Representation as theory-relative explanatory posit and critique of unconstrained naturalization.
- Shea, N. (2018), *Representation in Cognitive Science*, Oxford University Press. Plural/varitel semantics integrating task functions, exploitable correlational information and structural correspondence; explicit descriptive/directive treatment and content-based explanation.
- Geirhos, R. et al. (2020), `Shortcut learning in deep neural networks`, *Nature Machine Intelligence* 2, 665–673. Shows benchmark success can be achieved by decision rules that fail to transfer and diverge from intended task structure.
- Goodfellow, I., Shlens, J. & Szegedy, C. (2015), `Explaining and Harnessing Adversarial Examples`, ICLR / arXiv:1412.6572. High-confidence classification errors under small adversarial perturbations.
- Geiger, A., Lu, H., Icard, T. & Potts, C. (2021), `Causal Abstractions of Neural Networks`, arXiv:2106.02997. Interchange interventions as stronger tests of causal realization than decoding alone.

---

# Final MF3-B synthesis

MF3-A ended with the intuition that representation requires proxy use plus correctness conditions.

MF3-B reconstructs that into a more general form:

> **Representation is not defined by one source of content. Content is a typed, grounded relation selected by how a system or practice recruits vehicle distinctions as proxies for a target domain. The relation may be grounded through causal information, structural correspondence, biological/learned function, design, convention, inferential use or hybrids. A representation is not required to be simply true/false; it must instead be evaluable under a mode-appropriate profile that can distinguish fitting from failing tokens/trajectories without redefining content whenever error occurs.**

The deepest results are:

`Content grounding ≠ current accuracy.`

`Target domain ≠ actual referent.`

`Training objective ≠ realized internal content.`

`Misrepresentation ≠ malfunction ≠ misresponse ≠ noise.`

`Correctness is a typed evaluation relation, not universally binary truth.`

`Descriptive mode ≠ directive mode`, while hybrid pushmi-pullyu representations remain admissible.

**Next: MF3-C — Format, Code & Geometry.**
