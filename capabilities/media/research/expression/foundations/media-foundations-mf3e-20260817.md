# Ordivon Media Foundations — MF3-E Symbols, Reference & Compositionality

**Date:** 2026-08-17  
**Continuity Task:** `task:media-foundations-mf2h-20260817` revision 8 at start  
**Input:** MF0 Media Ontology frozen; MF1 Signal Foundations v1 frozen; MF2 Perception Foundations v1 frozen; MF3-A/B/C/D complete and provisional.  
**Status:** MF3-E complete as a provisional Representation round; Representation Foundations remain UNFROZEN.  
**Next:** MF3-F — Neural & Biological Representation.

---

# 1. Problem statement

MF3-A–D established that representation is not signal, perception, geometry, correlation, model resemblance or prediction success. A grounded representational relation can use many vehicle formats.

MF3-E asks what is distinctive about **symbolic** representation.

The hard questions are:

- What makes a vehicle a symbol rather than merely a signal or representation?
- What is the relation among token, type, expression, syntax, content and reference?
- Must symbols be arbitrary or conventional?
- Must symbols have referents?
- How do names, variables, pointers and indexicals differ?
- What is compositionality, and is it required for every symbol?
- Are productivity and systematicity definitions of symbolhood or capabilities of some symbolic systems?
- Does variable binding require local/discrete symbolic units?
- Can distributed/vector systems realize symbolic structure?
- Is an LLM tokenizer token a symbol in the semantic sense?
- What exactly is the symbol-grounding problem after MF3-B's grounding-provenance reconstruction?

The main result is a separation between **formal symbolhood**, **referential/semantic grounding**, and **compositional symbolic organization**.

---

# 2. Symbol ≠ representation

Every symbol used representationally is a representation vehicle or part of one, but not every representation is symbolic.

Examples of plausibly non-symbolic representations include:

- analogue gauge position;
- image projection;
- continuous probability field;
- distributed perceptual estimate;
- topographic neural map;
- latent trajectory state.

Symbols add a special organizational property:

> **tokens are recognized/recruited as instances of re-identifiable types/roles whose identity is sufficiently stable across physical variation to support type-governed substitution, combination, copying, storage or manipulation.**

This does not yet guarantee semantic content.

### Result

**RE-01 — Symbolhood is a vehicle/format role layered on top of representation; representation is broader than symbolic representation.**

---

# 3. Token and type

Newell & Simon's physical-symbol-system formulation usefully separates symbol patterns from symbol tokens occurring inside larger expressions.

MF3-E generalizes this distinction.

## Symbol token

A particular physical/computational occurrence:

- this printed `cat`;
- this UTF-8 byte sequence at a location;
- this token ID occurrence in a model input;
- this spoken occurrence;
- this memory cell content;
- this neural/robotic marker event if the system treats it symbolically.

## Symbol type

A system/practice-defined equivalence class or re-identification rule under which different tokens count as instances of the same symbolic kind.

Token physical identity can vary while type identity remains stable:

- fonts;
- handwriting;
- acoustic realizations;
- file encodings;
- device implementations.

The type need not be a metaphysically abstract object for MF3. What matters is a stable classification/recruitment relation.

### Result

**RE-02 — Symbol token ≠ symbol type. Symbolic operations generally presuppose some token re-identification/equivalence discipline.**

---

# 4. Formal symbolhood vs semantic symbolhood

This is the most important distinction in MF3-E.

## Formal symbol

A typed token/structure that can participate in system-defined operations according to its form/type/position.

Examples:

- parser tokens;
- variable names in syntax;
- machine opcodes;
- chess notation tokens;
- BPE subword IDs;
- symbols in a formal proof calculus.

A formal system can manipulate such symbols without thereby establishing what they mean outside the formal system.

## Semantic/referential symbol

A formal symbolic vehicle/expression that also participates in a grounded representational relation under MF3-A/B:

- it has content/reference/domain through systemic, designed, conventional or hybrid grounding;
- its symbolic role is recruited as a proxy;
- it has an evaluation/use profile.

Harnad's symbol-grounding problem is precisely the gap between these levels: formal tokens whose interpretation is supplied only from outside do not acquire intrinsic/systemic semantics merely by being shuffled according to syntax.

### Result

**RE-03 — Formal symbolhood ≠ semantic grounding. Syntax/manipulability can exist without independently grounded reference/content.**

---

# 5. Newell–Simon designation: retained but narrowed

Newell & Simon define a physical symbol system through physical symbol patterns, expressions and processes; their notions of **designation** and **interpretation** are especially relevant.

Their designation idea is operational: an expression designates an object when the system can, given that expression, access/affect the object or behave in ways dependent on it. Interpretation is a special case where an expression designates a process the system can execute.

MF3-E retains the useful operational lesson:

> symbol reference should matter to system behavior/use, not merely to an external annotator.

But MF3 does **not** adopt the Physical Symbol System Hypothesis that physical symbol systems are necessary and sufficient for general intelligence. That is an empirical architecture/intelligence hypothesis, not a representation ontology theorem.

Nor does designation alone solve MF3-B content grounding: a state may guide access to a correlated object without uniquely fixing content.

### Result

**RE-04 — Operational designation is strong evidence of systemic symbolic recruitment, but it must be combined with MF3 grounding/contrastive constraints.**

