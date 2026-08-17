# Ordivon Media Foundations — MF3-F Neural & Biological Representation

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 9 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3-A/B/C/D/E complete and provisional.  
**Status:** MF3-F complete as a provisional Representation round; Representation Foundations remain UNFROZEN.  
**Next:** MF3-G — Artificial Representation.

---

# 1. Problem statement

Neuroscience routinely says:

- `this neuron represents orientation`;
- `place cells represent location`;
- `motor cortex encodes movement direction`;
- `prefrontal cortex represents task rule`;
- `population activity represents uncertainty`.

These phrases can hide several very different empirical claims.

MF3-F asks:

> **What evidence actually licenses a neural representation attribution, and when is representational language merely a convenient gloss over correlation, control, dynamics, memory or causal mediation?**

The central chain under attack is:

`Tuning → Encoding → Decodability → Causal Use → Grounded Neural Content`.

The result is a strict non-collapse:

`Tuning ≠ Information ≠ Decodability ≠ Downstream Accessibility ≠ Causal Recruitment ≠ Grounded Neural Content`.

Neural representation attribution becomes a **convergent evidence profile**, not a one-statistic label.

---

# 2. First distinction — phenomenon, analysis and semantic claim

A typical neural experiment contains at least three levels.

## 2.1 Phenomenon

A neural variable `N` changes systematically with experimental/world variable `X`.

Examples:

- firing rate varies with orientation;
- place-cell activity varies with position;
- population state varies with task phase;
- neural trajectory varies with movement condition.

## 2.2 Analysis/model

An experimenter fits:

- tuning curve;
- GLM/encoding model;
- decoder;
- representational geometry;
- latent manifold;
- dynamical system;
- causal perturbation model.

## 2.3 Semantic/representational attribution

The scientist says:

> `N represents X`.

This third claim does not follow automatically from the first two.

### Result

**RF-01 — Neural response regularity and analyst model are evidence for, but are not identical to, representational content.**

---

# 3. Tuning is conditional response structure, not content

A tuning relation can be written:

`r(x,c) = E[N | X=x, C=c]`

where `C` contains context, task, state, history and other conditions.

A neuron can be tuned to `X` because:

- X causally drives it;
- X covaries with a hidden variable;
- X is one component of mixed selectivity;
- behavioral state covaries with X;
- recurrent dynamics produce both N and X-related activity;
- the neuron participates in a control process linked to X.

Tuning therefore establishes a statistical response relation under the sampled conditions, not semantic target selection.

### Result

**RF-02 — Tuning is a conditional response property; it is neither sufficient nor necessary for determinate single-variable content.**

---

# 4. Encoding model is a methodological direction, not semantic encoding

Neuroscience often calls a model of the form:

`p(N | X)`

an **encoding model**.

That terminology is useful but dangerous.

A successful encoding model says X predicts neural response under the experimental distribution.

It does not establish:

- that X is what the neuron represents;
- that downstream circuitry uses X-like distinctions;
- that X rather than correlated X' fixes content;
- that the relation survives intervention/context change.

### Result

**RF-03 — Methodological `encoding` in neuroscience must not be silently promoted to MF3 semantic representation.**

---

# 5. Decoding is observer-side recoverability

A decoder estimates:

`X_hat = D(N)`.

Strong decoding accuracy demonstrates that information useful for recovering X exists in the sampled neural state.

But the decoder may exploit:

- correlations inaccessible to actual downstream circuits;
- a nonlinear function the brain does not implement;
- nuisance variables correlated with X;
- population-wide information no biological consumer reads in that form.

MF3-A/C therefore apply directly:

`decodable-from ≠ represented-by`.

### Result

**RF-04 — Neural decodability is an accessibility/recoverability claim relative to a decoder class and dataset, not sufficient evidence of systemically grounded content.**

---

# 6. Decoder complexity matters

The more expressive the external decoder, the weaker the inference from successful decoding to actual neural use.

A highly nonlinear decoder may extract distinctions that require operations unavailable to biological downstream circuits.

Linear/simple decodability can be stronger evidence of accessible organization under restricted consumer classes, but remains insufficient by itself.

### Result

**RF-05 — Decoder success must be indexed to decoder class, sample regime and biological plausibility; unrestricted decoding risks constructing rather than discovering the relevant variable.**

---

# 7. Information content ≠ representational content

If neural activity has mutual information with X:

`I(N;X) > 0`,

then N statistically distinguishes X states.

But many variables can simultaneously share information with N:

- current position;
- visual scene;
- reward expectation;
- movement speed;
- task phase;
- latent context.

MF3-B's contrastive question remains mandatory:

> Why X rather than correlated X'?

### Result

**RF-06 — Statistical information is necessary evidence for many neural codes but does not by itself determine neural semantic content.**

---

# 8. Mixed selectivity is a decisive single-neuron falsifier

Rigotti et al. showed prefrontal neurons responding to heterogeneous nonlinear mixtures of task variables. Importantly, task-relevant variables remained decodable from the population even when single-neuron selectivity to those variables was eliminated in analysis.

This defeats a simple ontology:

`one interpretable tuning curve → one represented variable`.

A population may implement a high-dimensional computational basis in which no single coordinate has the clean semantic status an analyst wants.

### Result

