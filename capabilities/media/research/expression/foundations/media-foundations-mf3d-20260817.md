# Ordivon Media Foundations — MF3-D Structural Representation & Models

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 7 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3-A/B/C complete and provisional.  
**Status:** MF3-D complete as a provisional Representation round; Representation Foundations remain UNFROZEN.  
**Next:** MF3-E — Symbols, Reference & Compositionality.

---

# 1. Problem statement

MF3-C established:

`Content ≠ Code ≠ Format ≠ Geometry ≠ Coordinates ≠ Readout ≠ Function`.

This creates the central MF3-D question:

> If structural similarity, geometry and isomorphism are not content by themselves, how can maps, diagrams, scientific models, simulations, causal models and learned world models represent their targets *through structure*?

MF3-D attacks several tempting but over-strong claims:

1. structural similarity/isomorphism is sufficient for representation;
2. better models are simply more structurally faithful copies;
3. prediction success demonstrates model correctness;
4. simulation, prediction and model are equivalent notions;
5. a world model must reconstruct the full environment state/observation;
6. learned latent variables automatically represent latent causes;
7. a causal model is required for every useful world model;
8. a model that intentionally distorts its target is thereby a misrepresentation.

The reconstruction is a **keyed, scope-bounded, operation-bearing surrogate model ontology**.

---

# 2. Structural similarity is not structural representation

Suppose structures `M` and `T` are isomorphic or homomorphic.

That mathematical fact alone does not establish:

- which one represents the other;
- what target/domain is intended;
- which mapping is representationally relevant;
- which relations are intended to be preserved;
- which distortions are allowed;
- which inferences may legitimately transfer;
- what counts as representational error.

Suárez's critique of similarity/isomorphism therefore survives MF3-C intact: similarity and isomorphism can be **means** of representation without constituting representation itself.

Pero & Suárez sharpen the point through misrepresentation: homomorphism does not by itself distinguish accurate representation, misrepresentation and nonrepresentation; the actual representational mechanism has to do independent work.

### Result

**RD-01 — Structural correspondence is neither sufficient for structural representation nor self-interpreting.**

A representation relation still requires MF3-A/B grounding, recruitment and evaluability.

---

# 3. Target structure is not simply 'given by Reality'

Structural accounts often speak as if the target arrives already packaged as one mathematical structure.

But the same physical system can be structured as:

- particles and pairwise distances;
- rigid bodies and contacts;
- fields over space;
- a causal graph;
- an energy landscape;
- a state-transition system;
- a topology of reachable states;
- a control system;
- a social network;
- a statistical distribution.

Nguyen & Frigg explicitly identify this problem: structural mappings presuppose a structured target, but the target's relevant structure must be generated/selected by physical descriptions rather than being supplied uniquely by mathematics itself.

### Result

**RD-02 — Target structure is description-/question-relative without becoming arbitrary; the selected target structure must be grounded in target facts and the representational purpose.**

This extends MF3-B's frame/granularity discipline.

---

# 4. Keyed structural representation

The strongest reconstruction is not:

`Model structure ≈ Target structure`.

It is:

```text
Model system M
   │
   ├─ exemplifies / instantiates selected model features R_M
   │
   ├─ user/system operates on M
   │
   └─ key / interpretation κ specifies transfer
                         │
                         ▼
Target domain T structured as R_T
```

Frigg/Nguyen's DEKI-style `key` provides an especially useful precedent: model features can be systematically mapped/imputed to target features through an explicit representational key. Limit keys further show why an idealized model may accurately represent a target even when literal feature identity/similarity fails.

MF3-D generalizes this into an ontology-level relation:

> **A structural representation uses a grounded key/interpretation to select which model relations/operations stand in for which target relations/operations and how model-side inferences are transferred.**

The key need not be linguistic or consciously explicit. In an artificial agent it may be embodied by trained interfaces, decoder/transition roles and action-conditioned downstream use.

**RD-03 — Structural representation is keyed/typed correspondence plus grounded surrogate use, not bare structure matching.**

---

# 5. Model, model system and representation relation are distinct

The word `model` is overloaded.

MF3-D distinguishes:

## Model system `M`

The surrogate structure/entity on which reasoning or computation is performed.

Examples:

- equations plus state variables;
- a scale model;
- graph;
- diagram;
- simulation state;
- latent state-space model;
- causal graph plus structural equations;
- generative neural dynamics.

## Model representation relation `Rep(M,T)`

The relation under which selected features/operations of `M` stand in for `T`.

## Model token/artifact

A particular material or computational realization: paper diagram, file, neural weights, simulator executable, etc.

## Model run / simulation episode

A trajectory/execution generated by operating the model.

### Result

**RD-04 — Model system ≠ model artifact/token ≠ representation relation ≠ simulation/run.**