---

# 6. Arbitrariness is not a binary criterion for symbolhood

A common slogan says symbols are arbitrary while icons resemble and indices are causally connected.

The strong form fails.

A symbol vehicle can be:

- historically conventional but physically motivated;
- partly iconic and partly conventional;
- derived from an older pictorial sign;
- chosen because it is easy to discriminate;
- constrained by morphology/phonology;
- conventional in one relation but structurally motivated in another.

Examples:

- a restroom pictogram is iconic in shape and conventional in public use;
- an arrow can have diagrammatic/spatial motivation yet participate in formal notation;
- mathematical notation often contains conventional symbols with structural regularities;
- road signs can combine color conventions, text, icons and geometric layout.

The important symbolic property is not maximal arbitrariness but **type-governed stand-in use that does not require token-by-token physical resemblance to determine content**.

### Result

**RE-05 — Arbitrary physical shape is neither necessary nor sufficient for symbolic representation.**

---

# 7. Icon, index and symbol are modes, not exclusive natural kinds

Peircean-style icon/index/symbol distinctions remain useful descriptive dimensions:

- **iconic mode:** representational relation exploits selected resemblance/structural correspondence;
- **indexical mode:** token/reference depends on contextual/causal/spatiotemporal coupling;
- **symbolic mode:** token is interpreted/recruited through a type/rule/convention/systemic code that can generalize across token occurrences.

But real representations frequently combine these modes.

A map symbol may be conventional, topologically structural and indexically anchored to current position at once.

### Result

**RE-06 — Iconic, indexical and symbolic relations can coexist in one representation; MF3 does not freeze them as mutually exclusive object classes.**

---

# 8. Reference ≠ content

MF3-B already distinguished domain, content and actual referent. MF3-E applies this directly to symbols.

A symbol/expression may:

- refer to an individual;
- denote a class/property;
- express a relation;
- function as a variable;
- specify a command;
- contribute to a proposition without independently referring;
- have meaningful content while lacking an actual referent.

Therefore:

`symbolic content ≠ individual reference`.

### Result

**RE-07 — Reference/denotation is one semantic relation among several; not every meaningful symbol has or needs an individual referent.**

---

# 9. Type meaning/reference and token reference must be separated

The same symbol type can produce different token referents.

Kaplan's indexicals are the canonical case.

The linguistic rule/`character` associated with expressions such as `I`, `here` and `now` does not supply one context-independent referent. Instead it provides a rule mapping context to token content/reference.

Thus:

```text
Symbol type / character
        +
Context c
        ↓
Token content / referent
```

Two tokens of `I` uttered by different speakers are tokens of the same expression type but refer to different individuals.

Conversely, different symbol types can co-refer to the same entity.

### Result

**RE-08 — Symbol-type identity does not imply reference identity; reference can be token- and context-dependent.**

---

# 10. Indexicality and deixis

MF3-E distinguishes:

## Pure indexical-like rule

Reference can be determined by a context-sensitive rule using parameters such as speaker, place or time.

## Demonstrative/deictic rule

Reference additionally depends on a demonstration, attentional target, pointing/action cue or other contextual selection relation.

The important ontology result is broader than linguistic indexicals:

> some symbolic references are **context-completable** rather than encoded as fixed target identities in the symbol type.

Robotic `this object`, UI selection handles, cursor focus, pronouns and event references can all exhibit analogous context dependence.

### Result

**RE-09 — Context is sometimes constitutive of token reference, not merely extra metadata attached after semantic interpretation.**

---

# 11. Empty/nonexistent reference

A symbolic expression can remain meaningful even when no actual token referent exists.

Examples:

- `unicorn`;
- fictional names;
- a variable whose current query returns no object;
- a failed database identifier lookup;
- a prediction referring to an event that never occurs.

MF3-B already supplied the architecture:

`Domain + Content condition ≠ actual referent`.

MF3-E adds:

> symbolic reference systems must distinguish **reference rule/content** from **successful referent resolution**.

### Result

**RE-10 — Successful reference resolution is not necessary for a symbol/expression to possess content or a reference rule.**

---

# 12. Name ≠ variable ≠ identifier ≠ pointer

These are commonly collapsed under the word `reference`.

## Name

A symbolic expression whose use may be anchored historically/conventionally to an entity/type/domain.

## Variable

A typed/role-bearing placeholder whose denotation depends on a binding/assignment environment.

`x` does not usually have one fixed referent; its value is supplied by binding context.

## Identifier

A token used to discriminate/reidentify an entity within a namespace/system.

An identifier can be unique without carrying descriptive semantic content.

## Pointer/address/handle

An operational designator that grants access to a resource/object/location under a machine/runtime relation.

A pointer's referent can change across processes/runs; identical numeric addresses need not designate the same object in different address spaces.

## Semantic reference

The broader representational relation under which a symbol/expression stands for a target/domain entity or condition.

### Result

**RE-11 — Name, variable, identifier, pointer/handle and semantic reference are distinct symbolic roles even when one implementation uses the same string/token for several of them.**

---

# 13. Syntax ≠ semantics

## Syntax

Rules/relations governing well-formed symbolic structures and operations on them based on type/form/position.

## Semantics

Grounded content/reference/evaluation relations connecting symbolic structures to represented domains or practices.