**RF-07 — Single-neuron semantic labels can be unstable or incomplete even when population-level information/function is strong.**

**RF-08 — Mixed selectivity can be computationally advantageous; interpretability of individual units is not a universal criterion for neural representation quality.**

---

# 9. Population representation is not just a collection of neuron labels

A population state:

`n(t) = [n_1(t), ..., n_k(t)]`

can encode/recruit relations that are not decomposable into independent one-neuron contents.

Relevant structure may lie in:

- covariance;
- subspaces;
- population trajectories;
- manifold coordinates;
- temporal relations;
- population likelihood functions;
- distributed role structure.

### Result

**RF-09 — Population content need not equal the union of independently interpreted single-cell contents.**

---

# 10. Place cells — strong spatial evidence, but not `cell = coordinate`

O'Keefe & Dostrovsky reported hippocampal units whose firing depended strongly on the animal's location. Muller, Kubie & Ranck later quantified spatially localized place fields.

This is excellent evidence for spatially organized neural activity.

But the strongest representational claim is not:

> `cell i permanently means coordinate (x,y)`.

Place fields are conditional on environment, cue configuration, task/history and network state.

### Result

**RF-10 — Place-cell activity supplies strong evidence for context-indexed spatial representation, not a timeless one-cell/one-coordinate code.**

---

# 11. Remapping falsifies fixed cell semantics

Environmental manipulations can cause hippocampal place fields to change location, firing rate or field membership.

Thus the same physical neuron can participate in different spatial maps across contexts.

The stable representational unit may therefore reside at another level:

- ensemble map;
- context-conditioned code;
- relational state;
- attractor/population configuration.

### Result

**RF-11 — Hippocampal remapping shows that neural content assignment can be context- and map-relative; neuron identity does not fix one permanent spatial referent.**

---

# 12. Reference frame is part of neural content

A neural variable can be tuned to:

- retinal coordinates;
- head-centered direction;
- body-centered position;
- allocentric world position;
- route-relative progress;
- object-relative location.

The numerical variable `angle` or `position` is incomplete without the relevant frame.

### Result

**RF-12 — Neural content claims must specify reference frame/granularity; `represents position/direction` is underspecified without the coordinate relation.**

---

# 13. Head-direction cells — relational orientation, not compass symbols

Taube, Muller & Ranck identified postsubicular neurons whose discharge varied strongly with head direction and was relatively insensitive to location in the experimental chamber.

Environmental cue manipulations altered orientation of the preferred firing direction, demonstrating that the code is anchored through environmental/contextual relations rather than constituting an absolute physical compass label in the neuron.

### Result

**RF-13 — Head-direction activity is best treated as a context-anchored directional relation, not an intrinsic direction symbol carried by a cell.**

---

# 14. Grid cells — periodic structure is not one-cell metric content

Hafting et al. found medial entorhinal neurons with multiple spatial firing fields arranged in a triangular/hexagonal grid-like pattern.

This reveals striking spatial geometry.

But one grid cell alone aliases many positions because its firing fields repeat periodically.

Unique position information can depend on population phase relationships across cells/modules and additional contextual inputs.

### Result

**RF-14 — Grid periodicity is strong evidence of structured spatial coding but demonstrates why single-cell tuning need not uniquely determine represented position.**

This links directly to MF1 aliasing and MF3-C population geometry.

---

# 15. Place/grid/head-direction are a system, not isolated dictionaries

Spatial navigation combines variables such as:

- location;
- direction;
- distance;
- movement;
- landmarks;
- context;
- goals.

The explanatory unit is therefore often a coupled representational/navigation system rather than independent semantic cells.

### Result

**RF-15 — Neural content can be relational and system-distributed across interacting code families; cell-class names should not be mistaken for complete semantic decomposition.**

---

# 16. Time cells extend the same lesson into temporal organization

MacDonald et al. found hippocampal neurons active at successive moments during temporal gaps, while those neurons also reflected location/behavioral variables. Changing the temporal structure led many cells to `retime`.

This demonstrates:

- temporal selectivity;
- context dependence;
- mixed content/variables;
- population sequence organization.

### Result

**RF-16 — `Time cell` is an empirical functional label for context-dependent temporal firing structure, not evidence that a cell carries one context-free symbol for an absolute time value.**

---

# 17. Causal perturbation is stronger than decoding

If manipulating N changes behavior/downstream state in the way predicted by an X-content attribution, evidence becomes substantially stronger than correlation alone.

Robinson et al. selectively activated hippocampal place-cell ensembles associated with behaviorally relevant locations and biased spatial-memory behavior.

This establishes genuine causal recruitment of place-cell activity in spatial behavior.

### Result

**RF-17 — Targeted perturbation that induces content-predicted downstream changes is strong evidence of systemic neural use.**

---

# 18. But causal use still does not uniquely fix content

Suppose activating ensemble N causes the animal to slow near a reward-associated place.

Candidate contents may include:

- `location L`;
- `reward expected at L`;
- `memory state associated with L`;
- `approach/stop policy state`;
- a compound relational state.

Causal efficacy narrows the hypothesis space but does not uniquely select the semantic target.

### Result

**RF-18 — Causal relevance is not semantic target determination; strong neural-content claims still require contrastive grounding among competing interpretations.**

