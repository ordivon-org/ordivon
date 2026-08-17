# Ordivon Media Foundations — MF3-G Artificial Representation

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 10 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3-A/B/C/D/E/F complete and provisional.  
**Status:** MF3-G complete as a provisional Representation round; Representation Foundations remain UNFROZEN.  
**Next:** MF3-H — External / Public Representation.

---

# 1. Problem statement

Artificial neural networks create an unusually powerful testbed for representation ontology because an investigator can often:

- inspect every activation and parameter;
- duplicate the system exactly;
- train arbitrary decoders/probes;
- apply coordinate transforms;
- ablate or patch components;
- replace intermediate states;
- edit weights;
- generate controlled counterfactual inputs;
- compare behavioral consequences;
- retrain from altered data/objectives.

This makes artificial systems experimentally cleaner than biological systems in some respects.

It also creates new epistemic traps.

A researcher may accidentally infer:

`human label → probe → feature decomposition → causal effect → model's intrinsic semantic variable`

without proving the intermediate equivalences.

MF3-G therefore asks:

> **When is an ANN activation, direction, sparse feature, circuit, latent state or symbolic interface genuinely representational for the artificial system, rather than merely correlated, externally decodable, analyst-decomposed, behaviorally steerable or mechanically causal?**

The central non-collapse is:

`Activation selectivity ≠ Probe decodability ≠ Learned decomposition ≠ Mechanistic variable ≠ Causal intervention effect ≠ Grounded artificial content.`

---

# 2. Artificial representation inherits MF3-F but adds new evidence channels

MF3-F established for biology:

`Tuning ≠ Information ≠ Decodability ≠ Endogenous Use ≠ Causal Recruitment ≠ Grounded Content`.

Artificial systems preserve all these distinctions but add stronger access to:

- exact weights/architecture;
- training data and objective;
- activation-level interventions;
- component replacement;
- causal-model alignment;
- repeated retraining under controlled changes;
- mechanistic equivalence tests;
- coordinate/gauge transformations.

### Result

**RG-01 — Artificial systems allow unusually strong mechanistic evidence, but stronger observability does not remove the representation/content problem.**

---

# 3. Training objective is not internal content

A supervised network may be optimized for label `cat`.

It does not follow that every intermediate activation predictive of the label represents `cat`.

The model may exploit:

- texture;
- background;
- watermark;
- camera metadata;
- correlated context;
- shortcut features.

MF3-B already rejected:

`training label/objective = realized internal content`.

Artificial systems make the distinction even sharper because objective, gradient pressure and learned mechanism can be inspected separately.

### Result

**RG-02 — Designer objective, dataset label and realized internal content are separate attribution layers.**

---

# 4. Optimization norm ≠ semantic norm

Loss functions specify what parameter updates are rewarded during training.

They do not automatically specify what each internal state means.

Two models trained under identical loss can discover different internal codes.

One model can use a variable only indirectly or exploit a shortcut while achieving the same objective.

### Result

**RG-03 — Optimization loss supplies a training norm, not a complete token-level semantic evaluation rule for internal representations.**

---

# 5. Unit activation/selectivity is the artificial analogue of neural tuning

An ANN neuron/unit may activate strongly on examples associated with X.

This establishes a conditional activation regularity:

`a_i(x,c)`.

It does not by itself establish:

- X as content;
- monosemanticity;
- downstream use;
- causal necessity;
- stable reference across contexts.

### Result

**RG-04 — ANN unit selectivity/tuning is evidence of activation structure, not sufficient evidence of artificial semantic content.**

---

# 6. Maximum activating examples can mislead

Interpretability often begins by collecting examples producing high activation.

But a unit/feature may:

- have one coherent pattern at high activation;
- respond to unrelated patterns at moderate activation;
- combine multiple sparse features;
- activate because of a correlated lexical artifact.

Toy-model superposition work explicitly reproduces this possibility: a polysemantic neuron can have a dominant feature at high magnitude while carrying secondary features at lower magnitude.

### Result

**RG-05 — Top-activating examples are a hypothesis-generation tool, not proof of monosemantic content.**

---

# 7. Superposition destabilizes neuron-as-feature ontology

Elhage et al.'s toy models show how sparse features can be represented in superposition, with more features than available dimensions and polysemantic neurons emerging under some regimes.

The ontology lesson is not that every large network necessarily uses exactly the toy-model geometry.

It is:

> one physical neuron/dimension need not correspond to one computational feature.

### Result

**RG-06 — Unit identity is not a reliable universal representation unit; features may be distributed across directions and directions may participate in multiple features.**

---

# 8. Superposition is a hypothesis, not a universal explanatory theorem

Toy models establish possibility and derive qualitative predictions.

They do not prove that every observed polysemantic feature in every model is caused by the same superposition mechanism.

### Result

**RG-07 — Superposition should be treated as a mechanistic hypothesis requiring model-specific evidence, not an automatic explanation for all interpretability ambiguity.**

---

# 9. Feature ≠ neuron ≠ direction ≠ SAE latent

The word `feature` is overloaded.

MF3-G distinguishes:

## Behavioral/semantic feature

A distinction meaningful in the target/task/domain.

## Computational feature

A reusable internal variable/condition that participates in model computation.

## Geometric feature direction

A direction/subspace in an activation space.

## Sparse dictionary feature

A latent variable learned by an external sparse coding/SAE procedure.

## Unit/neuron

A privileged coordinate in the implemented architecture.

These can align, but alignment is an empirical result.

### Result

**RG-08 — `Feature` must be typed; semantic, computational, geometric, SAE-latent and neuron-level features are not interchangeable.**

---

# 10. Sparse autoencoders are analyst models of model activations

An SAE learns approximately:

`x ≈ b + Σ_i f_i(x) w_i`

under reconstruction and sparsity objectives.

This produces a new learned representation of the original model's representation.

Therefore the SAE feature space is not identical to the model activation space and does not automatically reveal an ontologically privileged basis.

### Result

**RG-09 — SAE latents are features of an interpretability model fitted to the target model's activations; they require separate evidence to count as variables genuinely used by the original model.**

---