A formal calculus can have rich syntax before an external interpretation is assigned.

A system can also possess semantic distinctions in a non-symbolic representation.

Therefore:

**RE-12 — Syntax is neither semantics nor required for all representation; semantics is not reducible to formal token manipulation.**

This is the core of Harnad's challenge to purely formal symbol systems.

---

# 14. Grounding graph, not every-symbol direct grounding

Harnad's proposed solution grounds elementary symbols through nonsymbolic iconic/categorical representations and builds higher-order symbolic descriptions from grounded primitives.

MF3-E accepts the important anti-circularity insight but rejects a universal requirement that every symbol individually connect directly to a sensorimotor category.

External/public symbols can acquire derived semantics from:

- users/practices;
- design specifications;
- institutions;
- established reference chains;
- interfaces to already-grounded systems.

Within a symbolic system, many symbols can inherit grounding compositionally/inferentially from a smaller grounded base.

The unacceptable case is an indefinitely closed network of uninterpreted tokens where every `meaning` is only another equally ungrounded token relation.

### Reconstruction

> **Symbol grounding is graph-like: semantic dependencies may pass through other symbols, but a semantic claim requires eventual anchoring in independently grounded systemic, designed, conventional or public representational relations.**

### Result

**RE-13 — Grounding need not be direct per symbol, but purely uninterpreted symbol-to-symbol closure cannot by itself create semantic grounding.**

---

# 15. Compositionality — minimal reconstruction

Strong compositionality is often stated as:

> the meaning/content of a complex expression is determined by the meanings/contents of its constituents and their mode of combination.

MF3-E refines this into a typed relation:

```text
C_whole = Φ_comp(
  C_part1,
  C_part2,
  ...,
  structural roles / mode of combination,
  context parameters allowed by the system
)
```

The critical component is **reusable constituent contribution under structured combination**, not literal concatenation.

### Result

**RE-14 — Compositionality is systematic content construction from reusable constituent/role contributions under a composition rule; it is not merely physical juxtaposition of tokens.**

---

# 16. Compositionality is not required for every symbol

An atomic label, name or alarm symbol can function symbolically without being internally compositional.

Therefore:

`symbolhood ≠ compositionality`.

Compositionality becomes crucial for symbol **systems** that need open-ended structured expression.

### Result

**RE-15 — Atomic symbols can be noncompositional; compositionality is a capability/format property of structured symbol systems, not a necessary property of every symbol token/type.**

---

# 17. Compositionality need not be perfectly context-free

Natural and artificial symbolic systems can contain:

- idioms;
- overloaded operators;
- context-sensitive names;
- type-dependent interpretations;
- indexicals;
- coercions;
- default rules;
- pragmatic enrichment.

Thus a naive formula where whole content is fixed only by context-free lexical meanings is too strong.

The more general condition is:

> the system exposes **stable reusable contribution rules** for some constituent distinctions under specified composition/context parameters.

### Result

**RE-16 — Compositionality is typed and context-bounded; a system can be partially compositional without every expression obeying one context-free semantic algebra.**

---

# 18. Productivity ≠ compositionality

## Productivity

Ability to construct/interpret a very large or potentially unbounded family of novel expressions from finite reusable resources/rules.

## Compositionality

Content of complex expressions is systematically related to constituent content and combination structure.

A finite but compositional language can lack practical unbounded productivity.

A generative system can produce an enormous space of outputs without having strongly compositional semantics.

### Result

**RE-17 — Productivity and compositionality are distinct; compositional structure is one powerful route to productivity, not an identity.**

---

# 19. Systematicity ≠ compositionality

Fodor & Pylyshyn use **systematicity** to point to linked cognitive capacities: e.g. a system capable of representing/understanding `John loves Mary` should, under the same constituent repertoire, exhibit corresponding capacity for related recombinations such as `Mary loves John`.

This motivates combinatorial constituent structure.

But systematicity is a **capacity pattern**, whereas compositionality is a property of representational organization/interpretation.

A system can possess some compositional encoding yet generalize poorly to unseen combinations because learning/training/use fails to exploit the structure robustly.

Lake & Baroni's SCAN results provide a clean artificial example: recurrent sequence models can perform well in nearby regimes but fail badly when tested on systematic novel recombinations.

### Result

**RE-18 — Systematicity is a generalization/capability signature associated with reusable compositional structure, not identical to compositionality itself.**

---

# 20. Fodor–Pylyshyn challenge retained, architecture conclusion rejected

Fodor & Pylyshyn's strongest enduring contribution for MF3 is the challenge:

> a theory of representation should explain why certain representational capacities come in systematic families rather than as arbitrary unrelated abilities.

Their preferred explanation is classical combinatorial syntax/semantics.

MF3-E retains the explanatory challenge but does not freeze the conclusion that the physical/cognitive implementation must be classical/localist symbolic architecture.

Why?

Because distributed systems can implement explicit compositional structures.

### Result

**RE-19 — Systematicity remains an important falsification criterion for compositional-representation theories, but it does not by itself determine the physical implementation architecture.**

---

# 21. Variable binding is the crucial structural operation

Compositional systems need to preserve not only which constituents exist, but **which constituent fills which role**.

For example:

`LOVES(John, Mary)`

and

`LOVES(Mary, John)`

contain the same fillers but differ in binding.