This separation becomes crucial for AI world models: learned weights define a model system; one imagined rollout is a model execution, not the model itself.

---

# 6. Surrogative reasoning is the key model affordance

Suárez's inferential conception highlights a practical property of scientific representations: users can reason about a target **via** the representation.

MF3-D treats this as the central *model* affordance.

A model supports a pattern:

```text
Target question Q_T
     │ translated/keyed to
     ▼
Model question Q_M
     │ operate / derive / simulate
     ▼
Model result A_M
     │ transfer / interpret
     ▼
Target claim A_T
```

A model therefore need not visually resemble its target. Its strength lies partly in supporting operations that stand in for otherwise expensive, impossible or unavailable target operations.

Examples:

- solve equations instead of perturbing a real bridge;
- trace a route on a map instead of physically exploring every path;
- roll out a latent dynamics model instead of acting in the real environment;
- intervene on a causal model instead of running every physical experiment.

### Result

**RD-05 — Modelhood is strongly associated with structured surrogate operations/inferences, not merely static depiction.**

This does not make inferential use alone sufficient for representation; MF3-B grounding is still required.

---

# 7. Structural preservation is selective

A London Underground map may preserve:

- station identity;
- adjacency;
- line connectivity;
- interchange structure;
- rough ordering;

while deliberately distorting:

- geographic distance;
- angle;
- scale;
- exact position.

The model can be excellent **because** it preserves less.

Likewise scientific idealizations intentionally omit or distort target features to expose particular relationships.

Van Fraassen emphasizes that scientific representation is selective and can require distortion even among selected parameters; Nguyen shows highly idealized toy models can be accurate under an appropriate interpretation rather than being globally similar copies.

### Result

**RD-06 — Structural fidelity is typed by the relations selected for preservation; maximum similarity or maximum structure preservation is not the model objective.**

---

# 8. Omission, abstraction, idealization, approximation and misrepresentation

These terms must not be collapsed.

## Omission

A target distinction/relation is outside the model's represented scope.

Example: subway map omits building heights.

Omission is not automatically error.

## Abstraction

Several target distinctions are intentionally treated as equivalent/irrelevant at the model's chosen granularity.

## Idealization

The model deliberately substitutes a simplified, limiting or otherwise counterfactual structure to expose/use relevant relations.

Examples: frictionless plane; point mass; infinite population.

## Approximation

The model represents a selected quantity/relation only to bounded numerical/structural tolerance.

## Distortion

A represented relation is systematically altered according to a known key/transformation, possibly to improve usability.

## Misrepresentation

Under MF3-B, a content-bearing model claim fails its intended evaluation profile **within the keyed represented scope**, rather than merely omitting or intentionally idealizing something.

### Result

**RD-07 — Omission ≠ abstraction ≠ idealization ≠ approximation ≠ distortion ≠ misrepresentation.**

A model can be literally false in some internal assumptions yet represent its target successfully under the relevant key.

---

# 9. Idealization falsifies 'closer copy = better model'

Many scientifically useful models gain explanatory/inferential value through deliberate non-fidelity.

If we rank models only by global resemblance, increasingly detailed simulation should dominate simpler idealized models. Scientific practice does not support this.

The correct comparison asks:

- Which target relations are relevant?
- What model operations are enabled?
- What inferential error does the simplification create?
- What generality, tractability or explanatory structure is gained?

### Result

**RD-08 — Model adequacy is a multidimensional trade-off, not monotonic closeness to Reality.**

---

# 10. A model represents a possibility structure, not merely one state

A static representation can stand for one state of affairs.

A model often does more: it specifies a **space of admissible or imagined states plus relations among them**.

A dynamical model may encode:

```text
State space S_M
Transition relation / dynamics T_M
Control/action relation A_M
Observation relation O_M (optional)
Constraints C_M
Uncertainty/noise model P_M (optional)
```

The represented content is therefore not just:

`the world is z`.

It may instead be:

> `these states are possible/relevant, these transitions/constraints relate them, and these operations map model trajectories to target possibilities.`

### Result

**RD-09 — Strong models can represent modal/possibility structure: admissible states, transitions and constraints, not only point facts.**

This is a major bridge toward world models.

---

# 11. Prediction ≠ model

A predictor is an input-output device/function that yields estimates of target variables.

A predictor may have little or no reusable internal surrogate structure.

Examples:

- lookup table from recent observations to next label;
- direct regression from image to tomorrow's scalar outcome;
- policy network from observation to action.

Such a system can be predictively successful without supporting:

- state manipulation;
- multi-step rollout;
- alternate-query inference;
- internal surrogate intervention;
- compositional reuse.

Conversely, a model can be valuable while making poor point predictions in some regimes if it supports qualitative, explanatory or counterfactual reasoning.