---

# 19. Causal perturbation can itself change the code

Robinson et al. also observed stimulation-driven remapping effects.

Thus intervention may not simply `set the represented variable` while leaving the representational system intact; perturbation can change network state/code organization itself.

### Result

**RF-19 — Neural intervention must distinguish manipulating content within a stable code from perturbing/reconfiguring the code itself.**

This is the biological analogue of MF3-C active transformation vs passive coordinate change.

---

# 20. Necessity, sufficiency and content are separate

A neural population may be:

- necessary for a behavior;
- sufficient to bias/trigger a behavior;
- informative about X;
- downstream-accessible;

without X being its full representational content.

Conversely, redundant representations can make one population non-necessary even if it genuinely carries and uses X-content.

### Result

**RF-20 — Behavioral necessity/sufficiency and representational content are separate attribution axes.**

---

# 21. Motor cortex is a decisive alternative-explanation domain

Motor neuroscience historically often searched for movement parameters represented by individual neurons: direction, force, muscle activation, etc.

Churchland et al. showed that population activity during reaching exhibits structured rotational dynamics whose temporal evolution follows naturally from preceding preparatory state, even though the behavior itself is not simply periodic in the same manner.

This supports a dynamical-system explanation in which neural population state participates in generating movement rather than merely reporting movement parameters.

### Result

**RF-21 — Some neural activity may be better explained as dynamical mechanism/control state than as a continuously decoded descriptive representation of external variables.**

---

# 22. Dynamics and representation are not mutually exclusive

Reject the reverse overreaction:

> `if neural activity is dynamical, it cannot represent`.

A dynamical state can still be representational if the system recruits it as a proxy for a distinct target/model state under MF3 criteria.

The correct question is explanatory:

> Does representational attribution add predictive/causal/explanatory structure beyond treating the neural trajectory as mechanism itself?

### Result

**RF-22 — Dynamical mechanism and representation can coexist; neither description automatically excludes the other.**

---

# 23. Neural manifolds are geometry, not content

Population activity often occupies a lower-dimensional region/subspace/manifold of the ambient neural state space.

Gallego et al. found preserved population modes/manifold structure across distinct motor behaviors; later work found stable latent dynamics over long periods despite turnover in recorded neurons.

These are strong observations about population geometry/dynamics.

But MF3-C applies:

`manifold coordinate ≠ semantic content`.

### Result

**RF-23 — Neural manifolds organize accessible/dynamical population structure but do not by themselves determine what the population represents.**

---

# 24. Stable population structure can coexist with unstable unit identity

Long-term population-dynamics studies show that stable latent organization/behavioral decoding can persist despite turnover or instability in recorded single units.

This provides a powerful falsifier for a strict neuron-as-symbol dictionary.

### Result

**RF-24 — Functionally stable neural representation may be multiply realized across changing unit-level participation; stable content need not imply stable neuron-to-content assignment.**

---

# 25. Biological basis is physically privileged

MF3-C noted that arbitrary basis rotations can preserve information while changing unit locality.

In a biological circuit, actual neurons and synapses are physically privileged coordinates because downstream connectivity, noise, metabolism and plasticity operate on them.

So single-neuron analysis is not meaningless merely because alternative mathematical bases exist.

### Result

**RF-25 — Biological coordinates are causally privileged implementation variables even when representational content is population/distributed and basis-relative at higher analytical levels.**

---

# 26. Population code ≠ probability code

A neural population can carry information without representing a probability distribution.

Ma et al.'s probabilistic population-code framework provides one explicit model in which population activity parameterizes likelihood/posterior-like distributions and supports Bayesian combination.

The ontology lesson is conditional:

- such a representation is possible;
- uncertainty/distributional content can be distributed;
- variability alone does not prove probabilistic semantics.

### Result

**RF-26 — Neural variability/population activity is not automatically probabilistic representation; distributional content requires a model/use relation that supports probability-like operations/evaluation.**

---

# 27. Explicit vs implicit uncertainty

A system may be uncertainty-sensitive without representing an explicit probability distribution.

Possibilities include:

- explicit distribution parameters;
- sampling-based dynamics;
- gain/reliability codes;
- ensemble dispersion;
- decision policies indirectly adapted to uncertainty.

### Result

**RF-27 — Behavioral sensitivity to uncertainty does not uniquely determine neural uncertainty format/content.**

MF3-C's multiple-realization principle applies.

---

# 28. Temporal code vs rate code is not an ontology dichotomy

Neural content may depend on:

- mean firing rate;
- precise spike timing;
- latency;
- synchrony;
- phase;
- sequence;
- population trajectory.

These are vehicle/code formats.

The same target content might be available through several formats, and one format may carry different contents under different consumers.

### Result

**RF-28 — Rate/temporal/population codes are vehicle-format claims; content must be established separately.**

---

# 29. Receptive field ≠ represented object

A receptive field characterizes how stimulus configuration affects a neuron's response.

It does not follow that the neuron semantically represents the entire stimulus object occupying that field.

The neuron's response may reflect:

- local feature extraction;
- gain modulation;
- prediction error;
- recurrent context;
- routing/attention;
- control of downstream processing.

### Result

**RF-29 — Receptive-field characterization is an input–response property, not by itself a complete content attribution.**