A bag/multiset of constituent activations cannot distinguish them.

MF3-E therefore identifies **role–filler binding** as a core compositional operation.

Possible implementations include:

- positional token slots;
- tree nodes;
- pointers/links;
- variable environments;
- synchrony/temporal relations;
- tensor products;
- vector symbolic bindings;
- attention-mediated dynamic relations;
- recurrent state structures.

### Result

**RE-20 — Constituent presence is insufficient for compositional structure; role–filler binding or an equivalent relation is required wherever relational order/role changes content.**

---

# 22. Variable ≠ filler

A variable is a reusable role/place whose value/reference can change under a binding environment.

A filler is the bound content/entity/value for a particular instance.

Thus:

`Variable/Role identity ≠ Filler identity`.

This allows structural reuse:

```text
LOVES(agent=x, patient=y)
```

with many bindings.

### Result

**RE-21 — Variable/role identity and filler/value identity are separate dimensions of symbolic compositional structure.**

---

# 23. Smolensky falsifies localist-symbolic necessity

Smolensky's tensor-product representation gives a direct constructive counterexample to the claim that role/filler structure requires one local discrete symbol unit per constituent.

A binding can be represented as a tensor product:

`r ⊗ f`

and a structure as a sum/composition of such bindings:

`S = Σ_i r_i ⊗ f_i`.

Roles and fillers themselves can be distributed vectors. Complex symbolic structures can be recursively constructed while preserving role–filler distinctions.

### Result

**RE-22 — Symbolic/compositional role structure can be implemented by fully distributed vehicles. Localist physical symbols are not ontologically necessary for symbolic computation.**

This is a major bridge between MF3-C geometry and MF3-E symbolic structure.

---

# 24. Distributed implementation does not automatically become symbolic

The reverse inference also fails.

A vector space does not become symbolic merely because an analyst can decompose it into candidate role/filler vectors.

MF3-A/B/C still require:

- systemic recruitment;
- grounding;
- stable role distinctions;
- actual operations exploiting binding/composition;
- intervention/counterfactual evidence where appropriate.

### Result

**RE-23 — Distributed realization can implement symbolic structure, but analyst-decomposability alone does not establish that the system uses a symbolic/compositional code.**

---

# 25. Symbolic format is an operational profile

After MF3-C/E, a symbolic format is best characterized not by physical discreteness alone but by a capability profile involving some combination of:

- re-identifiable types;
- token substitution under type rules;
- stable constituent identity across contexts;
- explicit/usable relational roles;
- binding/unbinding;
- composition/decomposition;
- copying/reuse;
- variable instantiation;
- reference reassignment under context/binding;
- type-sensitive operations;
- recursive/nested structure;
- interpretation/execution of designated processes.

Not every symbolic system needs all features.

### Result

**RE-24 — Symbolic representation is a typed operational format profile, not a claim about one privileged physical substrate.**

---

# 26. Formal syntax can be semantically neutral

Consider a proof checker over uninterpreted symbols.

It can:

- parse expressions;
- bind variables;
- substitute terms;
- apply rewrite rules;
- prove syntactic theorems.

The same formal structure may admit multiple external interpretations/models.

Therefore sophisticated compositional syntax does not by itself determine world reference.

### Result

**RE-25 — Compositional formal structure can be semantically underdetermined; syntax does not uniquely ground interpretation.**

This directly connects MF3-E back to MF3-D's key/interpretation problem.

---

# 27. Reference can be inherited compositionally

A complex expression can refer/denote through the structured contribution of components even if not every component independently names an object.

For example, predicates, quantifiers, operators and relation symbols contribute to the whole's evaluation/reference conditions differently from proper names.

Thus a symbolic system needs **typed semantic roles**, not a one-token-one-referent ontology.

### Result

**RE-26 — Compositional reference/content is role-sensitive; constituents can contribute functions, constraints, relations or binders rather than individual referents.**

---

# 28. Symbol identity and semantic identity are separable

The same formal symbol type may receive different semantics under different interpreters/namespaces/languages.

Conversely, different symbol types can share semantic content/reference.

Examples:

- `+` overloaded across integers, matrices, strings;
- `x` bound differently in different scopes;
- multiple aliases for one file/object;
- multilingual labels for one entity.

### Result

**RE-27 — Formal symbol-type identity ≠ semantic identity; semantic equivalence ≠ token/type identity.**

---

# 29. Namespace and scope are semantic infrastructure

Identifiers and variables cannot be interpreted independently of environments that determine:

- namespace;
- lexical scope;
- module;
- process/address space;
- database/table;
- conversation/context;
- temporal validity.

Therefore symbolic reference is frequently a relation of the form:

`Ref(token, environment, context) -> target/value`.

### Result

**RE-28 — Namespace/scope/context are first-class parts of many symbolic reference systems, not incidental implementation metadata.**

---

# 30. Symbol grounding provenance

MF3-B's grounding provenance becomes especially important for symbols.

## Systemic/endogenous symbolic grounding

The system's own perception/action/model dynamics establish and use the reference/content relation.

## Derived/designed symbolic grounding

Engineers specify that a token/field/code denotes a target, and the system uses it accordingly.

## Conventional/public grounding

A social practice stabilizes type, syntax and reference rules.

## Analyst-ascribed symbolic interpretation