### Result

**RD-10 — Prediction is an output/use relation; modelhood concerns reusable surrogate structure and operations. Predictive success is neither necessary nor sufficient for the strongest model notion.**

MF3-D does not deny weak statistical models. It introduces a typed distinction between `predictor-like model` and stronger structured modelhood.

---

# 12. Predictive success does not identify the represented structure

Two different models can have the same predictive distribution over observed data while differing in:

- latent-state interpretation;
- causal structure;
- intervention response;
- counterfactual response;
- off-distribution dynamics.

This is the model-level version of MF3-B content underdetermination and MF3-C representation equivalence.

### Result

**RD-11 — Observational/predictive equivalence is weaker than structural, interventional or counterfactual equivalence.**

A model that predicts correctly can still be structurally wrong for questions outside the predictive equivalence class.

---

# 13. Model scope is first-class

A model is rarely globally adequate.

Its representational claim must carry a scope:

`Σ = <domain region, variable set, timescale, intervention class, policy class, precision/tolerance, boundary conditions>`.

Examples:

- Newtonian mechanics at ordinary velocities;
- linearization near an operating point;
- a local weather forecast horizon;
- a world model trained under a family of policies;
- a subway map for network navigation, not geographic walking distance.

### Result

**RD-12 — Model validity/adequacy is scope-indexed; extrapolation beyond declared or evidenced scope is a new claim, not automatic continuation of model validity.**

This applies directly to learned world models under distribution shift.

---

# 14. Model evaluation is a profile, not one fidelity scalar

A structural model can be evaluated along different axes:

```text
State fidelity
  Does it estimate selected current states correctly?

Relational fidelity
  Are selected relations/topology/order preserved?

Dynamical fidelity
  Are transitions/trajectories preserved?

Distributional fidelity
  Are uncertainty and outcome distributions calibrated?

Predictive fidelity
  Are queried future quantities accurate?

Causal/interventional fidelity
  Does the model respond correctly to interventions?

Counterfactual fidelity
  Does it support correct alternate-world reasoning under a specified structural semantics?

Decision/task sufficiency
  Does it preserve what a consumer needs for planning/control?

Explanatory/inferential adequacy
  Does it support the intended surrogate reasoning?

Robustness/scope
  Does adequacy survive relevant perturbation/distribution shift?
```

### Result

**RD-13 — Model fidelity is typed; no universal scalar `world-model quality` is ontologically privileged.**

---

# 15. Simulation ≠ model ≠ prediction

## Model

The reusable surrogate state/structure/rules.

## Simulation

An execution of model operations producing one or more trajectories/states.

## Prediction

A claim/distribution about target outcomes, whether produced by a model, direct predictor, human inference or another method.

A simulator may generate plausible trajectories without those trajectories being accurate target predictions.

A model may support analytic inference without simulation.

A simulation may explore hypothetical states never expected to occur.

### Result

**RD-14 — Model, simulation and prediction are distinct roles. Simulation is model execution; prediction is a target-directed epistemic output.**

---

# 16. Generative model ≠ simulator ≠ world model

A generative model represents/implements a distribution or generative relation over data/states.

It becomes simulator-like when it can be executed iteratively or conditionally to generate state trajectories/events under explicit dynamics/conditions.

It becomes a strong world-model candidate only when its generated/latent structure is grounded and recruited as a surrogate for relevant environment/body dynamics/possibilities.

Therefore a text/image generator is not automatically a `world model` merely because it can generate plausible world-like samples.

### Result

**RD-15 — Generative capacity is neither sufficient for simulation fidelity nor for world-model status.**

---

# 17. Learned latent state need not represent physical latent causes

Suppose a learned dynamical system uses latent state `z_t`:

`z_{t+1} = F(z_t, a_t)`.

Even if `z_t` predicts future observations/rewards extremely well, it may represent:

- physical causes;
- predictive sufficient statistics;
- belief state over hidden causes;
- task-relevant quotient state;
- value-relevant state;
- model-relative coordinates;
- mixtures of these at different recruitment levels.

MF3-B/C block the shortcut:

`latent variable = latent cause`.

### Result

**RD-16 — Learned latent dynamics establishes a model state, not automatically a causally interpreted world variable. Grounding and interventional evidence are required for causal content.**

---

# 18. PlaNet / Dreamer: a world model need not work in observation space

PlaNet learns stochastic/deterministic latent dynamics from pixel observations and plans directly in latent space. Dreamer learns a world model and improves behavior through imagined future scenarios in latent state.

These systems demonstrate:

- representation can compress high-dimensional observations;
- planning can use latent dynamics rather than raw-pixel reconstruction as the primitive planning state;
- model utility depends on task/action-relevant transition structure, not visual isomorphism.

### Result

