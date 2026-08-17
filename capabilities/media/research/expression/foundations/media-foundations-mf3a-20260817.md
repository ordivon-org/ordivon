# Ordivon Media Foundations — MF3-A Representation Ontology

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 4 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen.  
**Status:** MF3-A complete as a provisional ontology round; Representation Foundations are NOT frozen.  
**Next:** MF3-B — Content, Correctness & Misrepresentation.

---

# 1. Why Representation requires a new foundation

MF0 already introduced a provisional boundary:

> Representation is a functionally recruited state serving as a proxy for another state/domain under correctness conditions.

MF1 then showed why Signal cannot be equated with Representation: a signal is structured variation recruited for discrimination, and signal transformations can be studied without semantic or proxy commitments.

MF2 showed why Perception cannot be equated with Representation: perception is the stateful, selective and potentially action-coupled organization/use of sensorimotor evidence that changes structured discriminability among world/body-relative possibilities. Some perceptual mechanisms may be usefully explained representationally, while direct sensorimotor control and other mechanisms must remain admissible until representation itself is defined.

MF3 therefore asks a different question:

> **When does one state/entity/structure count as standing for another state/domain, rather than merely covarying with it, being caused by it, discriminating it, or participating causally in behaviour?**

This round deliberately refuses the common shortcut `internal state / neural code / embedding / feature = representation`.

---

# 2. First-principles decomposition

A candidate representational episode minimally needs distinct roles that are often collapsed:

```text
Vehicle V
  └─ the physical/computational/biological state that does the representing

Target / Domain T
  └─ what V is about / stands in for / is used to track, model, describe or direct

Content C
  └─ what V represents T as being / what distinction or structured claim V makes available

System / Consumer S
  └─ the process, agent or interpreter for which V is recruited in a representational role

Mapping / Grounding G
  └─ what establishes the V↔T relation and determines relevant correspondences/content

Use / Recruitment U
  └─ how downstream processing/action treats V as a proxy rather than merely as another cause

Correctness conditions K
  └─ conditions under which the representation is accurate, inaccurate, satisfied, violated,
     true/false, fulfilled/unfulfilled, well/poorly matched, etc., depending on representation type

Context H
  └─ task, convention, history, mechanism, environment and temporal conditions
```

Candidate relational schema:

`Rep(V, T, C | S, G, U, K, H)`

This is not yet a final equation. It is a typing discipline intended to prevent `representation` from becoming a one-place property of an activation vector or artifact.

---

# 3. Attack 1 — Covariance / information is insufficient

Suppose state `V` covaries strongly with world variable `T`.

This is not enough.

Counterexamples include:

- shadows covarying with illumination/object geometry;
- tree rings covarying with age/environmental conditions;
- receptor activity covarying with stimulus intensity;
- hidden-layer units from which an external analyst can decode many variables;
- arbitrary variables in a deterministic system that correlate with later states.

Covariance establishes an informational/statistical relation. It does not by itself establish that the system **uses V as standing in for T**.

This preserves MF1:

> Signal/information relation can exist without representation.

Therefore:

**RA-01 — Information/covariance is neither sufficient nor by itself diagnostic of representation.**

It may be necessary for some natural representations but cannot be the ontology criterion.

---

# 4. Attack 2 — External decodability is insufficient

Modern neuroscience and ML often infer that variable `T` is represented in activation `V` because a decoder/probe can recover `T` from `V`.

This establishes:

`I(V;T) > 0` or some recoverability relation under the analyst's decoder.

It does NOT by itself establish:

- that the biological/artificial system itself can access that information;
- that it uses that information;
- that V's causal role depends on representing T;
- that T is the content rather than one of many correlated variables;
- that the proposed mapping survives intervention.

A sufficiently expressive external observer can often extract distinctions that are epiphenomenal to the system's own computation.

Geiger et al.'s causal-abstraction program supplies an important stronger test for artificial networks: align neural states with interpretable variables and use interventions/interchange interventions to test whether the internal state has the causal role predicted by the higher-level variable. This still does not solve all semantic/content questions, but it is stronger evidence than probe decodability alone.

Therefore:

**RA-02 — Decodable-from ≠ represented-by.**

**RA-03 — Causal/use evidence is stronger than observer-side recoverability for attributing representation.**

---

# 5. Attack 3 — Causal efficacy / action guidance is insufficient

The reverse shortcut also fails:

> If state V causally guides successful behaviour with respect to T, then V represents T.