An external observer maps system states to symbols for explanation, without evidence that the system itself uses those symbolic distinctions.

### Result

**RE-29 — Symbolic attribution must state grounding provenance; public/derived symbols and endogenous symbolic representations are not the same claim.**

---

# 31. LLM/subword tokens — what exactly is symbolic?

Modern language models give a high-value boundary case.

Sennrich et al. introduced BPE-based subword units to represent open-vocabulary text as sequences from a fixed discrete vocabulary. Transformer-style architectures then map discrete input/output symbols/tokens to continuous embeddings and contextualize them through attention-based computation.

This gives multiple distinct levels:

## Tokenizer level

A token ID is a **formal symbol/code element** in a discrete vocabulary.

Its identity is stable enough for parsing, lookup, copying and output decoding.

## Lexical/public language level

Some token strings inherit conventional linguistic content from human language, but many subword tokens are fragments whose standalone semantic content is weak, context-dependent or absent.

## Internal contextual representation level

The same token type produces different hidden/contextual states depending on neighboring tokens and model state.

These continuous states may carry rich content but are not thereby token-identical with the tokenizer symbol.

### Result

**RE-30 — An LLM token is clearly a formal symbol/code element at the tokenizer/interface level; whether it is a grounded semantic symbol is a separate provenance/content question.**

---

# 32. Token ID ≠ word ≠ concept

Subword tokenization is designed partly for computational/statistical vocabulary coverage, not to align one token with one semantic concept.

A word can map to:

- one token;
- several subword tokens;
- different segmentations under different tokenizers.

A token can appear in many words/contexts.

Therefore:

**RE-31 — Token vocabulary boundaries are code/segmentation boundaries, not an ontology of concepts or meanings.**

This is the language-model version of MF3-C's `dimension ≠ semantic factor`.

---

# 33. LLM symbolic capability must be tested at the operation level

The fact that a model consumes and emits formal token sequences does not establish that its internal computation is a classical symbolic architecture.

Relevant tests concern whether it realizes stable reusable relations such as:

- constituent identity;
- role/filler binding;
- variable-like reuse;
- systematic recombination;
- compositional content preservation;
- context-sensitive reference;
- execution of symbolically specified operations.

Transformer hidden states are continuous/distributed; symbolic organization, if present, may be emergent/implemented in distributed dynamics rather than one-token-one-symbol internal storage.

### Result

**RE-32 — Symbolic I/O does not determine internal symbolic architecture; symbolic internal attribution requires evidence about role/binding/composition operations.**

MF3-G will attack this empirically for artificial representations.

---

# 34. Compositional generalization is an empirical test, not a definition

SCAN and related benchmarks show a model can memorize/learn many input-output mappings yet fail systematically when familiar primitives must be recombined in novel ways.

Thus nominal compositional syntax in the data does not imply the learned internal representation actually supports compositional generalization.

At the same time, benchmark failure/success depends on split design, architecture and task assumptions; no one benchmark establishes a universal cognitive ontology.

### Result

**RE-33 — Compositional generalization tests whether a system functionally exploits reusable composition rules; it is evidence about symbolic/compositional capability, not a one-shot definition of symbolhood.**

---

# 35. Symbolic and subsymbolic are not mutually exclusive implementation classes

MF3-C/E now dissolve a common false dichotomy.

A system can have:

- discrete symbolic interfaces;
- distributed internal states;
- continuous binding operations;
- symbolic role structure realized in vectors;
- non-symbolic perceptual front ends feeding symbolic planners;
- symbolic tokens grounded through continuous sensorimotor models.

Therefore `symbolic vs neural` is usually ill-typed unless a level is specified.

### Result

**RE-34 — Symbolic/subsymbolic classification is level- and relation-dependent; a single system can be symbolic at one organizational level and distributed/continuous at another.**

---

# 36. Symbolic compositionality can be explicit or implicit

## Explicit symbolic structure

The system exposes constituent identities/roles directly:

- AST nodes;
- logical terms;
- variable environments;
- database relations;
- graph edges.

## Implicit/distributed symbolic realization

The system has stable role/binding/composition dynamics but no one local token/slot corresponds transparently to each constituent.

Smolensky-style TPR is the canonical constructive example.

### Result

**RE-35 — Explicit addressability is not required for symbolic role structure, but explicitness is a separate operational property with implications for inspectability/intervention.**

---

# 37. Variable binding enables content-preserving substitution

A strong symbolic system can often substitute a filler while preserving role structure:

`LOVES(John,Mary)`

→ replace agent filler →

`LOVES(Alice,Mary)`.

This operation preserves relational form while altering one content component.

This gives a useful operational test:

> can a system independently manipulate/rebind constituent roles while preserving the relevant structural relation?

### Result

**RE-36 — Rebinding/substitution under preserved role structure is strong evidence of compositional symbolic organization.**

---

# 38. Symbolic recursion is not universally required

Some symbol systems have finite-depth syntax or fixed-arity structures.

Recursive closure is extremely powerful for productivity and hierarchical composition, but it is not required for every symbol or every symbolic system.

### Result

**RE-37 — Recursion is a powerful symbolic-system capability, not a constitutive condition of symbolhood.**

---

# 39. Symbolic exactness is not guaranteed