**RD-17 — World-model state may be an action-relevant latent surrogate rather than an observation-level replica.**

---

# 19. MuZero is the decisive anti-copy falsifier

MuZero learns an iterable model that predicts quantities directly relevant to planning—reward, policy and value—without being trained to reproduce the full environment observation transition.

Yet the learned model supports tree search and strong planning performance across games and Atari.

This falsifies a strong claim:

> `A world model must reconstruct the environment's complete state transition or sensory future.`

### Result

**RD-18 — Full state/observation reconstruction is not necessary for decision-useful world modeling.**

But this introduces a necessary qualifier: such a model may be a **planning-sufficient** world model without being a high-fidelity descriptive model of every environmental variable.

---

# 20. Value equivalence formalizes selective world modeling

The Value Equivalence Principle makes the previous point precise.

Two environment models can be value-equivalent with respect to chosen policy/function sets if they yield the same Bellman updates, even while their transition structures differ in irrelevant respects.

Proper Value Equivalence goes further: multiple models can remain sufficient for optimal planning while ignoring many aspects of the environment.

This provides an unusually clean mathematical falsifier for `better model = more complete copy`.

### Result

**RD-19 — Decision/task equivalence can deliberately quotient away world distinctions that are irrelevant to a specified planning class.**

The size of the equivalence class depends on the consumer's policy/function/query class.

This links MF3-D directly to MF1 lossy sufficiency and MF3-C typed equivalence.

---

# 21. Fidelity vs sufficiency

MF3-D therefore introduces a strict distinction:

## Descriptive/world fidelity

How well does the model preserve selected world structure under its key and scope?

## Query sufficiency

Can the model answer a specified family of questions?

## Decision sufficiency

Can the model support decisions/policies equivalent to those available under a richer environment model?

## Future optionality

How many new queries/tasks can the representation/model support without retraining/reconstruction?

A highly task-specialized model can dominate a general model on decision efficiency while sacrificing future optionality.

### Result

**RD-20 — Model fidelity, query sufficiency, decision sufficiency and future optionality are distinct objectives.**

This mirrors MF1-G compression/task sufficiency at the representation-model level.

---

# 22. Model error compounds under iteration

For iterative dynamical models, small one-step errors can compound under rollout, especially off the training distribution.

Therefore one-step predictive accuracy is not enough to establish useful simulator/world-model behavior.

Relevant diagnostics include:

- multi-step rollout stability;
- closed-loop policy distribution;
- error under imagined trajectories;
- off-policy/off-support states;
- state consistency between encoded observations and model-generated latent transitions.

MuZero analyses, for example, have found limitations in generalization to unseen policies; learned models can be useful partly because planning/search remains biased toward regions where the model is better supported.

### Result

**RD-21 — Iterative model adequacy must be tested on the trajectory/query distribution induced by model use, not only on one-step observational prediction.**

---

# 23. World-model robustness is relevance-selective

A model that wastes capacity reconstructing every exogenous visual nuisance may perform worse for control than a model that isolates task-relevant endogenous dynamics.

Recent latent world-model work explicitly targets robustness to exogenous/irrelevant observation noise by learning task-specific latent dynamics.

This reinforces the ontology conclusion:

> a model need not preserve all observable information to represent the environment well **for a specified use**.

### Result

**RD-22 — World-model compression should be evaluated against represented/query/action scope, not by observation reconstruction alone.**

---

# 24. Causal model is a stronger structural mode, not the universal model form

A predictive/dynamical model can characterize:

`P(Y | X)`

or transition behavior under observed actions.

A structural causal model adds semantics for interventions and, under stronger assumptions, counterfactuals.

The important distinction is not graphical aesthetics but the query class the model licenses.

Pearl's structural framework emphasizes that intervention questions are not mere conditioning questions, and counterfactual evaluation depends on structural assumptions beyond observational associations.

### Result

**RD-23 — Causal/interventional structure is an additional representational commitment that supports stronger query classes; predictive structure alone does not imply it.**

---

# 25. Counterfactual structure is stronger than intervention structure

Consider:

- observational query: `What tends to happen when X=x?`
- intervention query: `What happens if we set X:=x?`
- counterfactual query: `For this actual case, what would Y have been if X had instead been x?`

The last requires a model of alternative possibilities tied through shared structural/exogenous assumptions.

Dynamic latent-state counterfactual work explicitly exposes how much additional structure is required when state and causal mechanisms are partially hidden.

### Result

**RD-24 — Observational, interventional and counterfactual model adequacy are distinct; success at a weaker level does not establish adequacy at a stronger level.**

No claim is made that every useful world model must reach counterfactual competence.

---

# 26. A causal model can also be wrong

Explicit causal arrows do not make a model causally correct.

Causal/world-model structure must still be grounded and tested under:

- interventions;
- mechanism changes;
- policy shift;
- out-of-distribution configurations;
- counterfactual constraints where identifiable/testable.

A learned causal graph that fits observational dynamics can still encode spurious direction or hidden confounding.

### Result

**RD-25 — Causal format/claims are not self-validating; causal content requires causal grounding/evaluation.**

---

# 27. Structural misrepresentation

A structural model can fail in typed ways:

## Relation insertion error

Represents a target relation that does not hold.

## Relation omission within declared scope

Fails to include a relation the key commits the model to representing.

## Wrong relation type

Treats correlation as causation; metric relation as ordinal; adjacency as reachability, etc.

## Wrong dynamics

Represents incorrect transition possibilities/probabilities.

## Wrong intervention semantics

Produces incorrect consequences under intervention.

## Wrong counterfactual coupling

Connects actual and alternate possibilities incorrectly.

## Scope error

Applies a valid local model outside the domain in which its key/assumptions hold.

## Resolution/granularity error

Uses an abstraction too coarse/fine for the declared query.

### Result

**RD-26 — Structural error must be typed by the represented relation/query class; model failure is not one scalar mismatch.**

---

# 28. Model equivalence is query-relative

MF3-C established typed representation equivalence. MF3-D adds model-query equivalence.

Two models may be:

- observationally equivalent;
- predictively equivalent for horizon H;
- trajectory equivalent over a restricted policy class;
- topologically equivalent;
- value-equivalent;
- interventionally equivalent;
- counterfactually equivalent;
- explanatorily/inferentially equivalent for a question family.

### Result

**RD-27 — `Same model` is an equivalence claim indexed to queries, operations, scope and evaluation profile.**

Model identity should not be inferred merely from output equality on one dataset.

---

# 29. A model's structure is partly an interface to operations

The same target information can be represented in formats that support very different operations.

Examples:

- adjacency list vs geometric map;
- differential equation vs sampled trajectory library;
- causal graph vs covariance matrix;
- symbolic rule system vs black-box predictor.

They can share some content while differing in what inferences are cheap, transparent or even available.

### Result

**RD-28 — Model structure is operational: it organizes not only represented states but permissible/easy surrogate transformations and queries.**

This extends MF3-C's `geometry as consumer interface` into full model structure.

---

# 30. Model vs memory/cache

A stored table of past episodes can support nearest-neighbor prediction and planning.

When should it count as a model?

MF3-D does not impose a hard metaphysical boundary, but proposes a useful functional gradient:

```text
record/cache
  preserves past instances

predictor
  maps current input to queried output

structured surrogate/model
  supports reusable relations/operations over states beyond direct replay

dynamical model
  supports iterative transition/trajectory operations

generative simulator
  generates possible state/observation trajectories

causal/interventional model
  supports explicit intervention semantics

counterfactual model
  relates actual and alternate trajectories under shared structural assumptions
```

These are capabilities, not a universal ranking. A simple map can be a strong model for its query family without being dynamical.

**RD-29 — Modelhood is graded/profiled by surrogate operations and scope rather than defined by storage complexity or neural architecture.**

---

# 31. Provisional model schema

MF3-D proposes:

```text
ModelEpisode = <
  M   : model system / surrogate,
  T   : target domain,
  Σ   : scope / boundary conditions,
  R_M : selected model relations/structure,
  R_T : selected target relations/structure,
  κ   : key / interpretation / transfer relation,
  O_M : permitted model operations,
  Q   : supported target query family,
  U   : surrogate recruitment/use,
  B   : grounding basis/provenance,
  E   : evaluation/adequacy profile,
  H   : history/context,
  S   : user/system/consumer practice
>
```

A model run additionally supplies:

`ρ_M = model trajectory / derived state / simulated episode`.

A target prediction/claim additionally supplies:

`A_T = interpreted target assertion/distribution/directive`.

This prevents model, execution and claim from collapsing into one object.

---

# 32. Structural representation candidate after MF3-D

> **A structural model is a grounded representational surrogate whose selected internal relations and operations are keyed to a target domain so that model-side transformations/inferences can stand in for a declared family of target-side questions within a bounded scope and typed adequacy profile.**

Structural representation therefore requires more than shared shape:

`Grounding + Key + Selected Structure + Surrogate Operations + Scope + Evaluation`.

---

# 33. World-model candidate after MF3-D

MF3-D now gives a provisional, implementation-neutral definition:

> **A world model is a stateful surrogate model recruited by an agent/system to represent and operate over temporally extended possibilities of its environment/body under a declared observation/action/query scope, such that model states and transitions can stand in for consequences relevant to prediction, inference, planning or control.**

Important nonrequirements:

- need not reconstruct every observation;
- need not encode every physical variable;
- need not have human-interpretable latents;
- need not be explicitly causal;
- need not be conscious;
- need not be globally faithful.