# 11. SAE interpretability is real evidence, not semantic proof

Bricken/Templeton-style sparse autoencoder work finds many latents whose activation examples are coherent, abstract, multilingual or multimodal, and whose steering affects model behavior.

This is important convergent evidence.

But even the originating work emphasizes incomplete reconstruction, dead features, unknown optimal dictionary size and imperfect quality metrics.

### Result

**RG-10 — Interpretable and causally steerable SAE features are stronger than purely descriptive clusters, but their semantic and mechanistic status remains empirical rather than guaranteed by the SAE objective.**

---

# 12. Feature splitting falsifies canonical-feature assumptions

As dictionary size or sparsity changes, one apparent feature may split into multiple more specific latents.

Therefore an analyst's chosen SAE hyperparameters can change the apparent ontology.

### Result

**RG-11 — SAE feature identity can be granularity/hyperparameter dependent; one learned dictionary does not establish a unique canonical concept inventory.**

---

# 13. Feature absorption is a stronger falsifier

Chanin et al. identify `feature absorption`: a seemingly interpretable/monosemantic SAE latent can fail to fire on examples that clearly instantiate the target feature because its activation has been absorbed into other latents.

This means:

> apparent precision on selected activation examples can coexist with poor recall of the hypothesized content.

### Result

**RG-12 — A feature label requires bidirectional testing: not only `when latent fires, is X present?` but also `when X is present, does the latent reliably participate?`**

---

# 14. Sparse feature extraction faces an identifiability problem

Different dictionaries may reconstruct the same activation distribution with different feature decompositions.

MF3-C's gauge/non-identifiability discipline applies.

Sparse priors add a preference but do not magically prove that the learned basis equals the model's intrinsic computational basis.

### Result

**RG-13 — Sparse decomposition introduces inductive assumptions; sparsity/interpretablity can select a useful basis without establishing uniqueness or intrinsic semantic privilege.**

---

# 15. MIB supplies an important benchmark falsifier

The Mechanistic Interpretability Benchmark evaluates methods against known/controlled circuit and causal-variable targets.

Its reported results show that, on its causal-variable localization tasks, supervised Distributed Alignment Search outperformed other methods and SAE features were not better than raw neurons.

The exact ranking is benchmark-dependent, but the ontology lesson is robust:

> greater human interpretability of a decomposition does not guarantee better localization of the model's actual causal variable.

### Result

**RG-14 — Interpretability quality and causal-variable faithfulness are distinct evaluation axes.**

---

# 16. `Reasoning feature` labels are especially vulnerable

Recent 2026 falsification-oriented work on SAE reasoning features shows that many contrastively selected `reasoning` features can be activated by lexical artifacts and can fail to activate on reasoning examples; steering these features produces little or negative reasoning improvement in the tested settings.

This is exactly the MF3-B/F contrastive-content problem.

### Result

**RG-15 — High-level feature labels such as `reasoning`, `deception`, `emotion` or `truth` require adversarial contrastive falsification against lexical/style/task correlates.**

---

# 17. Probe decodability remains weak evidence

A probe `D(h) -> X` demonstrates that X is recoverable from hidden state h under the probe class and data distribution.

Hewitt–Liang and Elazar et al. show why this cannot establish behavioral use.

Elazar et al. explicitly find conventional probing performance need not correlate with task importance.

### Result

**RG-16 — Probe success establishes observer-side accessibility, not endogenous computational use.**

---

# 18. Amnesic probing strengthens but does not solve the problem

Amnesic probing removes a probe-defined information subspace and checks whether model behavior changes.

This asks a stronger causal/use question.

However:

- removal may damage unrelated information;
- target variables can be redundantly encoded;
- the intervention can move the representation off its natural manifold;
- failure to affect behavior can reflect alternative pathways.

### Result

**RG-17 — Information-removal interventions are stronger use evidence than ordinary probes but remain intervention-model dependent.**

---

# 19. Causal intervention ≠ semantic target determination

If adding a direction changes sentiment, this establishes a causal relation between the manipulated activation and output sentiment.

It does not uniquely prove that the direction's content is `sentiment`.

It may encode or induce:

- lexical style;
- topic;
- response prior;
- instruction-following mode;
- correlated persona state;
- multiple entangled variables.

### Result

**RG-18 — Behavioral steering provides causal efficacy evidence, not by itself unique semantic interpretation.**

---

# 20. Steering vector ≠ concept vector

Activation Addition / contrastive activation steering shows that simple activation-space directions can causally control high-level output properties.

This is significant evidence of a low-complexity causal control direction.

But a steering vector is defined by a contrast and intervention recipe, not directly by ontology.

### Result

**RG-19 — A successful steering vector should be called a causal control/intervention direction until contrastive, reuse and grounding evidence supports stronger `concept representation` language.**

---

# 21. Off-manifold interventions complicate interpretation

Artificial activation edits can produce states that normal model computation never generates.

Behavioral effects from such states can reflect:

- genuine manipulation of an internal variable;
- distribution shift inside the network;
- saturation;
- accidental activation of many mechanisms.

### Result

**RG-20 — Artificial interventions must distinguish naturalistic variable substitution from arbitrary off-manifold perturbation.**

---

# 22. Activation patching localizes causal contribution, conditionally

Activation patching/casual tracing compares clean and corrupted runs and replaces internal activations to test recovery/change of target behavior.

This gives stronger component-level causal evidence than passive attribution.

But Zhang & Nanda show results can depend substantially on:

- corruption method;
- patching metric;
- evaluation choice.

### Result

**RG-21 — Activation-patching localization is intervention- and metric-relative; patching results are causal evidence about a specified counterfactual experiment, not context-free component semantics.**

---

# 23. Causal tracing factual recall gives a strong but scoped case

Meng et al.'s causal tracing identifies middle-layer feed-forward computations important for factual predictions, then ROME directly edits model weights to change specific factual associations while testing specificity/generalization.

This combination is stronger than decoding because it links localization, intervention and behavioral generalization.

### Result

**RG-22 — Localization + targeted edit + content-predicted generalization is strong evidence for a scoped artificial representational mechanism.**