Symbolic systems are often associated with exact/discrete semantics, but symbols can support:

- vague predicates;
- probabilistic interpretations;
- fuzzy categories;
- ambiguous names;
- context-sensitive meanings;
- defeasible rules.

Discrete token identity therefore does not imply discrete/precise semantic content.

### Result

**RE-38 — Discrete symbol types can carry uncertain, graded, vague or context-dependent content; vehicle discreteness ≠ semantic discreteness.**

---

# 40. Symbol/reference failure taxonomy

MF3-E adds symbol-specific failure modes.

## Token recognition error

Physical token is classified as wrong symbol type.

## Type/code error

Wrong token type emitted/selected.

## Binding error

Correct fillers but wrong roles/variable assignments.

## Scope/namespace error

Correct identifier interpreted in wrong environment.

## Reference-resolution failure

Symbol has a valid reference rule but no matching referent in current context.

## Misreference

A token refers to the wrong entity while remaining a valid symbolic token.

## Composition error

Constituent contents/roles are combined under the wrong structure/operator.

## Semantic misrepresentation

The resulting grounded content fails its evaluation profile.

## Syntax error

Expression fails the formal composition rules and may have no valid semantic interpretation in the system.

### Result

**RE-39 — Symbolic failure must distinguish token/type, binding, scope, reference, composition, semantic and syntax failures.**

---

# 41. Revised symbol schema

MF3-E proposes:

```text
SymbolEpisode = <
  τ   : token occurrence / vehicle,
  Θ   : symbol type / type-reidentification rule,
  X   : containing expression / symbolic structure,
  Syn : syntactic/structural role,
  Bind: binding / assignment / namespace/context relation,
  D   : semantic target/domain,
  Φ   : content contribution,
  Ref : token-level reference/denotation rule/result (optional),
  U   : symbolic recruitment/use,
  B   : grounding basis/provenance,
  Comp: composition rule/environment,
  E   : evaluation profile,
  H   : history/context,
  S   : system/practice/consumer
>
```

Not every field is required for every atomic symbol.

For a **formal symbol**, semantic fields may remain externally uninterpreted.

For a **semantic symbol**, MF3 grounding fields must be established.

For a **compositional symbolic expression**, constituent role/binding/composition relations become central.

---

# 42. Provisional symbol definition after MF3-E

> **A symbol is a re-identifiable typed representational/formal vehicle whose token identity can be abstracted from incidental physical variation and recruited under type-/role-governed operations within a system or practice. A semantic symbol additionally participates in a grounded content/reference relation; a compositional symbolic system supports reusable constituents/roles whose contributions can be systematically rebound and combined into larger content-bearing structures.**

This definition deliberately separates three strengths:

```text
S0 Formal symbol
   typed manipulable token

S1 Semantic/referential symbol
   S0 + grounded content/reference

S2 Compositional symbol system
   S1 + reusable roles/constituents + binding/composition

S3 Productive/systematic symbolic capability
   S2 + robust novel recombination/generalization
```

These are capability profiles, not mandatory linear stages.

---

# 43. Symbolic capability profile

MF3-E proposes independent axes:

- type stability/re-identifiability;
- syntactic manipulability;
- designation/reference;
- grounding provenance;
- context sensitivity;
- constituent reuse;
- variable/role binding;
- compositionality;
- decomposition;
- substitution/rebinding;
- recursion;
- productivity;
- systematicity;
- interpretability/executability;
- public/conventional shareability.

### Result

**RE-40 — Symbolic systems should be characterized by capability profiles rather than one binary `symbolic/non-symbolic` label.**

---

# 44. MF3-E provisional axioms

**RE-01** Representation is broader than symbolic representation.

**RE-02** Symbol token and symbol type are distinct; symbolic operations presuppose re-identification/equivalence rules.

**RE-03** Formal symbolhood and semantic grounding are distinct.

**RE-04** Newell–Simon-style operational designation is strong systemic-use evidence but not a complete grounding theory.

**RE-05** Arbitrary physical shape is neither necessary nor sufficient for symbolhood.

**RE-06** Iconic, indexical and symbolic representational modes can coexist.

**RE-07** Reference is not identical to content; not every meaningful symbol individually refers to an object.

**RE-08** Type identity does not imply referent identity; token/context can determine reference.

**RE-09** Context can be constitutive of token reference in indexical/deictic systems.

**RE-10** Content/reference rules can exist without successful current referent resolution.

**RE-11** Names, variables, identifiers, pointers/handles and semantic reference are distinct roles.

**RE-12** Syntax and semantics are distinct; formal manipulation does not by itself ground meaning.

**RE-13** Symbol grounding can be graph-mediated and inherited; pure uninterpreted symbol-symbol closure does not independently ground semantics.

**RE-14** Compositionality is systematic whole-content construction from reusable constituent contributions plus combination structure/context.

**RE-15** Compositionality is not required for every atomic symbol.

**RE-16** Compositionality can be partial/context-bounded rather than perfectly context-free.

**RE-17** Productivity and compositionality are distinct.

**RE-18** Systematicity and compositionality are distinct; systematicity is a capacity/generalization signature.

**RE-19** Fodor–Pylyshyn systematicity remains a falsification challenge without fixing implementation architecture.

**RE-20** Role–filler binding is required wherever constituent role/order alters content.