A thermostat's bimetal strip, a centrifugal governor, a reactive obstacle-avoidance controller or a direct sensorimotor loop can causally guide behaviour without requiring that every intermediate state be treated as a proxy for a distal state.

If every causally useful control variable counts as representation, then representation becomes nearly coextensive with functional causation.

Ramsey's `job description challenge` is important here: invoking representation should explain something that a non-semantic causal/mechanistic description does not already explain equally well. Detector/receptor status alone does not meet that challenge.

Clark & Toribio's anti-representational challenge reinforces the boundary: some intelligent adaptive behaviour can at least plausibly be modelled in direct agent–environment dynamical terms, so cognitive success cannot be used as a proof that internal representation must be present everywhere.

Therefore:

**RA-04 — Functional causation/action guidance is not sufficient for representation.**

**RA-05 — A representational posit must perform explanatory work qua representation.**

---

# 6. Attack 4 — Similarity / structural correspondence is insufficient alone

Maps, images, diagrams, models and many neural/ML states invite a structural account:

`V` represents `T` because relations in V correspond to relations in T.

Structural correspondence is powerful but underdetermined:

- almost any sufficiently rich structure can be mapped homomorphically/isomorphically onto many target structures under some mapping;
- similarity is respect-relative: two things are always similar in some respects and dissimilar in others;
- the relevant mapping must be selected by use, convention, causal history, design, task or another grounding relation;
- structural correspondence cannot by itself determine which domain is represented.

Therefore:

**RA-06 — Structural correspondence can constitute representational format/content only relative to a grounded mapping and use context.**

This does not reduce structural representation to convention; biological systems can ground mappings through learning/function/history. It says only that bare mathematical similarity is insufficient.

---

# 7. Attack 5 — Internality is neither necessary nor sufficient

External representations are obvious counterexamples to `representation = internal cognitive state`:

- maps;
- diagrams;
- text;
- photographs;
- equations;
- measurement displays;
- files/data structures used as stand-ins by software.

Conversely, many internal states are merely causal/mechanistic states and need not be representations.

Therefore:

**RA-07 — Representation is a role/relation, not an intrinsic natural object class and not an internality property.**

This directly inherits MF0 relationality.

---

# 8. Attack 6 — Conscious interpretation / human meaning is not required

A navigation system can use a map state, a controller can use an estimated state, and a trained animal can act on an indicator without consciously interpreting a symbol.

Thus conscious awareness and linguistic semantics cannot be constitutive of representation.

At the same time, conventional symbols demonstrate that some representational relations are institutionally/socially grounded rather than purely causal/biological.

Therefore:

**RA-08 — Representation can be subpersonal, artificial or external and need not be consciously interpreted.**

**RA-09 — Representational grounding can be natural/learned/functional, designed, conventional or hybrid; these must remain typed rather than collapsed.**

---

# 9. Why misrepresentation is central

A pure covariance account has a deep problem: if V simply means whatever it covaries with, then systematic error tends to redefine the content rather than produce genuine misrepresentation.

But representation appears to be normatively asymmetric:

- a map can place a road where no road exists;
- a thermometer can give an inaccurate reading;
- an internal estimate can locate an object incorrectly;
- a classifier can classify a dog as a cat;
- a goal state can fail to be satisfied.

The representation can remain a representation **of T** while being wrong about T.

This strongly suggests that representation requires some distinction between:

`what fixes the content/target`

and

`whether the current token matches/satisfies that content correctly`.

Shea's representational framework explicitly treats correct representation as explanatory of successful behaviour and misrepresentation as explanatory of systematic failure, with downstream error patterns constrained by where the mistaken content enters processing.

Therefore:

**RA-10 — Genuine representation supports correctness/satisfaction conditions that can remain fixed across at least some cases of error.**

But this round does NOT yet freeze one naturalistic theory of how those correctness conditions are grounded. Teleosemantic, learning/history, structural, causal, inferential and hybrid accounts remain candidates for MF3-B.

---

# 10. Proxy / stand-in relation

The strongest surviving candidate distinction is **proxy use**.

A state is representational when the system treats properties/structure of the vehicle as a basis for dealing with a distinct target/domain — effectively allowing the vehicle to stand in for that target in some process.

This need not mean the target is absent. A live camera image may represent a currently present scene. But representation becomes especially clear under **decoupling**:

- a map guides action when the mapped place is not perceptually available;
- memory supports reasoning about past events;
- a model predicts future/unobserved states;
- a world model can simulate hypothetical trajectories;
- a token can denote a remote or nonexistent entity.