Still, `fact stored in MLP` must remain scope- and method-qualified rather than treated as literal database storage.

---

# 24. Causal abstraction is stronger than component causality

Geiger et al. align internal neural states with variables in an interpretable causal model and use interchange interventions to test whether swapping the candidate neural variable causes the effects predicted by the high-level causal model.

This directly tests whether a network realizes a proposed causal representational structure.

### Result

**RG-23 — Interchange-intervention causal abstraction is among the strongest available evidence that an artificial internal state realizes a proposed abstract variable/role.**

---

# 25. Causal abstraction still depends on the proposed high-level model

Even a successful interchange intervention is relative to:

- selected high-level variables;
- alignment map;
- tested intervention family;
- input distribution;
- causal abstraction criterion.

Alternative high-level abstractions may also fit.

### Result

**RG-24 — Causal abstraction verifies a typed correspondence to a proposed abstract model; it does not imply a unique metaphysically privileged semantic decomposition.**

---

# 26. Replacement models add a new truth boundary

Cross-layer transcoders and related replacement models approximate original network computations using more interpretable sparse features.

Attribution graphs can then be traced through the replacement model.

This is powerful because feature–feature interactions become easier to inspect.

But the graph is directly a mechanism of the **replacement model**; inference to the original model depends on approximation fidelity.

### Result

**RG-25 — Mechanistic interpretation through a replacement model requires an explicit approximation/reconstruction truth boundary.**

---

# 27. Attribution graph ≠ complete computation graph

2025 circuit-tracing work explicitly presents attribution graphs as partial, hypothesis-generating descriptions, with limitations from reconstruction error, attention treatment, suppression motifs and global-circuit incompleteness.

### Result

**RG-26 — Attribution graphs are evidence-bearing partial surrogate explanations, not literal complete causal graphs of the original network.**

---

# 28. Feature circuits are stronger than isolated features

A feature gains stronger mechanistic status when:

- upstream conditions activate it;
- downstream features read/use it;
- interventions produce predicted path-specific effects;
- alternative paths can be distinguished;
- the feature participates systematically across prompts/contexts.

### Result

**RG-27 — Reusable causal circuit participation is stronger evidence of endogenous computational representation than isolated feature interpretability.**

---

# 29. Current 2025 circuit tracing reveals reusable internal structure, but method-relative

Attribution-graph studies of Claude 3.5 Haiku report features/circuits supporting multilingual processing, planning, reasoning and hallucination-related behaviors, with follow-up intervention tests.

These results materially strengthen the case that large models possess reusable abstract internal variables beyond surface token correlations.

But the authors themselves emphasize that `feature` remains fuzzy and that sparse decomposition is an imperfect microscope.

### Result

**RG-28 — Mechanistically reusable abstract internal structure is empirically supported in frontier LMs, while exact feature ontology remains method-relative and incomplete.**

---

# 30. Natural-language explanations are representations of representations

Natural Language Autoencoders (NLAs, 2026) train an activation verbalizer and reconstructor so an internal activation can be compressed into natural-language text from which the activation can be approximately reconstructed.

This produces:

`activation → text explanation → reconstructed activation`.

The text is therefore a learned code/surrogate for the activation.

It is not automatically a privileged ground-truth description of `what the model is thinking`.

### Result

**RG-29 — NLA text is an externally learned representational surrogate of model activations; reconstruction and downstream tests support usefulness, not literal semantic transparency by definition.**

---

# 31. Reconstruction fidelity ≠ semantic fidelity

Two explanations may reconstruct similar activation structure while using different linguistic abstractions.

A text bottleneck can omit distinctions irrelevant to reconstruction under the trained decoder.

Conversely, fluent explanations may hallucinate human-readable structure that only partially matches causal use.

### Result

**RG-30 — Activation reconstruction, human interpretability and semantic/mechanistic faithfulness are separate evaluation axes for natural-language interpretability tools.**

---

# 32. J-space / global-workspace evidence is unusually strong system-use evidence

Anthropic's 2026 J-space work reports an internal low-dimensional family of patterns discovered through a Jacobian-based lens, with unusually broad connectivity and reuse.

A particularly strong intervention substitutes a `France` representation with `China`; multiple distinct downstream questions then change coherently—capital, language, continent, currency.

This is stronger than probe decodability because one internal edit is reused by multiple downstream computations in content-consistent ways.

### Result

**RG-31 — Cross-task content-preserving substitution with one shared internal edit is strong evidence for a reusable variable-like artificial representation.**

---

# 33. J-space remains a method-defined lens, not the final ontology

The J-lens is constructed from how activation directions affect possible future word outputs and reportedly has limitations, including a bias toward concepts expressible as single tokens.

Thus `J-space` is an empirically privileged representational interface discovered by a particular analysis, not automatically the complete set of model concepts.

### Result

**RG-32 — A highly functional internal workspace can be real without its discovery coordinates being the unique or exhaustive semantic basis of the model.**

---

# 34. Cross-task reuse is a major representation criterion

Suppose internal variable V can be manipulated once and many different downstream tasks use it appropriately.

This shows:

- stable reusable identity;
- endogenous accessibility;
- compositional/task-independent recruitment;
- causal influence across consumers.

### Result

**RG-33 — Cross-consumer/cross-task reuse is exceptionally strong evidence that an artificial state functions as a systemic proxy variable rather than a task-specific correlation.**

---

# 35. Persona/emotion axes demonstrate causal abstract organization without implying phenomenology

2026 work on an `Assistant Axis` and emotion-related internal patterns reports activation directions/representations whose steering changes persona susceptibility, preferences or behavior.

These findings support functional abstract representation claims.

They do **not** establish human-like subjective emotion or phenomenal experience.

### Result

**RG-34 — Functional representation of a psychological/social concept is distinct from possessing the corresponding human phenomenology.**

This is the artificial analogue of MF2's awareness boundary.

---

# 36. Behavior label ≠ represented concept

A direction that increases `sycophancy`, `deception`, or `desperation-like behavior` may represent:

- a broad latent policy/persona state;
- a more specific behavioral tendency;
- a contextual control variable;
- several correlated features.

### Result