Important requirements for the strong use of the term:

- grounded relation to environment/body rather than merely plausible sample generation;
- state/possibility structure reusable across more than a single fixed output;
- some temporally extended transition/constraint relation;
- actual system recruitment for prediction/inference/planning/control;
- explicit or inferable query/scope and adequacy criteria.

### Result

**RD-30 — World model ≠ complete world copy; it is a grounded temporally extended surrogate of world/body possibilities for a declared use/scope.**

---

# 34. World-model strength profile

Rather than one binary label, MF3-D proposes typed capabilities:

## W0 — Predictive surrogate

Predicts selected future quantities.

## W1 — Stateful latent surrogate

Maintains model state integrating history/partial observability.

## W2 — Iterative dynamical surrogate

Supports repeated transition under actions/time.

## W3 — Generative/simulation surrogate

Can generate possible trajectories/observations/states.

## W4 — Planning-sufficient surrogate

Preserves variables/operations sufficient for a declared decision class; MuZero/value-equivalent models can qualify even without sensory reconstruction.

## W5 — Interventional/causal surrogate

Supports a declared intervention semantics beyond passive prediction.

## W6 — Counterfactual surrogate

Supports alternate trajectories conditioned on shared case-specific structural assumptions.

These dimensions can overlap rather than forming a mandatory linear ladder.

**RD-31 — `World model` should be accompanied by a capability/query profile rather than treated as one homogeneous natural kind.**

---

# 35. Why counterfactual power is not a universal requirement

A robot navigation model may be excellent if it predicts action-conditioned local transitions and costs, even without identifying autonomous causal mechanisms.

MuZero can be planning-sufficient without reconstructive or explicit causal semantics.

Therefore making counterfactual semantics a necessary world-model condition would exclude useful and empirically successful models.

But counterfactual capability matters when the target use specifically asks:

- mechanism attribution;
- policy transfer;
- scientific explanation;
- diagnosis;
- what-if reasoning under changes not represented by ordinary action transitions.

### Result

**RD-32 — Causal/counterfactual competence is a typed strengthening of world-model structure, not a universal constitutive requirement.**

---

# 36. The world-model illusion: plausible rollouts can be structurally wrong

A generative simulator can produce realistic-looking trajectories while violating:

- object persistence;
- conservation laws;
- causal direction;
- long-horizon dynamics;
- intervention consistency;
- rare-event structure.

Therefore visual realism or likelihood can conceal structural misrepresentation.

This repeats MF1/MF2's deep rule:

`plausible ≠ faithful`.

### Result

**RD-33 — Realistic generation is not evidence of correct world-model structure without relational/dynamical/interventional tests appropriate to the claimed model scope.**

---

# 37. Reconstruction of 'fidelity'

After MF3-D, `model fidelity` means:

> **fidelity with respect to a keyed set of target distinctions/relations, a query family, scope and evaluation metric.**

It is not:

> global resemblance to the world.

This allows a model to be:

- high topology fidelity / low metric fidelity;
- high value fidelity / low sensory fidelity;
- high short-horizon prediction / low counterfactual fidelity;
- high task sufficiency / low future optionality;
- high observational fidelity / low causal fidelity.

**RD-34 — Model fidelity is a vector/profile indexed by the key, query family and scope.**

---

# 38. MF3-D provisional axioms

**RD-01** Structural correspondence is insufficient and non-self-interpreting.

**RD-02** Target structure is selected/structured relative to grounded descriptions/questions, not uniquely given as one mathematical object.

**RD-03** Structural representation requires a grounded key/interpretation plus surrogate use; bare isomorphism/homomorphism is insufficient.

**RD-04** Model system, model artifact/token, representation relation and model run/simulation are distinct.

**RD-05** Strong modelhood involves surrogate reasoning/operations, not merely static depiction.

**RD-06** Structural preservation is selective; maximum structural similarity is not the universal model objective.

**RD-07** Omission, abstraction, idealization, approximation, distortion and misrepresentation are distinct.

**RD-08** Model adequacy is multidimensional and need not increase monotonically with resemblance/detail.

**RD-09** Models can represent possibility/state-transition structure rather than only point facts.

**RD-10** Prediction is an output relation; predictive success alone is insufficient for strong structured modelhood.

**RD-11** Observational/predictive equivalence is weaker than structural/interventional/counterfactual equivalence.

**RD-12** Model validity is scope-indexed.

**RD-13** Model fidelity is typed: state, relational, dynamical, distributional, causal, counterfactual, decision and explanatory adequacy differ.

**RD-14** Model, simulation and prediction are distinct roles.

**RD-15** Generative capacity alone is insufficient for simulator fidelity or world-model status.