---

# 30. Feature detector language must be typed

Calling a neuron a `feature detector` can mean:

1. it responds selectively to a feature;
2. its activity carries information about the feature;
3. downstream circuits use it to discriminate the feature;
4. it is biologically/functionally recruited as a proxy for the feature.

These are not equivalent.

### Result

**RF-30 — `Feature detector` should be unpacked into response selectivity, information, consumer use and representational grounding rather than treated as a primitive neural-semantic class.**

---

# 31. Biological grounding is plural

MF3-B's grounding routes become concrete in biology.

Neural content can be stabilized by combinations of:

- evolutionary proper function;
- developmental organization;
- individual learning;
- sensorimotor calibration;
- recurrent system role;
- current task recruitment;
- social/conventional interfaces in language-capable organisms.

### Result

**RF-31 — Biological content grounding is historically and functionally plural; evolutionary teleology is a strong route but not the sole determinant of neural content.**

---

# 32. Current tuning and historical function can diverge

A circuit can be:

- adapted;
- recalibrated;
- lesioned;
- repurposed;
- trained for a new task.

Therefore current response statistics can diverge from historical proper function.

### Result

**RF-32 — Neural content attribution should keep current causal recruitment, learned history and evolutionary function as separate grounding constraints rather than collapsing them.**

---

# 33. Misrepresentation is possible in neural systems

If a neural state is genuinely representational, MF3-B requires room for error without content drift.

Examples include candidate states corresponding to:

- wrong location estimate;
- incorrect head-direction estimate;
- false sensory hypothesis;
- miscalibrated magnitude;
- incorrect predicted outcome.

A theory that defines neural content as `whatever caused/currently correlates with this neural state` cannot explain such neural misrepresentation.

### Result

**RF-33 — Neural representation requires content stability sufficient to distinguish at least some erroneous neural tokens/states from content redefinition.**

---

# 34. Neural noise ≠ misrepresentation

A random spike or corrupted population state is not automatically a false representation.

Possible failure loci:

- physical noise;
- invalid neural state;
- misrepresentation;
- downstream misread;
- motor execution error.

### Result

**RF-34 — Neural noise, representational error and downstream behavioral error are distinct failure types.**

---

# 35. Neural control state ≠ descriptive representation

A motor setpoint or control variable may causally organize behavior without descriptively standing for a current external state.

Some control variables may be directive representations under MF3-B; others may simply implement dynamical dispositions.

### Result

**RF-35 — Control relevance alone does not establish descriptive representation; directive representation must be distinguished from nonrepresentational control dynamics.**

---

# 36. Attractor state ≠ representation by definition

An attractor is a dynamical property: nearby states converge toward a stable set/state.

An attractor can implement:

- memory;
- categorical decision;
- motor pattern;
- homeostatic regime;
- oscillator phase;

without automatically representing an external target.

### Result

**RF-36 — Attractor dynamics is an implementation/mechanism property, not a semantic criterion.**

An attractor becomes representational only when grounding/proxy/evaluation criteria are independently met.

---

# 37. Memory trace ≠ representation by definition

A synaptic change can causally influence future behavior while containing no online proxy state available for surrogate use.

Distinguish:

## Memory disposition/engram substrate

A durable physical change enabling later reconstruction/behavior.

## Memory representation

A reinstated or persistent state recruited as standing in for a past event/content.

### Result

**RF-37 — Memory storage disposition and active memory representation are distinct; not every plastic trace is a representational token.**

---

# 38. Replay can strengthen representational attribution

When neural sequences recur during offline/rest periods and preserve relations to experienced or prospective trajectories, the system is operating decoupled from current sensory input.

Decoupling is strong MF3-A evidence for proxy/model use.

But replay still requires grounding and functional analysis to determine whether it represents past trajectory, prospective path, value structure or internal dynamics.

### Result

**RF-38 — Decoupled neural replay is strong evidence for representational/model-like use, but sequence similarity alone does not uniquely determine content.**

---

# 39. Neural symbolhood requires more than cell classes

A `place cell`, `face cell` or `concept cell` label does not automatically satisfy MF3-E symbolic criteria.

Symbolic attribution requires evidence of:

- re-identifiable token/type roles;
- substitution/reuse;
- role/filler binding;
- composition;
- type-governed manipulation.

### Result

**RF-39 — Neural selectivity categories are not automatically neural symbols.**

---

# 40. Distributed neural symbolic structure remains admissible

MF3-E/Smolensky prevent the opposite error.

If a neural population implements stable role/filler binding, substitution and compositional operations, it could instantiate symbolic organization without one-neuron-per-symbol units.

### Result

**RF-40 — Neural symbolic representation, if present, may be distributed and dynamical; local symbolic neurons are not required.**

---

# 41. Neural binding claims need intervention, not decoder labels alone

Suppose an analyst decodes `agent`, `patient` and `object` from a population.

This does not establish the system represents role–filler bindings.

Stronger evidence would show:

- constituent reuse across contexts;
- independent role/filler manipulation;
- predictable effect of rebinding perturbations;
- downstream systematic recombination.

### Result

**RF-41 — Neural role/binding attribution requires relational and causal evidence beyond separate constituent decodability.**

---

# 42. Neural representation can be layer-relative