**RE-21** Variable/role identity and filler identity are distinct.

**RE-22** Fully distributed vehicles can implement symbolic role/binding structure.

**RE-23** Analyst-decomposable vectors are not automatically systemically symbolic.

**RE-24** Symbolic representation is an operational format profile rather than a substrate category.

**RE-25** Formal compositional syntax can remain semantically underdetermined.

**RE-26** Constituents can contribute predicates/functions/binders/relations rather than individual referents.

**RE-27** Formal type identity and semantic identity are distinct.

**RE-28** Namespace/scope/context are first-class symbolic reference infrastructure.

**RE-29** Symbol grounding provenance must remain typed: systemic, derived/designed, conventional/public, analyst-ascribed.

**RE-30** LLM/subword token IDs are formal code/symbol elements at the tokenizer interface; semantic-symbol status is a separate grounding/content claim.

**RE-31** Token boundaries do not define concept boundaries.

**RE-32** Symbolic I/O does not establish a classical symbolic internal architecture.

**RE-33** Compositional-generalization tests provide capability evidence, not a universal definition of symbolhood.

**RE-34** Symbolic and distributed/subsymbolic descriptions can apply at different levels of one system.

**RE-35** Symbolic role structure can be explicit or distributed; explicit addressability is a separate property.

**RE-36** Content-preserving rebinding/substitution is strong evidence of compositional symbolic organization.

**RE-37** Recursion is powerful but not universally constitutive of symbolhood.

**RE-38** Discrete vehicle identity does not imply precise/discrete semantic content.

**RE-39** Symbolic failures separate token/type, binding, scope, reference, composition, semantic and syntax failure loci.

**RE-40** Symbolic capability should be profiled multidimensionally rather than treated as one binary natural kind.

---

# 45. Claims rejected by MF3-E

Reject as universal foundational claims:

- every representation is symbolic;
- every discrete token is a semantic symbol;
- formal symbol manipulation automatically supplies meaning;
- symbol shape must be arbitrary;
- arbitrary shape is sufficient for symbolhood;
- iconic/indexical/symbolic signs are mutually exclusive object classes;
- every meaningful symbol must refer to one actual object;
- symbol type has one fixed referent across all tokens/contexts;
- names, identifiers, variables and pointers are the same kind of reference;
- syntax and semantics are the same relation;
- every semantic symbol must directly ground in sensorimotor experience;
- a dictionary/web of symbol-symbol definitions can bootstrap intrinsic grounding from nothing;
- every symbol must be compositional;
- compositionality means simple token concatenation;
- productivity is identical to compositionality;
- systematicity is identical to compositionality;
- symbolic/compositional structure requires local one-hot or one-neuron-per-symbol implementation;
- distributed/vector representations cannot implement symbolic structures;
- any vector decomposition found by an analyst proves systemic symbolic structure;
- role/filler binding is unnecessary if all constituents are present;
- recursion is necessary for every symbol system;
- discrete symbolic tokens imply exact/discrete meanings;
- tokenizer token = word = concept;
- LLM token vocabulary is a semantic ontology;
- symbolic input/output proves classical symbolic internal computation;
- successful language generation alone proves robust compositional systematicity.

---

# 46. Hard cross-domain falsifiers

## 46.1 Formal logic

Tokens and rewrite rules can be fully formal while multiple interpretations remain possible. Shows syntax/composition without intrinsic world grounding.

## 46.2 Programming identifier

The string `x` can denote different variables under different lexical scopes. Same type-like spelling, different binding/reference.

## 46.3 Pointer/address

Numeric address `0x...` designates relative to process/address-space/runtime state. Same number is not a universal referent.

## 46.4 Indexical `I`

Same linguistic type, different token referents by context. Falsifies fixed type→referent mapping.

## 46.5 Fictional name

A symbolic expression can support stable inferential content in a fictional domain without an actual physical referent.

## 46.6 Tensor-product binding

Distributed vector vehicles can preserve symbolic role/filler structure. Falsifies localist implementation necessity.

## 46.7 LLM BPE token

Discrete token ID is formally stable while conceptual content may span multiple tokens and contextual hidden states. Falsifies token=concept.

## 46.8 SCAN

A neural sequence system can succeed on many familiar combinations yet fail novel systematic recombination. Falsifies performance-on-seen-compositions = compositional systematicity.

---

# 47. Primary/original literature anchors