**RD-16** Learned latent states are not automatically latent physical causes.

**RD-17** World-model planning state may be a latent surrogate rather than an observation-level replica.

**RD-18** Full state/observation reconstruction is not necessary for decision-useful world modeling.

**RD-19** Decision/value equivalence can quotient away environment distinctions irrelevant to a declared planning class.

**RD-20** Descriptive fidelity, query sufficiency, decision sufficiency and future optionality are separate objectives.

**RD-21** Iterative model adequacy must be evaluated on trajectories/query distributions induced by model use, not only one-step prediction.

**RD-22** Task-relevant world-model compression can legitimately discard exogenous observable detail.

**RD-23** Causal/interventional semantics is an additional representational commitment, not implied by predictive structure.

**RD-24** Observational, interventional and counterfactual adequacy are distinct model capabilities.

**RD-25** Explicit causal format does not establish causal truth; causal content requires grounding/evaluation.

**RD-26** Structural misrepresentation is typed by relation/query/scope.

**RD-27** Model equivalence is indexed to query family, operations, scope and evaluation profile.

**RD-28** Model structure organizes permissible/easy surrogate operations, not only stored state relations.

**RD-29** Modelhood is better treated as a capability/profile than inferred from architecture, file type or complexity.

**RD-30** A world model is a grounded, stateful, temporally extended surrogate of environment/body possibilities for a declared use/scope, not a complete world copy.

**RD-31** World models require capability/query profiles; predictive, stateful, dynamical, generative, planning, causal and counterfactual strengths can differ.

**RD-32** Causal/counterfactual power strengthens some world models but is not universally constitutive.

**RD-33** Plausible/realistic generated trajectories do not establish structural world-model fidelity.

**RD-34** Model fidelity is a keyed, scope- and query-relative profile rather than a global scalar.

---

# 39. Claims rejected by MF3-D

Reject as universal foundational claims:

- structural similarity or isomorphism by itself constitutes representation;
- homomorphism automatically distinguishes representation from misrepresentation;
- Reality supplies one unique mathematical target structure independently of description/question;
- models must resemble/copy their targets globally;
- more detailed or more realistic models are always better;
- idealization is simply representational error;
- omission is automatically misrepresentation;
- every model must predict;
- predictive success proves the model's internal structure is correct;
- one-step predictive accuracy establishes long-horizon model adequacy;
- model = simulation;
- simulation = prediction;
- generative model = world model;
- realistic samples prove world-model fidelity;
- latent variable = latent physical cause;
- world models must reconstruct all observations/environment variables;
- world models must have human-interpretable states;
- world models must be causal/counterfactual models;
- task-sufficient models are therefore globally faithful models;
- full sensory reconstruction is always superior to task-relevant abstraction;
- observational equivalence implies intervention/counterfactual equivalence;
- causal graphs are self-validating because they contain causal arrows;
- there is one universal scalar model-fidelity score;
- models are either globally correct or globally incorrect independently of scope;
- two models producing the same outputs on a dataset are necessarily the same model in the relevant sense.

---

# 40. Remaining unresolved after MF3-D

1. Exactly how `key/interpretation` is realized in purely endogenous learned systems without an external human interpreter.
2. Whether some external public model tokens represent before any actual surrogate use, purely by established convention/design.
3. How symbolic/compositional model structure differs from generic relational/vector model structure.
4. Whether variable identity/reference in models requires symbol-like anchoring beyond structural role.
5. How model parts inherit or compose content into larger model claims.
6. When multiple structurally distinct models should count as rival descriptions versus complementary perspectives.
7. How to distinguish a predictive sufficient statistic from a content-rich latent world state in distributed AI systems.
8. What intervention evidence is enough to assign causal content to learned latent variables.
9. Whether counterfactual capability can be graded without committing to one SCM semantics.
10. How simulation-generated model states acquire token reference/content when they correspond to unrealized possibilities.
11. How fictional/imagined model systems support reference to real targets without collapsing model ontology into target ontology.
12. How external diagrams/maps/images combine conventional symbols with analogue/structural correspondence.
13. What compositional/syntactic organization is necessary for open-ended symbolic representation.

Most of these now point directly into MF3-E through MF3-H.

---

# 41. MF3-E handoff — Symbols, Reference & Compositionality

The structural/model ontology is now strong enough to isolate what structure alone cannot explain.

MF3-E should attack:

- token/type distinction;
- symbol vs signal vs representation;
- reference/denotation;
- index/icon/symbol distinctions without treating Peircean taxonomy as foundational law;
- arbitrary/conventional vs natural grounding;
- syntax vs semantics;
- compositionality;
- productivity/systematicity;
- variable binding;
- names, labels, pointers and identifiers;
- empty/nonexistent reference;
- deictic/indexical reference;
- symbol grounding;
- whether neural/LLM tokens are symbols, vehicles in a symbolic system, or merely conventionally assigned codes;
- whether structured vector representations can realize compositional symbolic roles without one-token/one-concept correspondence;
- how external public symbols differ from endogenous/systemic representations.