The same biological state may be interpreted at several levels:

- receptor signal;
- local feature;
- population latent state;
- perceptual estimate;
- motor affordance;
- task variable;
- symbolic/conceptual role.

MF3-B allows layered content when different consumers genuinely recruit the state differently.

### Result

**RF-42 — Neural content can be multi-level and consumer-relative without becoming arbitrary; each level needs its own grounding/use evidence.**

---

# 43. The decoder's-dictionary fallacy

A recurrent error pattern:

1. train decoder `D(N) -> X`;
2. label neuron/population with word `X`;
3. treat label as the system's own semantic dictionary.

This confuses observer interpretation with endogenous representation.

### Result

**RF-43 — An analyst's successful decoder/dictionary does not automatically belong to the biological system.**

This is the neural analogue of MF3-G probe caution and MF3-E analyst-ascribed symbols.

---

# 44. Strong neural attribution needs contrastive tests

For candidate content X, test plausible alternatives:

- X vs correlated X';
- distal vs proximal variable;
- sensory variable vs action affordance;
- current state vs predicted state;
- location vs context;
- object vs reward;
- descriptive vs directive role.

### Result

**RF-44 — Neural content attribution should be explicitly contrastive, not merely positive-fit based.**

---

# 45. Generalization matters

If N truly represents X at a claimed abstraction level, the relation should survive relevant nuisance variation within that scope.

Examples:

- position code across speed variation;
- category code across exemplars;
- direction code across location;
- rule code across stimuli.

Failure may reveal that the original variable was too abstract or confounded.

### Result

**RF-45 — Generalization across content-irrelevant variation is evidence for the proposed content grain, but the relevant invariances must be typed rather than maximized.**

---

# 46. Remapping does not refute representation

A common opposite mistake is:

> if code changes with context, it cannot represent location.

But context can be part of the representation relation.

The correct content may be:

`location-within-context/map`.

### Result

**RF-46 — Context-sensitive remapping refines the content specification; it does not automatically eliminate representational status.**

---

# 47. Neural code can be latent and task-relative

A population may preserve only distinctions required by the animal's current task/policy.

This mirrors MF3-D value-equivalent world models.

A brain need not maintain a complete state description to possess useful representation.

### Result

**RF-47 — Biological representation can be task-sufficient and selectively lossy; completeness is not a representation requirement.**

---

# 48. Direct sensorimotor mechanisms remain admissible

MF2 explicitly left nonrepresentational sensorimotor explanations open.

A tight feedback loop may transform sensory input into action without a state functioning as a decoupled/grounded proxy for a distinct target.

If representational language adds no counterfactual/explanatory work, MF3-A's job-description constraint recommends omitting it.

### Result

**RF-48 — Not every neural computation requires a representational description; direct dynamical/sensorimotor control remains an admissible explanation.**

---

# 49. Representation should earn explanatory work

The strongest practical test is:

> What can we explain or predict by saying `N represents X` that we cannot explain equally well by saying `N covaries with X` or `N participates in dynamics Y`?

Representation earns its place when it supports:

- content-specific perturbation predictions;
- error/misrepresentation analysis;
- decoupled inference/model use;
- transfer across contexts;
- consumer-specific surrogate operations;
- behavioral choices tied to represented alternatives.

### Result

**RF-49 — Neural representational vocabulary should perform explanatory work qua representation rather than merely rename a correlation.**

---

# 50. Neural Representation Evidence Profile

MF3-F rejects one scalar `representation score` but proposes independent evidence dimensions.

## A — Association / selectivity

Does neural activity covary/tune with X?

## I — Information / recoverability

Can X distinctions be decoded, under what decoder class and distribution?

## U — Endogenous usability

Is the information accessible/recruited by actual downstream circuitry?

## C — Causal recruitment

Do targeted interventions on the proposed vehicle alter X-specific downstream computation/behavior as predicted?

## G — Grounding / target determination

Why X rather than plausible correlated alternatives? What causal, functional, learned or historical relation anchors the target?

## E — Evaluability/error

Can the same content remain fixed while tokens/states become wrong, biased or miscalibrated?

## R — Robustness / scope

Does the attribution survive relevant context/nuisance variation, and is its valid scope explicit?

## D — Decoupling/model use

Can the state be recruited when the target is absent, future, remembered or simulated?

### Result

**RF-50 — Strong neural representation claims should report a multidimensional evidence profile rather than infer representation from any single statistic.**

---

# 51. Evidence strengths are not a mandatory ladder

Some representations cannot ethically/practically be causally manipulated.

Some external biological signals may have strong evolutionary grounding but limited decoupling.

Some memory/model states have strong decoupling but weak direct target causation.

Therefore no universal sequence such as:

`tuning < decoding < causality < representation`

is frozen.

### Result

**RF-51 — Neural representation evidence dimensions converge nonlinearly; absence of one evidence type does not universally refute representation.**

---

# 52. Minimal neural representation candidate

MF3-F proposes:

> **A neural state/population is strongly attributable as representing X when its structured distinctions are not merely correlated with X but are grounded and endogenously recruited by the biological system as a proxy for X (or an X-relative domain/possibility), under a content-appropriate evaluation relation, with evidence that survives relevant contrastive alternatives and context/scope tests.**