Decoupling is therefore strong evidence for representation, but it is not made a universal necessity because online indicators and perceptual estimates may still genuinely represent presently available states.

Therefore:

**RA-11 — Proxy/stand-in use is a core candidate property of representation.**

**RA-12 — Decoupled use is strong but non-necessary evidence of representational status.**

---

# 11. Representation is not one binary natural kind

Clark & Toribio argue that the representational/non-representational dichotomy may conceal degrees and types of representationality. MF3-A agrees with the typed part but avoids prematurely defining a one-dimensional scalar `degree of representation`.

Representation profiles can differ along orthogonal axes:

### Grounding

- causal/informational;
- learned;
- biological function/history;
- designed;
- conventional/social;
- inferential/systematic;
- hybrid.

### Target relation

- current observable;
- distal hidden state;
- past state;
- future/predicted state;
- counterfactual/hypothetical state;
- fictional/nonexistent entity;
- goal/desired state;
- rule/norm/constraint.

### Direction of fit

- descriptive: representation is assessed against world/state;
- directive: world/action is assessed against representation/goal;
- mixed/hybrid.

### Format

- scalar/category;
- vector/distributed;
- spatial/map-like;
- temporal/trajectory;
- graph/relational;
- symbolic/compositional;
- probabilistic/distributional;
- generative/model-based;
- procedural/policy-like candidates.

### Explicitness/access

- directly addressable variable/token;
- distributed but causally usable;
- only externally decodable (insufficient alone);
- conventional public symbol;
- implicit structural constraint candidate.

These axes must not be collapsed into one hierarchy.

---

# 12. Vehicle, content, format and geometry must be separated

A recurring source of confusion is calling a vector `the representation` without distinguishing:

- **vehicle:** the vector/activation/tensor itself;
- **format:** how distinctions are organized in the vehicle;
- **geometry:** distances/directions/topology among vehicle states;
- **content:** what states of the vehicle represent about the target;
- **code/mapping:** relation connecting vehicle states to content distinctions;
- **consumer/use:** what downstream operation exploits the vehicle;
- **target/domain:** what the representation concerns.

Two systems may use identical numerical vectors with different content because grounding/use differs. Conversely, different vehicles/formats can carry functionally equivalent content.

Therefore:

**RA-13 — Vehicle ≠ content ≠ format ≠ geometry ≠ target ≠ meaning.**

This extends MF1's transform/geometry discipline into representation.

---

# 13. Representation vs Signal vs Perception vs Meaning

## Signal

Signal asks:

> What structured variation is available/recruited to discriminate states through mediation?

It requires no stand-in relation or correctness semantics.

## Perception

Perception asks:

> How does a sensing/acting system organize and use sensorimotor evidence to alter structured discriminability over world/body possibilities?

Some perceptual states may serve as representations; some perceptual mechanisms may be sufficiently explained without representational posits.

## Representation

Representation asks:

> When does a vehicle become recruited as a proxy/stand-in for a distinct target/domain under a content-determining relation and correctness/satisfaction conditions?

## Meaning

Meaning is not equated with representation. A representational state can have content in a minimal correctness-guiding sense without possessing linguistic, conceptual, social or phenomenological meaning. Conventional semantics, interpretation, reference, pragmatics and social meaning belong to later MF3/MF10 layers.

Therefore the foundational non-collapse is:

`Signal ≠ Perception ≠ Representation ≠ Meaning`.

Relations among them are many-to-many, not a fixed serial pipeline.

---

# 14. Artificial neural networks / embeddings as falsifiers

The term `representation` in ML is often used operationally for hidden activations or learned feature spaces.

MF3-A imposes stricter questions:

1. **Information:** Is target variable T recoverable from V?
2. **Usability:** Is it in a format accessible to relevant downstream mechanisms?
3. **Use:** Does the network actually causally depend on V-as-T for the behavior?
4. **Grounding:** Why is T rather than a correlated variable the represented content?
5. **Correctness:** What determines when V misrepresents T rather than simply instantiating another activation?
6. **Intervention:** Do targeted interventions on V induce the changes predicted by the hypothesized represented variable?
7. **Counterfactual role:** Does the representational attribution generalize beyond the training correlation under changed conditions?

Geiger et al.'s causal abstraction/interchange intervention methodology directly strengthens items 3 and 6: representational interpretation gains evidence when internal neural variables causally realize the roles of variables in an interpretable higher-level model.