**RG-35 — Behavioral phenotype names should not be copied directly into internal semantic labels without contrastive/mechanistic decomposition.**

---

# 37. Multilingual/multimodal invariance strengthens abstraction claims

A candidate feature that activates for the same concept across:

- multiple languages;
- text and images;
- paraphrases;
- concrete and abstract instances;

survives more nuisance variation than a lexical detector.

### Result

**RG-36 — Cross-modal/cross-lingual generalization is strong evidence that a candidate representation tracks a more abstract equivalence class than surface form.**

Still, it does not alone prove endogenous use or unique target content.

---

# 38. CLIP demonstrates derived multimodal grounding but not full world grounding

CLIP learns image/text representations from hundreds of millions of image-caption pairs via contrastive matching, enabling zero-shot transfer using natural-language prompts.

This establishes a strong learned alignment among visual patterns and conventional linguistic distinctions.

But image-text alignment is still mediated by the dataset and public language; it does not by itself supply causal/action grounding in the physical world.

### Result

**RG-37 — Multimodal contrastive learning can provide strong derived/cross-modal grounding while remaining distinct from embodied action-causal grounding.**

---

# 39. Embodiment adds grounding routes, not automatic semantic truth

PaLM-E incorporates continuous sensor modalities into an embodied language model; RT-2 jointly trains vision-language and robot-action data, representing actions in token form and using the resulting policy for closed-loop robot control.

These systems add:

- real sensor coupling;
- action consequences;
- closed-loop environmental feedback;
- embodiment-specific success/failure.

### Result

**RG-38 — Embodied artificial systems can acquire stronger systemic sensorimotor grounding than text-only models, but embodiment alone does not uniquely determine every internal state's semantic content.**

---

# 40. Grounding is a graph in artificial systems too

Artificial grounding can combine:

- public linguistic convention;
- human-labeled datasets;
- image/text co-occurrence;
- synthetic supervision;
- reward/task feedback;
- sensorimotor interaction;
- tool/API interfaces;
- environment state variables;
- internally learned model states.

### Result

**RG-39 — Artificial semantic grounding is typically hybrid and graph-mediated rather than purely linguistic or purely sensorimotor.**

---

# 41. Tool/API tokens can have strong derived reference

A string such as a database key or API argument may have exact public/designed semantics through an external protocol even if the model learned it only from text.

If tool execution feeds results back into the system, reference becomes operationally closed through environment interaction.

### Result

**RG-40 — Designed external interfaces can provide exact derived/conventional grounding routes independent of whether internal language-model states have intrinsic human-like semantics.**

---

# 42. Token embedding ≠ contextual representation

A tokenizer token ID maps to a learned embedding vector.

But after attention/MLP processing, the same token type can occupy radically different contextual hidden states.

Therefore:

`token identity ≠ token embedding ≠ contextual token state ≠ concept`.

### Result

**RG-41 — Static token embeddings and contextual internal representations are different representational levels and should not be semantically conflated.**

---

# 43. Residual stream is a communication substrate, not one semantic vector table

Transformer residual streams aggregate many component outputs and support downstream computation across layers.

Different subspaces/directions can be read by different heads/MLPs.

### Result

**RG-42 — Residual-stream coordinates are implementation/communication variables; semantic attribution belongs to typed directions/subspaces/circuits only after use/grounding evidence.**

---

# 44. Basis/gauge discipline is especially important for artificial networks

An invertible linear basis transformation of an internal vector representation can preserve full model function when connected weights are transformed consistently.

Thus individual coordinates are not semantic primitives.

However, original network coordinates are physically/computationally privileged by parameter sparsity, architectural modules and implementation cost.

### Result

**RG-43 — Artificial representation analysis must distinguish functional gauge freedom from the implemented basis actually used by network components.**

---

# 45. Linear representation hypothesis is a hypothesis family

Many interpretability methods assume important concepts correspond approximately to linear directions or low-dimensional subspaces.

Successful linear probes and steering give substantial evidence that some useful variables are linearly accessible/controllable.

But this does not imply all model content is linear or that each semantic concept has one unique direction.

### Result

**RG-44 — Linearity is an empirically fruitful representational format hypothesis, not an ontology-wide law of artificial cognition.**

---

# 46. Same concept can have multiple directions/implementations

A semantic distinction may be:

- represented differently by layer;
- split across contexts;
- distributed across a subspace;
- encoded in different bases across models;
- realized by multiple redundant features.

### Result

**RG-45 — Artificial content does not require one globally unique concept vector.**

---

# 47. One direction can support multiple interpretations

A steering or probe direction may entangle:

- concept;
- style;
- position;
- token frequency;
- policy state.

### Result

**RG-46 — Direction-level causal effects require factorized contrastive testing before semantic naming.**

---

# 48. World-model latent ≠ physical latent cause

MF3-D applies unchanged.

Artificial world-model state may represent:

- predictive sufficient statistics;
- belief state;
- value-equivalent state;
- action-conditioned task state;
- latent physical causes;
- model-relative coordinates.

### Result

**RG-47 — Learned world-model latents gain causal/world-state content only through grounding and intervention/query evidence, not from being hidden variables in a generative model.**

---

# 49. Planning sufficiency can outrank reconstructive fidelity

MuZero/value-equivalence results remain decisive artificial cases.

An internal state can be highly useful for action while discarding details irrelevant to planning.

### Result

**RG-48 — Artificial representation should be evaluated against query/consumer scope; full sensory/world reconstruction is not required for strong task/world-model representation.**

---

# 50. Mechanistic state ≠ representation by definition

A hidden activation can be causally indispensable for computation while functioning only as:

- accumulator;
- routing gate;
- normalization signal;
- control variable;
- algorithmic scratch state.

If no distinct target/domain proxy relation is needed, representation language may add nothing.

### Result

**RG-49 — Mechanistic importance is not sufficient for representational status.**

---

# 51. Algorithmic variable can become representational when it stands in for a distinct domain variable

A carry bit in an addition circuit may be a formal/internal algorithmic variable.

If it systematically stands in for a mathematical carry condition under system use/evaluation, representational attribution can be appropriate.