Causal perturbation and decoupled use are strong supporting evidence but are not individually universal requirements.

---

# 53. NeuralRepresentationEpisode schema

```text
NeuralRepEpisode = <
  N   : neural vehicle/state/population/trajectory,
  L   : biological level/region/circuit,
  Z   : vehicle state space / code format,
  X   : candidate target/domain,
  Φ   : proposed content/condition,
  F   : reference frame/granularity,
  Ctx : task/context/state,
  U   : endogenous consumer/use,
  B   : grounding basis/history/function,
  Int : intervention/causal evidence profile,
  Dec : decoder/accessibility evidence profile,
  E   : evaluation/error profile,
  S   : valid scope/generalization conditions,
  D   : decoupling/model-use profile
>
```

This schema forces an attribution to state more than `neuron X fires for Y`.

---

# 54. Neural-content wording discipline

MF3-F recommends replacing ambiguous claims with evidence-typed language.

Instead of:

> `Neuron N represents direction.`

prefer one of:

- `N is directionally tuned under context C.`
- `Direction is linearly decodable from population P.`
- `Downstream circuit Q uses P to discriminate direction.`
- `Perturbing P shifts direction-specific behavior.`
- `Convergent tuning/use/perturbation/history evidence supports a context-indexed directional representation.`

### Result

**RF-52 — Evidence-typed wording reduces semantic overclaim and preserves the distinction between observation and representational inference.**

---

# 55. Place-cell reconstruction under the MF3-F standard

What can we safely say?

1. hippocampal neurons show strong spatially selective firing;
2. ensembles organize spatial maps that depend on environment/context;
3. place codes can remap under environmental manipulation;
4. selective activation of behaviorally relevant place-cell ensembles causally biases spatial-memory behavior;
5. therefore place-cell populations have unusually strong evidence for systemic spatial representation;
6. nevertheless the exact content can be layered—location, context-linked location, memory state, reward/action relation—and must be tested contrastively.

### Result

**RF-53 — `Place representation` is strongly supported at the hippocampal ensemble/system level, while simplistic one-cell/one-place semantics is rejected.**

---

# 56. Head-direction reconstruction

Evidence profile:

- strong directional tuning;
- relative independence from location in canonical experiments;
- environmental cue anchoring/manipulation;
- stable preferred direction within context;
- population/circuit organization.

Safest content:

> a context-anchored estimate/state of heading relative to the operative reference frame.

Not:

> a neuron intrinsically means `north`.

### Result

**RF-54 — Head-direction content is relational/frame-indexed rather than an intrinsic symbolic direction label.**

---

# 57. Grid-cell reconstruction

Evidence profile:

- periodic spatial firing geometry;
- topographically/systematically organized population structure;
- position aliases at single-cell level;
- richer position information through population phase/module relationships.

Safest inference:

> grid-cell populations provide structured metric/phase-like spatial coding useful within navigation systems.

### Result

**RF-55 — Grid representations are paradigmatically population-geometric; single-cell periodicity is insufficient for unique spatial content.**

---

# 58. PFC mixed-selectivity reconstruction

Safest inference:

> high-dimensional population states carry and make task variables accessible in combinations that support flexible downstream mappings.

Avoid:

> every PFC neuron has one hidden semantic variable waiting to be named.

### Result

**RF-56 — Mixed-selectivity populations are evidence for distributed task-state representation/computational basis, not for a semantic dictionary of individual neurons.**

---

# 59. Motor-cortex reconstruction

Motor cortex supports movement through population dynamics with structured low-dimensional trajectories.

Some variables are decodable from those trajectories, but dynamics may be mechanistically primary for some questions.

Safest interpretation:

> representational and dynamical descriptions must be tested for explanatory necessity rather than assumed from tuning.

### Result

**RF-57 — In motor systems, population dynamics can explain computation without requiring every decodable kinematic variable to be an explicitly represented internal quantity.**

---

# 60. Biological representation is often active and closed-loop

Unlike a static codebook, neural representation participates in recurrent loops:

`world → sensor → neural state → action → changed world/sensing`.

Therefore the represented variable can depend on action history and active sensing.

### Result

**RF-58 — Neural representation is often embedded in closed-loop sensorimotor dynamics; content analysis must include action-conditioned grounding and acquisition where relevant.**

This links directly back to MF2 active perception.

---

# 61. Biological representation and embodiment

Neural states can represent body-relative variables:

- posture;
- limb configuration;
- heading;
- effort;
- interoceptive/body states.

Representation ontology should not privilege external distal objects.

### Result

**RF-59 — Neural representation domains include body/self-relative and action-relative variables, not only external-world descriptions.**

---

# 62. Neural representation is not necessarily conscious

Most neural representational processes, if genuine, need not enter conscious awareness.

MF2 already separated perception, attention and awareness.

### Result

**RF-60 — Conscious access is not constitutive of neural representation.**

---

# 63. Neural representation is not necessarily perceptual

Neural representations can be involved in:

- memory;
- planning;
- value;
- goals;
- action;
- social variables;
- language;
- abstract task state.

### Result

**RF-61 — Neural representation is broader than neural perception.**

---

# 64. Neural representation is not necessarily symbolic

Place/grid/head-direction/population probability codes can be representational without satisfying MF3-E symbol-type/compositional criteria.