But even causal realization is not automatically semantic grounding. MF3-B must determine what turns a causally useful abstraction into content-bearing representation.

---

# 15. World models as a high-value edge case

A learned world model is more plausibly representational than a generic feature vector because it may:

- model latent state not currently observed;
- predict future observations;
- support counterfactual rollouts;
- guide action using internal simulated trajectories;
- continue operating when the target state is absent from current sensory input.

Ha & Schmidhuber's `World Models` provides a clean artificial case: a compressed learned model supports a controller, and the controller can even be trained inside internally generated rollouts before transfer back to the external environment.

This supplies strong **proxy + decoupling + downstream-use** evidence.

However, the learned latent dimensions do not thereby acquire simple human-readable symbolic content. Representational status and interpretability are separate.

Therefore:

**RA-14 — Representational status ≠ human interpretability.**

**RA-15 — Generative/predictive decoupled models are strong representation candidates, but their exact content still requires grounding analysis.**

---

# 16. Provisional minimal representation criterion

The strongest candidate after MF3-A is:

> **A representation is a relationally grounded vehicle that a system recruits as a proxy for a distinct target/domain, such that differences or structure in the vehicle are used as standing-in-for differences or structure in the target under content-determining mapping/use conditions that support correctness, incorrectness or satisfaction assessment.**

Compact schema:

```text
Representation
 = Vehicle
 + Target/Domain
 + Proxy Recruitment
 + Content-determining Grounding/Mapping
 + Correctness/Satisfaction Conditions
```

with `System/Consumer + Context + History` generally required to determine those relations.

This definition is **provisional** because MF3-B must attack the hardest terms:

- What exactly is a proxy?
- Are correctness conditions necessary for every representation type?
- Can directive representations (goals, motor commands) be wrong, or only satisfied/unsatisfied?
- How are content and target fixed without circular semantic notions?
- Can structural correspondence + use suffice?
- Is biological function/history necessary in natural systems?
- Can conventional representation be unified with natural representation?

---

# 17. MF3-A provisional axioms

These are working constraints, not frozen Representation Foundations v1.

**RA-01** Information/covariance is insufficient for representation.

**RA-02** External decodability is insufficient for representation.

**RA-03** Causal/use evidence is stronger than observer-side recoverability.

**RA-04** Causal efficacy or action guidance alone is insufficient.

**RA-05** A representational posit must perform explanatory work qua representation.

**RA-06** Structural correspondence requires a grounded relevant mapping/use context.

**RA-07** Representation is a relational role, not intrinsic internality or a natural object class.

**RA-08** Conscious interpretation is not constitutive of representation.

**RA-09** Grounding types are plural and must be typed: natural/learned/functional/designed/conventional/hybrid.

**RA-10** Genuine representation supports correctness/satisfaction conditions robust enough to distinguish at least some misrepresentation from mere content change.

**RA-11** Proxy/stand-in recruitment is a core candidate property.

**RA-12** Decoupled use is strong but non-necessary evidence for representation.

**RA-13** Vehicle, content, format, geometry, mapping/code, target and meaning are distinct.

**RA-14** Representational status does not imply conscious or human interpretability.

**RA-15** Generative/predictive world models are strong representation candidates, but content still requires grounding.

**RA-16** Representation attribution is stronger when interventions show that the proposed representational variable has the predicted causal role in downstream processing.

**RA-17** Signal, perception, representation and meaning are distinct layers/relations; none should be defined merely as the next serial stage of the previous one.

**RA-18** Not all perception is assumed representational; nonrepresentational sensorimotor mechanisms remain admissible.

---

# 18. Rejected claims after MF3-A

Reject as foundational claims:

- every information-bearing/correlated state is a representation;
- every decodable neural/ML feature is represented content;
- every causally useful detector/control state is a representation;
- every internal state is representational;
- representations must be internal;
- representation requires conscious interpretation;
- structural similarity alone determines representational content;
- embeddings are representations simply because ML convention calls them representations;
- representational content equals vector geometry;
- representation equals linguistic meaning;
- perception necessarily consists of internal representation processing;
- representation must be symbolic, discrete or language-like;
- representation must be pictorial/isomorphic;
- human interpretability is required for representation;
- successful behaviour proves representational processing.

---

# 19. Unresolved questions deliberately handed to MF3-B+