### Result

**RG-50 — Internal computational variables can be representations, but only when proxy/grounding/evaluation relations are established rather than inferred from causal necessity alone.**

---

# 52. Symbolic I/O still does not establish symbolic internals

MF3-E applies fully to LLMs.

Discrete tokens are formal symbols at the interface.

Continuous transformer internals may implement symbolic role/binding structure, but this requires evidence beyond sequence generation.

### Result

**RG-51 — Artificial symbolic input/output and internal symbolic/compositional representation are distinct claims.**

---

# 53. Artificial compositionality requires relational interventions

To establish role/filler structure, stronger tests include:

- swap filler while preserving role;
- swap roles while preserving fillers;
- novel recombination;
- interchange intervention on candidate variables;
- cross-context constituent reuse.

### Result

**RG-52 — Artificial role–filler/compositional representation should be demonstrated by content-preserving rebinding and systematic intervention, not merely by separate probe decodability of constituents.**

---

# 54. Causal abstraction provides a bridge to symbolic structure

Geiger-style interchange intervention can test whether hidden states instantiate variables in a compositional causal model.

This is a strong route for proving that distributed neural states implement symbolic-like roles without requiring one-hot symbols.

### Result

**RG-53 — Causal abstraction is a principled bridge between distributed neural implementation and higher-level symbolic/compositional representation.**

---

# 55. Chain-of-thought text ≠ internal representation ground truth

External chain-of-thought is itself a public symbolic artifact produced by the model.

It can be:

- a genuine scratchpad used causally;
- a partial report;
- a post-hoc explanation;
- stylistic rationalization.

### Result

**RG-54 — Generated reasoning text and internal representational process are distinct objects; behavioral/internal evidence is required to infer their correspondence.**

---

# 56. Internal verbalizability ≠ semantic completeness

NLA/J-space-like methods can map some internal states to language, but not every internal variable must have a clean linguistic label.

### Result

**RG-55 — Human-language describability is not a constitutive condition of artificial representation.**

---

# 57. Representation explanations themselves have provenance

A feature label such as `Golden Gate Bridge` can be:

- produced by a human analyst;
- produced by an automated explainer model;
- inferred from activation examples;
- validated through interventions.

These are evidence sources, not the represented content itself.

### Result

**RG-56 — Interpretability labels require provenance and validation; explanatory text is an analyst-level representation of candidate model content.**

---

# 58. Human interpretability ≠ model usefulness

A feature can be essential to the model while difficult to summarize in natural language.

A beautifully labeled feature can be behaviorally irrelevant or redundant.

### Result

**RG-57 — Human semantic interpretability and endogenous computational importance are distinct axes.**

---

# 59. Completeness is as important as precision

Feature studies often highlight cases where a latent strongly activates and the concept is present.

But representational attribution should also test whether the concept occurs without that feature and whether alternative features substitute.

### Result

**RG-58 — Artificial feature attribution requires precision, recall/completeness and redundancy analysis, not only cherry-picked positive examples.**

---

# 60. Specificity under intervention matters

If steering/ablating a feature changes many unrelated behaviors, the feature may be:

- entangled;
- a broad control axis;
- off-manifold perturbation;
- upstream of many variables.

### Result

**RG-59 — Content-specific causal claims require intervention specificity, not merely large behavioral effect.**

---

# 61. Generalization under paraphrase/modal/context variation matters

A high-level artificial representation claim should survive variations declared irrelevant to content:

- wording;
- language;
- visual appearance;
- position;
- prompt template;
- task surface form.

### Result

**RG-60 — Nuisance-invariant generalization supports abstract artificial-content claims, but invariance must remain scope-typed.**

---

# 62. Counterexamples are more informative than activation exemplars

For candidate feature X, actively search for:

1. X-present / feature-inactive cases;
2. X-absent / feature-active cases;
3. correlated Y varied independently;
4. adversarial paraphrases;
5. causal feature intervention without X-like behavioral effect;
6. same behavior through alternative mechanisms.

### Result

**RG-61 — Artificial representation attribution should be falsification-first rather than exemplar-first.**

---

# 63. Artificial representation evidence profile

MF3-G extends MF3-F with artificial-specific dimensions.

## A — Association/selectivity

Does candidate state/feature correlate with X?

## I — Information/recoverability

Can X be decoded; by what class?

## U — Endogenous use

Do actual network consumers read/use it?

## C — Causal recruitment

Does naturalistic intervention produce predicted content-specific effects?

## G — Grounding/target determination

Why X rather than correlated X' or analyst label?

## E — Error/evaluability

Can the variable be wrong while retaining stable content?

## R — Robustness/scope

Does attribution survive nuisance/context changes within scope?

## D — Decoupling/model use

Does the state support absent/future/hypothetical target use?

## J — Gauge/identifiability

Is the candidate variable stable under reasonable basis/decomposition alternatives? What is method-defined?

## P — Provenance

Was content assigned by labels/design, inherited from public convention, learned through multimodal/sensorimotor interaction, or merely analyst-ascribed?

## M — Mechanistic integration

Does the candidate participate reproducibly in circuits/causal abstractions and cross-task consumers?

### Result

**RG-62 — Strong artificial representation claims require a multidimensional evidence profile rather than a probe score, SAE label or steering effect alone.**

---

# 64. Evidence profile is not a universal ladder

A conventional public symbol may have very strong provenance/reference but little internal decoupling.

A world-model latent may have strong decoupling/use but weak human interpretability.

A causal algorithmic variable may have strong mechanistic integration without public semantic labels.

### Result

**RG-63 — Artificial representation evidence dimensions converge differently by representation type; no universal scalar representation score is frozen.**

---

# 65. Strong artificial representation candidate

MF3-G proposes:

> **An artificial internal state/feature strongly represents X when its structured distinctions are systemically recruited as a grounded proxy for X (or an X-relative domain/possibility) in the model's own computation, with content-appropriate evaluability, and when this attribution survives contrastive alternatives, causal/mechanistic tests, reasonable reparameterization/decomposition challenges and declared scope/generalization tests.**

This excludes the shortcut:

`human-readable label = model content`.