### Result

**RF-62 — Neural representation does not imply symbolic representation.**

---

# 65. Neural code and biological meaning must not be conflated

A scientist may call a firing pattern a `code` because it correlates systematically with X.

MF3-C defined code more strictly as a grounded systematic assignment connecting content-relevant distinctions and vehicle distinctions.

### Result

**RF-63 — Descriptive neural-code language should state whether it means statistical mapping, decodability, consumer use or grounded representational code.**

---

# 66. Provisional axioms RF-01→RF-63

All RF propositions in this document are provisional constraints for MF3-I falsification. None are yet frozen Representation Foundations.

Core subset:

**RF-01** Phenomenon/model/semantic attribution are separate.

**RF-02** Tuning is conditional response structure, not sufficient content.

**RF-03** Neuroscientific encoding-model success is not semantic encoding by definition.

**RF-04** Decodability is observer-relative recoverability, not sufficient representation.

**RF-07–09** Mixed selectivity/population structure invalidate one-unit/one-variable ontology.

**RF-10–16** Place/grid/head-direction/time coding is context/frame/population dependent.

**RF-17–20** Causal perturbation strongly improves systemic-use evidence but does not alone fix semantic target; interventions can modify the code itself.

**RF-21–24** Dynamics/manifolds provide mechanism-level alternatives and population structure; geometry/dynamics are not content by themselves.

**RF-26–28** Uncertainty, population and temporal codes are formats whose semantic interpretation needs separate grounding.

**RF-31–34** Biological grounding/history/function and neural misrepresentation require typed analysis.

**RF-35–38** Control states, attractors, memory traces and replay must not be automatically collapsed into representation.

**RF-39–41** Neural symbol/binding claims require MF3-E role/composition evidence.

**RF-43–45** Decoder dictionaries, contrastive alternatives and generalization tests are central epistemic controls.

**RF-48–49** Nonrepresentational neural explanations remain admissible; representation must earn explanatory work.

**RF-50–52** Neural representation attribution should use a multidimensional evidence profile and evidence-typed wording.

---

# 67. Claims rejected by MF3-F

Reject as universal foundational claims:

- neural tuning is neural representation;
- a successful encoding model establishes semantic encoding;
- anything decodable from neural activity is represented by the brain;
- linear decoding proves endogenous use;
- the best external decoder reconstructs the brain's own semantic variables;
- mutual information fixes content;
- every selectively responsive neuron has one determinate semantic label;
- population content is just a set of single-neuron labels;
- place cell = fixed coordinate symbol;
- grid cell alone uniquely specifies position;
- head-direction cell intrinsically means a global compass direction;
- remapping disproves spatial representation;
- causal behavioral effect uniquely determines representational content;
- optogenetically setting a neural population necessarily sets a represented variable while leaving code semantics unchanged;
- necessary-for-behavior = represents-the-behavioral-variable;
- motor cortical activity must be interpreted as encoding external movement parameters;
- dynamical-system explanations exclude representation;
- neural manifold geometry equals semantic content;
- stable content requires stable neuron-to-content assignment;
- neural variability automatically represents uncertainty;
- probabilistic behavior proves an explicit probability code;
- receptive field equals represented object;
- attractor state is automatically representation;
- plastic memory trace is automatically an active representation;
- replay sequence similarity uniquely fixes past/future content;
- place/face/concept cell labels automatically imply neural symbols;
- analyst-decoded roles/fillers prove neural binding;
- biological representation requires consciousness;
- all neural computation is representational;
- all useful neural states should receive representational labels.

---

# 68. Primary/original literature anchors