- Newell, A. & Simon, H. A. (1976), `Computer Science as Empirical Inquiry: Symbols and Search`, *Communications of the ACM* 19(3), 113–126. Defines physical symbol systems in terms of physical symbol patterns/tokens, expressions, processes, designation and interpretation; states the Physical Symbol System Hypothesis.
- Harnad, S. (1990), `The Symbol Grounding Problem`, *Physica D* 42, 335–346. DOI: 10.1016/0167-2789(90)90087-6. Distinguishes merely formal symbol manipulation from intrinsically/systemically grounded semantics and proposes grounding elementary symbols in nonsymbolic iconic/categorical representations.
- Fodor, J. A. & Pylyshyn, Z. W. (1988), `Connectionism and Cognitive Architecture: A Critical Analysis`, *Cognition* 28, 3–71. DOI: 10.1016/0010-0277(88)90031-5. Develops the systematicity/productivity challenge and argues for combinatorial syntactic/semantic constituent structure.
- Smolensky, P. (1990), `Tensor Product Variable Binding and the Representation of Symbolic Structures in Connectionist Systems`, *Artificial Intelligence* 46, 159–216. DOI: 10.1016/0004-3702(90)90007-M. Gives distributed role–filler binding and recursive symbolic-structure representations using tensor products.
- Smolensky, P. (1987), `Analysis of Distributed Representation of Constituent Structure in Connectionist Systems`, NeurIPS 0. Earlier distributed role/filler-binding analysis.
- Kaplan, D. (1989), `Demonstratives: An Essay on the Semantics, Logic, Metaphysics, and Epistemology of Demonstratives and Other Indexicals`, in *Themes from Kaplan*, 481–563. Distinguishes context-sensitive rules/character from token content/reference for indexicals and demonstratives.
- Sennrich, R., Haddow, B. & Birch, A. (2016; arXiv 2015), `Neural Machine Translation of Rare Words with Subword Units`, ACL. arXiv:1508.07909. Uses fixed vocabularies of subword units/BPE to encode open-vocabulary text as discrete token sequences.
- Vaswani, A. et al. (2017), `Attention Is All You Need`, NeurIPS. arXiv:1706.03762. Transformer maps discrete input/output symbols through embeddings and contextual sequence computation with attention.
- Lake, B. M. & Baroni, M. (2018), `Generalization without Systematicity: On the Compositional Skills of Sequence-to-Sequence Recurrent Networks`, ICML/PMLR 80, 2873–2882. SCAN demonstrates severe failures under systematic novel recombination despite success in easier/generalization-nearby regimes.

---

# 48. MF3-E reconstruction

The strongest reconstruction is three-layered:

```text
Layer 1 — Formal symbolic organization
  token/type identity
  expressions
  syntax
  role/binding
  substitution/composition

Layer 2 — Grounded symbolic semantics
  content/domain/reference
  grounding provenance
  context/namespace
  evaluation

Layer 3 — Productive compositional capability
  reusable constituents
  systematic rebinding/recombination
  recursive/structured composition where supported
  novel-generalization behavior
```

These layers can dissociate.

A proof calculus may be rich at Layer 1 and externally interpreted at Layer 2.

A public word may have conventional Layer-2 semantics while one specific neural internal state implements it nonlocally.

A learned neural system may manipulate token sequences yet show weak Layer-3 systematicity.

A distributed TPR-style implementation can realize Layer-1/3 symbolic organization without local symbolic units.

---

# 49. Deep synthesis

MF3-E replaces the vague question:

> `Is this system symbolic?`

with a sequence of typed questions:

1. **What are the token types and how are tokens reidentified?**
2. **What formal operations depend on token/type/role structure?**
3. **Which expressions designate/refer, and under what context/namespace/binding?**
4. **Where does semantic grounding come from—systemic, designed, conventional, public or merely analyst-ascribed?**
5. **Does the system preserve constituent identity and role–filler binding?**
6. **Can constituents be rebound/substituted/composed while preserving structural content?**
7. **Does it generalize systematically to novel combinations?**
8. **At which level is the implementation local/discrete versus distributed/continuous?**

The resulting non-collapses are:

`Symbol token ≠ Symbol type ≠ Reference ≠ Content.`

`Formal symbol ≠ Semantic symbol.`

`Syntax ≠ Semantics.`

`Name ≠ Variable ≠ Identifier ≠ Pointer.`

`Compositionality ≠ Productivity ≠ Systematicity.`

`Symbolic organization ≠ Localist implementation.`

`Token ID ≠ Word ≠ Concept.`

---

# 50. MF3-F handoff — Neural & Biological Representation

MF3-A–E now give enough ontology to attack neural representation without importing semantic labels from experimental practice.

MF3-F should ask:

- what evidence licenses `neuron/population represents X`;
- tuning ≠ content;
- encoding vs decoding vs causal use;
- receptive fields and feature detectors;
- population codes;
- mixed selectivity;
- place/grid/head-direction cells;
- predictive/remapping/context effects;
- reference frames;
- temporal codes;
- neural manifolds/dynamics;
- explicit vs implicit uncertainty;
- causal perturbation evidence;
- whether neural variables are symbols, analogue representations, latent states or control dynamics;
- direct/nonrepresentational sensorimotor alternatives;
- how biological grounding/history/function differs from artificial labels/probes;
- whether compositional role/binding has convincing neural realizations;
- how to avoid one-neuron-one-concept and decoder's-dictionary fallacies.

This is **MF3-F — Neural & Biological Representation**.

---

# Final MF3-E handoff

MF3-E establishes that `symbol` is not synonymous with meaning, discreteness or language.

> **Formal symbolhood is typed manipulability and re-identifiable token/role structure. Semantic symbolhood additionally requires grounded content/reference. Compositional symbolic organization additionally requires reusable constituents and role/binding relations that support systematic content construction.**

The deepest falsification is two-sided:

- pure syntax does not create semantics;
- semantics/compositionality do not require local discrete physical symbols.

Harnad blocks `syntax = meaning`; Smolensky blocks `symbolic structure = localist implementation`.

The next round moves from symbolic vehicles to the biological substrate where representational language is often used most casually.

**Next: MF3-F — Neural & Biological Representation.**