---

# 66. ArtificialRepEpisode schema

```text
ArtificialRepEpisode = <
  V   : internal vehicle/state/direction/subspace/feature,
  L   : layer/component/circuit location,
  Z   : vehicle/code/geometry,
  X   : candidate target/domain,
  Φ   : proposed content,
  Ctx : input/task/context,
  U   : endogenous consumers/use,
  B   : grounding/provenance basis,
  C   : causal intervention profile,
  Dec : probe/decoder evidence,
  Mech: circuit/causal-abstraction evidence,
  J   : gauge/identifiability/decomposition status,
  E   : error/evaluation profile,
  R   : robustness/generalization scope,
  D   : decoupling/model-use profile,
  Int : analyst/explainer interpretation provenance
>
```

---

# 67. Artificial feature wording discipline

Instead of:

> `Feature 9123 represents deception.`

prefer staged claims:

- `Feature 9123 activates more strongly on dataset examples labeled deception.`
- `The label is robust across paraphrases/languages and contrastive non-deceptive cases.`
- `The feature is linearly/readout-accessible to downstream components.`
- `Feature intervention causally changes deception-related behavior with measured specificity.`
- `Circuit analysis shows feature participation in a reusable mechanism.`
- `Convergent evidence supports a scoped representation of deception-related state.`

### Result

**RG-64 — Evidence-typed wording is required to avoid converting interpretability hypotheses into semantic facts.**

---

# 68. SAE feature reconstruction under the MF3-G standard

A strong SAE feature claim should report:

- activation precision;
- recall/absorption failures;
- feature splitting across dictionary sizes;
- reconstruction error;
- dead features;
- causal steering/ablation;
- intervention specificity;
- downstream circuit use;
- robustness across data distributions;
- alternative decompositions.

### Result

**RG-65 — `Monosemantic SAE feature` is a graded empirical claim, not a guarantee conferred by sparse-autoencoder construction.**

---

# 69. Causal feature reconstruction

A candidate internal variable is substantially stronger when:

1. a controlled distinction X changes the candidate state;
2. the state generalizes across surface forms;
3. actual downstream mechanisms depend on it;
4. interchange/patching interventions transplant the X-dependent behavior;
5. alternative correlated interpretations fail;
6. the effect composes/reuses across tasks.

### Result

**RG-66 — Cross-context causal transplantability is among the strongest evidence for internal variable-like representation in artificial systems.**

---

# 70. Grounding reconstruction for text-only LMs

Text-only LMs are not simply `ungrounded` or `grounded` as a binary.

They receive derived/public grounding through text authored by agents whose words refer to the world.

They can also acquire:

- protocol/tool semantics;
- interaction feedback;
- user corrections;
- execution results;
- externally supplied images/sensor data in multimodal extensions.

What may be weaker than an embodied agent is direct sensorimotor/action-causal anchoring.

### Result

**RG-67 — Text-only artificial systems can possess derived/conventional semantic grounding; absence of embodiment does not imply semantic nullity, but grounding provenance differs from direct sensorimotor systems.**

---

# 71. Endogenous grounding can emerge through task structure

Within an artificial system, an internal variable can become systemically grounded when stable distinctions are repeatedly recruited to solve tasks and predict/interact with an external domain, even if the initial supervision was externally assigned.

### Result

**RG-68 — Derived supervision and endogenous use can coexist; grounding provenance can evolve through learning rather than belonging to one permanent category.**

---

# 72. External labels can become internalized without becoming identical to internal variables

Training can cause model states to organize around public categories.

But internal distinctions may be:

- finer;
- coarser;
- differently partitioned;
- context-conditioned;
- relationally transformed.

### Result

**RG-69 — Internalization of a public category does not require one-to-one identity between human category boundaries and model feature boundaries.**

---

# 73. `Concept` should be reserved for robust abstraction claims

MF3-G recommends using `concept feature` only when evidence demonstrates substantial invariance/generalization and systemic reuse beyond lexical/statistical correlations.

### Result

**RG-70 — `Concept` is a stronger abstraction claim than `feature`, `direction` or `detector` and should require correspondingly stronger evidence.**

---

# 74. Artificial misrepresentation is possible

A model state may represent:

- Paris as capital of France;
- object at location L;
- user intent;
- confidence/probability;

and be wrong.

The content must remain stable enough for error to be identified.

### Result

**RG-71 — Artificial representation theories must support error without redefining internal content to match every model output or activation.**

---

# 75. Hallucination output ≠ hallucinated internal representation by definition

A false output could arise from:

- wrong internal world state;
- correct internal state followed by faulty decoding;
- sampling noise;
- policy/instruction conflict;
- fabricated-answer strategy.

### Result

**RG-72 — Output error and internal representational error are separate failure loci.**

Circuit-level 2025 work showing cases of plausible rationalization despite internal intermediate structure makes this distinction particularly important.

---

# 76. Internal state report ≠ infallible introspection

A model may verbalize internal state through generated text or NLA-style methods.

Neither guarantees perfect access/faithfulness.

### Result

**RG-73 — Artificial self-report is evidence about internal representation only after independent causal/reconstruction validation.**

---

# 77. Representation can be transient and dynamically constructed

An artificial system need not store one persistent feature for every concept.

Representational states may be generated contextually as needed through network computation.

### Result

**RG-74 — Artificial content can be dynamically instantiated; persistent dedicated feature storage is not required.**

---

# 78. Representation can be distributed across time/depth

Transformer computation unfolds over layers and token positions.

A content-bearing process may be represented by a trajectory across states rather than one activation vector.

### Result

**RG-75 — Artificial representation vehicles include temporal/depth trajectories and circuits, not only instantaneous layer vectors.**

---

# 79. Representation can have multiple consumers

J-space-style evidence highlights an important architecture property: one internal variable can be read by many downstream computations.

### Result

**RG-76 — Multi-consumer broadcast/reuse strengthens the case for a general-purpose representation rather than a local intermediate.**

---

# 80. Representation can be consumer-local

Conversely, a state used only by one narrow downstream computation can still represent for that consumer.

### Result