This is **MF3-E — Symbols, Reference & Compositionality**.

---

# 42. Primary/original literature anchors

- Suárez, M. (2002/2004), *An Inferential Conception of Scientific Representation* / *The Pragmatics of Scientific Representation*. Scientific representation requires intentional/target-directed use and capacity for surrogate inference; similarity/isomorphism are possible means rather than universal constituents.
- Suárez, M. (2003), *Scientific Representation: Against Similarity and Isomorphism*. Direct critique of reductive similarity/isomorphism accounts.
- Contessa, G. (2007), *Representation, Interpretation, and Surrogative Reasoning*. Interpretation licenses model-to-target surrogate inference.
- Frigg, R. (2006), *Scientific Representation and the Semantic View of Theories*. Argues standard structural/semantic-view accounts do not by themselves solve scientific representation.
- Pero, F. & Suárez, M. (2015), *Varieties of Misrepresentation and Homomorphism*. Homomorphism does not itself distinguish representation/misrepresentation/nonrepresentation.
- Nguyen, J. & Frigg, R. (2017), *Mathematics is not the only language in the book of nature*. Target structure requires structure-generating physical descriptions; mapping accounts presuppose rather than automatically discover target structure.
- Nguyen, J. & Frigg, R. (2020), *Unlocking Limits*. DEKI account and representational keys; limit keys demonstrate systematic model-to-target transfer under idealization.
- van Fraassen, B. (2002), *Science as Representation: Flouting the Criteria*. Representation is selective, purpose-relative and can require distortion.
- Nguyen, J. (2019), *It's Not a Game: Accurate Representation with Toy Models*. Highly idealized models can accurately represent under suitable interpretation; idealization need not equal misrepresentation.
- Hafner, D. et al. (2018), *Learning Latent Dynamics for Planning from Pixels* (PlaNet). Learns action-conditioned latent dynamics from images and plans in latent space.
- Hafner, D. et al. (2023), *Mastering Diverse Domains through World Models* (DreamerV3). Learns environment model and improves behavior via imagined future scenarios.
- Schrittwieser, J. et al. (2019/2020), *Mastering Atari, Go, Chess and Shogi by Planning with a Learned Model* (MuZero). Learns iterable reward/value/policy-relevant model without reconstructing full environment dynamics.
- Grimm, C., Barreto, A., Singh, S. & Silver, D. (2020), *The Value Equivalence Principle for Model-Based Reinforcement Learning*. Multiple models can be equivalent for value-based planning despite differing from full transition models.
- Grimm, C. et al. (2021), *Proper Value Equivalence*. Multiple environment models may remain fully planning-sufficient while ignoring environment aspects irrelevant to optimal planning.
- Sun, R. et al. (2024), *Learning Latent Dynamic Robust Representations for World Models*. Task-relevant latent dynamics can improve robustness under exogenous visual distractors.
- Balke, A. & Pearl, J. (1995/2013), *Counterfactuals and Policy Analysis in Structural Models*. Structural models support policy/counterfactual evaluation beyond ordinary observational prediction.
- Pearl, J., structural causal model work (1995–2009). Distinguishes association/conditioning from intervention and counterfactual queries through explicit causal structure.

---

# Final MF3-D synthesis

MF3-D rejects the picture of a model as a more-or-less faithful miniature copy of Reality.

The stronger ontology is:

> **A model is a structured surrogate. It becomes a structural representation when a grounded key selects which model relations/operations stand in for which target relations/operations, allowing surrogate reasoning within a bounded scope and typed adequacy profile.**

The deep non-collapses are:

`Structural similarity ≠ Structural representation.`

`Model system ≠ Representation relation ≠ Simulation ≠ Prediction.`

`Idealization/distortion ≠ Misrepresentation.`

`Predictive equivalence ≠ Causal/interventional equivalence ≠ Counterfactual equivalence.`

`World-model fidelity ≠ Decision sufficiency ≠ Future optionality.`

And the provisional world-model result is:

> **A world model is not a world copy. It is a grounded, stateful, temporally extended surrogate over environment/body possibilities, recruited for a declared prediction/inference/planning/control scope.**

MuZero/value-equivalent models are decisive falsifiers of reconstructive maximalism: a model can discard large amounts of world detail yet preserve exactly what its consumer needs. Conversely, realistic generative rollouts can be structurally wrong.

The next foundational problem is the one structure cannot settle by itself: how symbols/tokens refer, compose and support open-ended representation.

**Next: MF3-E — Symbols, Reference & Compositionality.**