- O'Keefe, J. & Dostrovsky, J. (1971), `The hippocampus as a spatial map. Preliminary evidence from unit activity in the freely-moving rat`, *Brain Research* 34(1), 171–175. DOI: 10.1016/0006-8993(71)90358-1.
- Muller, R. U., Kubie, J. L. & Ranck, J. B. Jr. (1987), `Spatial firing patterns of hippocampal complex-spike cells in a fixed environment`, *Journal of Neuroscience* 7(7), 1935–1950. DOI: 10.1523/JNEUROSCI.07-07-01935.1987.
- Muller, R. U. & Kubie, J. L. (1987), `The effects of changes in the environment on the spatial firing of hippocampal complex-spike cells`, *Journal of Neuroscience* 7(7), 1951–1968. DOI: 10.1523/JNEUROSCI.07-07-01951.1987. Environment-dependent place-field change/remapping evidence.
- Taube, J. S., Muller, R. U. & Ranck, J. B. Jr. (1990), `Head-direction cells recorded from the postsubiculum in freely moving rats. I. Description and quantitative analysis`, *Journal of Neuroscience* 10(2), 420–435. DOI: 10.1523/JNEUROSCI.10-02-00420.1990.
- Taube, J. S., Muller, R. U. & Ranck, J. B. Jr. (1990), `Head-direction cells recorded from the postsubiculum in freely moving rats. II. Effects of environmental manipulations`, *Journal of Neuroscience* 10(2), 436–447. DOI: 10.1523/JNEUROSCI.10-02-00436.1990.
- Hafting, T., Fyhn, M., Molden, S., Moser, M.-B. & Moser, E. I. (2005), `Microstructure of a spatial map in the entorhinal cortex`, *Nature* 436, 801–806. DOI: 10.1038/nature03721. Grid-cell periodic spatial firing.
- Ma, W. J., Beck, J. M., Latham, P. E. & Pouget, A. (2006), `Bayesian inference with probabilistic population codes`, *Nature Neuroscience* 9, 1432–1438. DOI: 10.1038/nn1790. Constructive population-code model for distributional/probabilistic neural representation.
- MacDonald, C. J., Lepage, K. Q., Eden, U. T. & Eichenbaum, H. (2011), `Hippocampal “time cells” bridge the gap in memory for discontiguous events`, *Neuron* 71(4), 737–749. DOI: 10.1016/j.neuron.2011.07.012.
- Churchland, M. M. et al. (2012), `Neural population dynamics during reaching`, *Nature* 487, 51–56. DOI: 10.1038/nature11129. Population-dynamical account of motor cortical activity challenging simple parameter-encoding views.
- Rigotti, M. et al. (2013), `The importance of mixed selectivity in complex cognitive tasks`, *Nature* 497, 585–590. DOI: 10.1038/nature12160. Mixed selectivity, population decoding and high-dimensional computational advantage.
- Gallego, J. A. et al. (2018), `Cortical population activity within a preserved neural manifold underlies multiple motor behaviors`, *Nature Communications* 9, 4233. DOI: 10.1038/s41467-018-06560-z.
- Gallego, J. A. et al. (2020), `Long-term stability of cortical population dynamics underlying consistent behavior`, *Nature Neuroscience* 23. DOI: 10.1038/s41593-019-0555-4. Stable latent population dynamics across long time spans despite changes/turnover in recorded units.
- Robinson, N. T. M. et al. (2020), `Targeted Activation of Hippocampal Place Cells Drives Memory-Guided Spatial Behavior`, *Cell* 183(6), 1586–1599.e10. DOI: 10.1016/j.cell.2020.09.061. Targeted place-cell ensemble activation causally biases spatial-memory behavior and can induce remapping.

---

# 69. MF3-F reconstruction

The old implicit picture was:

```text
world variable X
     ↓
neuron tuned to X
     ↓
therefore neuron represents X
```

MF3-F replaces it with:

```text
World/body/task variable X
         │
         ├─ causal/statistical relation
         ▼
Neural vehicle N / population trajectory
         │
         ├─ information/selectivity
         ├─ vehicle code/geometry
         ├─ context/reference frame
         ├─ actual downstream recruitment
         ├─ learned/evolutionary grounding
         ├─ perturbational causal role
         ├─ error/evaluation structure
         └─ decoupled/model use where present
                  │
                  ▼
          Biological computation/action
```

The semantic attribution `N represents X` becomes warranted only when the evidence profile makes **proxy/grounding** explanatorily better than mere correlation or mechanism-only descriptions.

---

# 70. Deep synthesis

The strongest MF3-F conclusion is not `the brain does not represent` and not `everything in the brain represents`.

It is:

> **Neural representation is an explanatory relation that must be earned by convergent evidence. Tuning and decoding establish structured dependence; endogenous use and causal perturbation establish stronger systemic relevance; grounding, contrastive target determination, error structure, context/frame and scope establish content. Population/dynamical organization may be the correct vehicle even when individual neurons lack stable semantic labels.**

Thus the core non-collapses are:

`Tuning ≠ Encoding-model fit ≠ Information ≠ Decodability ≠ Causal Use ≠ Grounded Content.`

`Single neuron ≠ representation unit.`

`Population geometry ≠ content.`

`Causal efficacy ≠ semantic target determination.`

`Control state ≠ representation.`

`Attractor ≠ representation.`

`Memory trace ≠ active memory representation.`

`Neural selectivity ≠ neural symbol.`

And the positive candidate is:

> **A neural representation is a biologically grounded, endogenously recruited proxy relation instantiated in neural states/populations/trajectories, whose content is contrastively identifiable and evaluable within a declared context/reference frame/scope.**

---

# 71. MF3-G handoff — Artificial Representation

MF3-F now gives the exact discipline needed for artificial networks.

MF3-G should attack:

- activation/tuning in ANN units;
- probe decodability;
- concept neurons/features;
- sparse autoencoders;
- mechanistic interpretability features;
- residual-stream/vector representations;
- causal tracing/activation patching;
- representation engineering/interventions;
- superposition/polysemanticity;
- distributed features;
- world-model latents;
- LLM hidden states;
- multimodal alignment;
- token embeddings vs contextual states;
- chain-of-thought/external scratchpad vs internal representation;
- learned variables under gauge/reparameterization;
- causal abstraction;
- whether internal states are systemically grounded or only derived from human labels/training objectives;
- when ANN states are better understood as control/dynamical computational states rather than representations;
- artificial symbol/binding/compositionality evidence.

Key inherited discipline:

`Probe decoding ≠ internal representation.`

`Activation intervention ≠ semantic target determination.`

`Training label ≠ realized content.`

`Feature visualization ≠ grounding.`

`Geometry ≠ content.`

`World-model latent ≠ physical latent cause.`

`Symbolic I/O ≠ classical symbolic internal architecture.`

**Next: MF3-G — Artificial Representation.**