**RG-77 — Global broadcast is not necessary for representation; consumer scope is part of the attribution.**

---

# 81. Artificial Representation Strength Profile

MF3-G proposes independent capabilities:

## AR0 — Correlational feature

Stable association/selectivity.

## AR1 — Recoverable feature

Information is decodable by a specified reader class.

## AR2 — Endogenously accessible variable

Actual model components use the distinction.

## AR3 — Causally manipulable variable

Naturalistic interventions produce content-specific changes.

## AR4 — Causal-abstraction variable

Interchange interventions validate a proposed high-level causal role.

## AR5 — Reusable grounded representation

The variable generalizes and is reused across contexts/consumers with stable target/content.

## AR6 — Model/symbolic/compositional representation

Supports decoupled surrogate operations or systematic role/binding/composition.

These are evidence/capability profiles, not a mandatory linear hierarchy.

### Result

**RG-78 — Artificial `representation` claims should specify strength/profile rather than relying on a binary label.**

---

# 82. Core rejected claims

MF3-G rejects as universal foundational claims:

- training label equals internal content;
- loss function directly supplies internal semantics;
- high activation equals concept representation;
- top-activating examples prove monosemanticity;
- neuron equals feature;
- superposition explains all polysemanticity;
- SAE latent equals true model feature;
- sparse dictionary is a unique canonical semantic basis;
- human-interpretable features are necessarily causally faithful;
- probe decodability proves endogenous use;
- amnesic-probe behavioral change uniquely determines content;
- steering vector equals concept vector;
- activation patching gives context-free component semantics;
- causal effect uniquely fixes semantic target;
- attribution graph is the complete causal graph of the original model;
- replacement-model feature identity equals original-model feature identity;
- natural-language explanation is literal ground-truth thought;
- reconstructable activation explanation is therefore semantically complete;
- multilingual/multimodal activation alone proves unique content;
- multimodal alignment equals full physical-world grounding;
- embodiment automatically grounds every hidden state;
- token embedding equals contextual concept;
- residual-stream coordinate is a semantic primitive;
- all concepts have one unique linear direction;
- all internal representations are linear;
- world-model latent equals physical latent cause;
- mechanistic importance equals representational status;
- symbolic I/O proves symbolic internal architecture;
- chain-of-thought is a transparent report of internal reasoning;
- fluent self-report proves introspective access;
- output hallucination proves one corresponding hallucinated internal variable;
- human interpretability equals computational importance;
- one successful intervention proves monosemantic semantic content.

---

# 83. Primary/original literature anchors

- Elhage, N. et al. (2022), `Toy Models of Superposition`, Transformer Circuits Thread. Constructive demonstration of superposition/polysemanticity in toy networks and motivation for overcomplete feature bases.
- Bricken, T. et al. (2023), `Towards Monosemanticity: Decomposing Language Models With Dictionary Learning`, Transformer Circuits Thread. Sparse autoencoder decomposition of transformer activations into interpretable features.
- Templeton, A. et al. (2024), `Scaling Monosemanticity: Extracting Interpretable Features from Claude 3 Sonnet`, Transformer Circuits Thread. Large-scale SAE extraction; abstract multilingual/multimodal features and steering, with explicit completeness/reconstruction limitations.
- Chanin, D. et al. (2024), `A is for Absorption: Studying Feature Splitting and Absorption in Sparse Autoencoders`, arXiv:2409.14507. Identifies feature splitting/absorption and shows apparent monosemanticity can hide false negatives.
- Mueller, A. et al. (2025), `MIB: A Mechanistic Interpretability Benchmark`, arXiv:2504.13151. Benchmarks circuit and causal-variable localization; reports supervised DAS strongest for causal-variable localization and SAEs not outperforming neurons in the evaluated setting.
- Ma, G. et al. (2026), `Do Sparse Autoencoders Identify Reasoning Features in Language Models?`, arXiv:2601.05679. Falsification-oriented tests find many candidate reasoning features track lexical artifacts rather than reasoning computations in studied models/settings.
- Hewitt, J. & Liang, P. (2019), `Designing and Interpreting Probes with Control Tasks`, EMNLP-IJCNLP. Probe capacity/selectivity controls.
- Elazar, Y. et al. (2021), `Amnesic Probing: Behavioral Explanation with Amnesic Counterfactuals`, TACL 9:160–175. Conventional probing does not establish behavioral importance; intervention-based information removal probes use.
- Meng, K., Bau, D., Andonian, A. & Belinkov, Y. (2022), `Locating and Editing Factual Associations in GPT`, NeurIPS/arXiv:2202.05262. Causal tracing plus ROME editing of factual associations.
- Geiger, A., Lu, H., Icard, T. & Potts, C. (2021/2024), `Causal Abstractions of Neural Networks`, arXiv:2106.02997. Aligns neural states with high-level causal variables and validates with interchange interventions.
- Turner, A. M. et al. (2023), `Steering Language Models With Activation Engineering`, arXiv:2308.10248. Activation Addition shows causal behavioral control using activation-space directions.
- Zhang, F. & Nanda, N. (2023), `Towards Best Practices of Activation Patching in Language Models: Metrics and Methods`, arXiv:2309.16042. Demonstrates localization sensitivity to patching metrics/corruptions.
- Ameisen, E. et al. (2025), `Circuit Tracing: Revealing Computational Graphs in Language Models`, Transformer Circuits Thread. Cross-layer-transcoder replacement model and attribution graphs; explicitly partial/method-limited mechanistic surrogate.
- Anthropic Interpretability Team (2025), `On the Biology of a Large Language Model`. Frontier-model attribution-graph analyses with perturbation validation; treats features as evolving/fuzzy interpretability units.
- Anthropic (2026), `Natural Language Autoencoders: Turning Claude's thoughts into text`. Learns activation→language→activation round-trip descriptions; establishes a new external surrogate code for hidden states and reports limitations.
- Anthropic (2026), `A global workspace in language models`. Jacobian-lens/J-space results including cross-task substitution/reuse and broad connectivity; strongest current case of reusable internal variable-like representation, while method limitations remain.
- Anthropic (2026), `Emotion concepts and their function in a large language model`. Identifies emotion-related activation patterns with causal behavioral effects without claiming phenomenal emotion.
- Anthropic (2026), `The assistant axis: situating and stabilizing the character of large language models`. Persona-space direction with causal steering effects across models.
- Radford, A. et al. (2021), `Learning Transferable Visual Models From Natural Language Supervision`, arXiv:2103.00020. CLIP image–language contrastive alignment and zero-shot transfer.
- Driess, D. et al. (2023), `PaLM-E: An Embodied Multimodal Language Model`, arXiv:2303.03378. Integrates continuous sensor modalities and language in embodied tasks.
- Brohan, A. et al. (2023), `RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control`, arXiv:2307.15818. Vision-language-action co-training with robot actions as tokens and closed-loop robotic control.