1. What naturalistically grounds representational correctness/misrepresentation?
2. Is correctness/satisfaction necessary for all representation types?
3. How should descriptive vs directive representations be unified?
4. Can goals, desires, motor commands and policies be representations, and what are their direction-of-fit conditions?
5. Can a state represent fictional/nonexistent/counterfactual targets without prior causal covariance?
6. How should conventional public symbols and natural/subpersonal representations be unified without trivializing either?
7. Does proxy use require a consumer distinct from the vehicle-producing subsystem?
8. How much decoupling is sufficient/necessary for strong representational status?
9. When does structural correspondence become content-bearing rather than merely mathematical similarity?
10. Can distributed neural/ML representations have determinate content when no single unit maps cleanly to a target variable?
11. What is the relation between content and representational geometry?
12. Can procedural policies themselves represent, or do they merely implement dispositions/actions?
13. Where is the boundary between representation and memory?
14. Where is the boundary between representation and model/simulation?
15. Does explicit error correction imply an internal norm of correctness or only engineering loss minimization?

---

# 20. MF3 research program reconstructed

MF3 should not be one monolithic chapter. The ontology now naturally decomposes into:

### MF3-A — Representation Ontology ✅

Representation ≠ Signal ≠ Perception ≠ Meaning; vehicle/target/content/proxy/correctness decomposition.

### MF3-B — Content, Correctness & Misrepresentation

How content is fixed; error; direction of fit; descriptive vs directive representation; teleosemantic/causal/learning/structural/inferential/hybrid accounts.

### MF3-C — Format, Code & Geometry

Distributed vs local, vector, topological, spatial, temporal, probabilistic, symbolic, compositional and generative formats; format ≠ content.

### MF3-D — Structural Representation & Models

Maps, diagrams, images, simulations, scientific models, world models; correspondence, homomorphism, interpretation and counterfactual structure.

### MF3-E — Symbols, Reference & Compositionality

Tokens/types, symbol grounding, reference, syntax, compositionality, productivity/systematicity; representation ≠ language.

### MF3-F — Neural & Biological Representation

What neural coding evidence licenses representational claims; decodability vs use; mixed selectivity; population codes; embodied/direct alternatives.

### MF3-G — Artificial Representation

Embeddings, hidden states, latent variables, transformers, multimodal representations, world models, causal abstraction, probes/interventions, interpretability.

### MF3-H — External / Public Representation

Writing, images, notation, diagrams, measurement displays, files/data structures; conventional/designed grounding.

### MF3-I — Representation Falsification & Reconstruction

Cross-domain attack → final Representation Ontology Graph → freeze Representation Foundations v1 → enter MF4 Composition.

This mirrors the falsification-first architecture that stabilized MF1 and MF2.

---

# 21. Primary / original literature anchors for MF3-A

- Clark, A. & Toribio, J. (1994), `Doing Without Representing?`, Synthese 101(3), 401–431. DOI: 10.1007/BF01063896.
- deCharms, R. C. & Zador, A. (2000), `Neural Representation and the Cortical Code`, Annual Review of Neuroscience 23, 613–647. DOI: 10.1146/annurev.neuro.23.1.613.
- Ramsey, W. M. (2007), `Representation Reconsidered`, Cambridge University Press; especially the job-description challenge and critique of receptor/detector notions.
- Dretske, F. (2006), `Representation, Teleosemantics, and the Problem of Self-Knowledge`, in Teleosemantics: New Philosophical Essays, Oxford University Press.
- Shea, N. (2018), `Representation in Cognitive Science`, Oxford University Press; content, function, correlational information, structural correspondence, misrepresentation and descriptive/directive representation.
- Geiger, A., Lu, H., Icard, T. & Potts, C. (2021), `Causal Abstractions of Neural Networks`, arXiv:2106.02997; causal alignment and interchange interventions for neural representation analysis.
- Ha, D. & Schmidhuber, J. (2018), `World Models`, arXiv:1803.10122; learned compressed generative world state used by downstream controllers, including decoupled imagined rollouts.

---

# Final MF3-A handoff

The main gain is a stricter ontology than common cognitive-science/ML usage:

> **Information is cheap; representation is not.**

A representation is not established merely by correlation, decodability, internal location, neural activation, causal efficacy, similarity, prediction accuracy or successful behaviour.

The strongest surviving candidate is a **relationally grounded proxy role under correctness/satisfaction conditions**. The next round must attack exactly the hardest part of that candidate: content and normativity.

**Next:** MF3-B — **Content, Correctness & Misrepresentation**.