---

# 84. MF3-G reconstruction

The naive artificial-representation picture is:

```text
Human concept X
     ↓ labels/prompts
Model activation correlates with X
     ↓ probe / SAE / visualization
Interpretable feature labeled X
     ↓ steering
Output behavior changes
     ↓
Therefore model internally represents X
```

MF3-G replaces it with:

```text
External/public/task distinction X
           │
           ├─ training/design/conventional grounding
           ├─ multimodal/sensorimotor coupling
           ▼
Raw model vehicle/state V
           │
           ├─ activation/selectivity
           ├─ information/probe accessibility
           ├─ geometry/gauge
           ├─ actual network consumers
           ├─ causal circuit participation
           ├─ decoupled/model use
           └─ error/evaluation structure
           │
   ┌───────┴────────┐
   │                │
Analyst model       Original model
probe/SAE/NLA/      computation
transcoder/etc.          │
   │                     │
interpretation           │
   └──── evidence convergence ────┐
                                  ▼
                   scoped representational attribution
```

The crucial new truth boundary is:

`Model representation ≠ Interpretability model's representation of model representation.`

---

# 85. Deep synthesis

Artificial systems confirm nearly every MF3 distinction and make several of them sharper.

## 85.1 Observability does not solve semantics

Even when every float is visible, content remains a relation requiring target determination, systemic use and evaluability.

## 85.2 Intervention does not solve semantics

The ability to change behavior by editing an activation proves causal leverage, not uniquely what the edited state means.

## 85.3 Interpretability methods create new representational layers

Probes, sparse autoencoders, transcoders, attribution graphs and natural-language autoencoders are themselves models/representations of the original network.

Their variables can be useful without being identical to the network's native computational variables.

## 85.4 Artificial systems permit unusually strong positive evidence

Interchange interventions, causal abstraction, targeted edits, cross-task substitution and multi-consumer reuse can demonstrate internal proxy variables much more strongly than ordinary probing.

## 85.5 Grounding is typed and hybrid

Text models can inherit conventional/derived grounding; multimodal models add cross-modal grounding; embodied agents add action-causal sensorimotor grounding; tool/API interaction adds designed operational reference.

None of these individually makes all internal states semantically transparent.

## 85.6 Symbolic and neural remain level-relative

Tokens are formal symbols, but internal symbolic structure requires role/binding/composition evidence. Distributed causal variables can implement symbolic roles.

---

# 86. Core MF3-G non-collapses

`Training Objective ≠ Internal Content.`

`Activation Selectivity ≠ Representation.`

`Probe Decodability ≠ Endogenous Use.`

`SAE Feature ≠ Native Model Feature.`

`Human Interpretability ≠ Causal Faithfulness.`

`Steering Direction ≠ Concept Vector.`

`Activation Patching ≠ Unique Semantics.`

`Causal Efficacy ≠ Semantic Target Determination.`

`Replacement Model ≠ Original Model.`

`Attribution Graph ≠ Complete Computation.`

`Text Explanation ≠ Ground-Truth Thought.`

`Token ≠ Embedding ≠ Contextual State ≠ Concept.`

`Multimodal Alignment ≠ Full World Grounding.`

`World-Model Latent ≠ Physical Latent Cause.`

`Mechanistic Variable ≠ Representation by Definition.`

`Symbolic I/O ≠ Symbolic Internal Architecture.`

---

# 87. MF3-H handoff — External / Public Representation

MF3-A–G have focused heavily on systemic/internal representation.

MF3-H must now attack the other extreme: representations that remain public/external and can represent even when no current user is actively consuming them.

Questions:

- Can a road sign, map, book, file or inscription represent while nobody reads it?
- Is actual consumer recruitment necessary, or can established convention/design disposition suffice?
- What distinguishes artifact inscription from symbolic token/type?
- How do public conventions stabilize meaning across users/time?
- What is authorship/intention's role?
- Can accidental marks become representations?
- How do copied/generated artifacts inherit provenance/reference?
- How do metadata, filenames, schemas, standards and protocols represent?
- How should database records/API payloads be analyzed?
- How do external memory, notation, writing and diagrams extend cognition without becoming internal neural representation?
- How do public representations persist through storage/serialization/format migration?
- How do provenance, authenticity, quotation, forgery and versioning affect representational status without changing raw content?
- How do media artifacts combine iconic/indexical/symbolic/structural modes?
- What is the relation between medium and representation now that MF0–MF3 are separated?

This is **MF3-H — External / Public Representation**.

---

# Final MF3-G handoff

MF3-G establishes an exacting but non-skeptical position.

Artificial systems **do** contain strong representations. Current causal-abstraction, cross-task reuse, intervention and circuit evidence can be far stronger than simple decoding.

But the representation claim must not be outsourced to the interpretability method.

> **A probe finds a readable relation. An SAE proposes a sparse explanatory basis. A steering vector supplies causal leverage. A patching experiment localizes a counterfactual contribution. A transcoder supplies a replacement model. An NLA supplies a linguistic surrogate. None of these alone is the model's semantic ontology.**

The strongest attribution comes from convergence:

`Grounding + Endogenous Use + Causal/Mechanistic Integration + Contrastive Target Determination + Error/Evaluation + Robustness + Gauge Awareness + Reuse`.

The next round leaves internal computation and asks how representation exists in the public world at all.

**Next: MF3-H — External / Public Representation.**
