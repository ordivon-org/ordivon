# Input-Induced Latent-State Controllability — Thought LEGO R1

**Identity:** `thought:research/latent-input-controllability-r1`
**Home:** Ordivon Research (conceptual thought LEGO), with native Formal verification under `tools/formal/`.
**Status:** PROVEN_ABSTRACT_CORE / EMPIRICAL_UNKNOWN / INDEPENDENT_REVIEW_REQUESTED
**Mathematical authority:** no fixed Owner and no approval-based validity.
Any Agent may submit a proof term or countermodel. Only checked theorems
under explicit assumptions substantiate abstract mathematical statements;
Git/Runtime attest to source execution, not mathematical truth.
**Current source base:** `927d9be1f312790bd5e01cbf74556ce579db4a92` (protected main at this proof qualification; not deployed-source truth).
**Formal artifact:** `tools/formal/LatentInputReachability.lean` — Lean 4.35.0 via existing `tools/formal/mise.toml`.

## Origin and corrected idea

A reported Qwen3.5-4B neuron-steering demonstration motivates a general question:
can a *legal external input* create an internal state or observable behavior
similar to a *direct internal intervention*? A neuron index, steering dose or
hostile output **does not** by itself prove a prompt bypass, a universal trigger,
an instruction-hierarchy failure, or a mechanistic semantic interpretation.

The research object is input-constrained controllability, not an exploit string.

## Typed ports / representation

Given context `C` (at minimum higher-priority instructions, model revision,
tokenizer, runtime conditions and relevant environment), prompt/input `P`,
internal state/trajectory `H`, observed behavior `O`:

- `allowed : C → P → Prop` — admissible input domain.
- `encode : C → P → H` — actual system transition for a fixed implementation.
- `intervene : H → H` — direct internal state operation; not a prompt.
- `observe : H → O` — declared observer; may be lossy.
- `safe : C → H → Prop` — declared safety property, not assumed to hold.

`Reachable(c,h) := ∃ p, allowed(c,p) ∧ encode(c,p)=h`.

`Exact(c,base) := Reachable(c,intervene(encode(c,base)))`.

`Behavioral(c,base) := ∃ p,allowed(c,p) ∧ observe(encode(c,p))
=observe(intervene(encode(c,base)))`.

The `State` type may represent a **whole layer×token trajectory** rather than
one neuron value; an observer may be behavior, a probe or a validated system
effect. No universal claims arise from an arbitrary observer.

## Mechanically checked mathematical claims

1. Exact state emulation implies observational emulation **for the fixed observer**.
2. Assuming *all allowed inputs* satisfy an explicitly stated safe-state invariant,
   a target violating that invariant cannot be exactly emulated by such an input.
3. The existing R2.1 assume/guarantee `IOContract` + totality formulation admits
   ordinary behavior under that invariant; an unsafe internal intervention fails
   the same port contract for an allowed base input.
4. A nonempty finite example has observed equivalence but impossible exact state
   emulation, and an unsafe direct target. Therefore observational equivalence
   does **not** imply exact reachability or full safety.
5. A finite two-context example shows that exact reachability in one context does
   not imply exact reachability in another.

These are **conditional mathematical theorems and countermodels**, not verified
facts about the weights of Qwen or any deployed LLM. Lean compilation is proof
checking, not causal experiment validation. Confirm via native Lean executable
and a negative false-theorem rejection, with no `sorry` or new axioms.

## Scientific claims NOT discharged by Lean

- Actual effect of Qwen3.5-4B L14 N8949 / L13 N7956: **UNVERIFIED_HERE**.
- Natural input simulation of a concrete Qwen activation perturbation: **UNKNOWN**.
- Cross-prompt, cross-context, cross-version, cross-modality, cross-model stability: **UNKNOWN**.
- Model-internal refusal vs instruction priority vs external tool authority:
  distinct hypotheses with separate observables; **no inference of system bypass**.
- Statistical confidence, adverse side effects, causal mediators and distribution
  drift: require experiments and independently held-out validation.
- Formal guarantee of real safety: **NOT CLAIMED** without executable
  implementation refinement, correct observer, property, assumptions and scope.

## Research / falsification obligations

- E1: Measure neutral behavioral traits (format, register, verbosity) with fixed
  model revision, tokenizer, seed, decoding and input-domain controls.
- E2: Compare equal-norm random internal perturbations and no-op controls.
- E3: Compare output agreement, declared probes and layer/token trajectories
  separately; perform causal intervention tests, not correlation alone.
- E4: Check non-target capabilities and environmental drift, and report
  failures and counterexamples instead of optimizing operational jailbreaks.
- E5: Seek independent Formal/Research/Security review of the observer,
  allowed-input predicate, invariants, type boundaries, and proof artifacts.
- E6: Reuse current R2.1 LEGO primitives and owner test infrastructure; only
  expand if a demonstrated consumer requires it.

## Currentness / invalidation

A model revision, tokenizer, multimodal encoder, runtime semantics, system
context, `allowed` policy, `observe` definition, `safe` definition,
Lean/toolchain version, or dependent R2.1 contract change can invalidate the
applicability of an experimental conclusion. Unchanged theorem source alone
does not preserve the correspondence to a changed deployed system.

**Coordination:** `space:ordivon-meta-thinking-r1:20261024`,
`topic:latent-input-state-controllability-formal-r1:20261027`,
`work:ordivon:latent-input-state-controllability-formal-r1:20261027`.

## R2 — Ownerless mathematical acceptance and formal refinement

No fixed Owner or reviewer opinion grants mathematical acceptance.
Any Agent may submit a falsifiable conjecture, proof term or finite countermodel.
The acceptance basis is a mechanically checked theorem **with explicit
assumptions**, not a human/agent vote, GitHub review, job result or audit
prose. Execution/source identity is evidence about what ran, not theorem truth.
The current source/verification artifact must still be bound to real inputs.

### Additional proved obligations (Lean)

- A safety property is determined by an observer exactly when it factors
  through that observer to a predicate on observations. This is a logical
  condition; a narrow observation is not automatically safety-complete.
- Behavioral imitation preserves safety **under** the stated
  observer-determination and safe-input assumptions; a countermodel
  demonstrates unsafe hidden states with equal behavior.
- An injective observer makes observed equality sufficient for exact
  state equality; without it the original nonconverse remains.
- A changed observer alone can reverse behavioral reachability while
  admissible inputs, encoder, intervention and safety predicate stay fixed.
- Exact reachability transports across environment changes if allowed-input
  membership, *reachable* encoded states, and the intervention target
  remain equivalent. Observational reachability needs only the corresponding
  declared observations; input-safety invariants need only property
  equivalence on allowed reachable inputs.
- Abstract invariants transfer to a concrete implementation only through
  explicitly supplied admissibility, state-relation simulation and
  safety-preservation premises. A finite countermodel shows agreement of
  the observations alone does not provide that correspondence.

Each proof retains its original quantified model scope. In particular,
''if and only if'' above applies only to *observer-factorization*, not to
the sufficient-condition theorem about safety under Behavioral.

### Incremental impact principle

A version bump or environmental change is neither a mandatory global
invalidation nor an automatic preservation: compare exactly the predicates
and evaluations used by each theorem. State reachability, observational
reachability and safety invariants have different relevant slices.
Where an obligation cannot be established, the disposition is UNKNOWN,
never proof-by-unchanged-source or proof-by-agent-approval.

### Unresolved implementation boundary

Qwen neuron effects, actual prompt-state trajectories, neural implementation
refinement, cross-model generalization and real adversarial behavior remain
unproved. Lean checked propositions over abstract function symbols,
not the inference implementation or its trained parameters.

## R3 — Token-indexed trace and inductive safety

This stage extends the input/state abstraction to a transition system with
initial(c,h), transition(c,h,h-next), and safe(c,h). A ValidTrace
is a mathematical function Nat -> State (token/time index). It is not
a measured transformer activation sequence or a stochastic model.

Machine-checked proof obligations:

- Inductive global trace safety: initial safety and preservation at
  every valid step imply safety at every token index.
- Trace-local incremental reuse: a changed environment preserves trace
  validity when initial and actual transition predicates preserve truth
  on this trace. Unreachable states need not be checked for this claim.
- Property-local reuse: safety transfers between models along a fixed
  trace when their safety predicates agree at every visited state.
- Relational simulation: initial relation and paired step preservation
  lift a state relation to all time indices; an explicit safety-reflection
  premise transfers abstract safety to concrete safety.
- Two countermodels: identical observations at every token index can
  conceal different safety values; a safe initial state can become unsafe
  on a valid but non-safety-preserving transition.

A theorem about one fixed trace does NOT prove preservation of all
possible future traces or that modified software generates the same
trajectory. The real model-to-proof bridge, sampling policy, cache
semantics, decoder, runtime state, and actual Qwen parameter behavior
remain UNKNOWN. An abstract Lean theorem establishes only the
implication under its hypotheses; unproven implementation correspondence
cannot be supplied by human or Agent approval.

### R3 source-cut proof-kernel correction

The protected main at 632c735b01e70cdaf807cbf5ac161c0eea774684
contained two competing OrdivonR21.DependsOnlyOn declarations
(readset/goal and actual-dependency/observation functions), which made
Lean reject the second declaration and leave affected theorem stubs
with sorryAx in its post-error diagnostic. The minimal repair renames
the *second* declaration to DependsOnlyOnActualDependencies and updates
its two consumers. Both original and repaired sources were checked by
the same native Lean binary: the original fails, the repaired copy
compiles and reports no axiom dependencies for the two frame theorems.
This fixes a mathematical proof-kernel failure, not a deployed-systems
safety proof.

## R4 — Nondeterministic traces and exact two-outcome probability

Mathematical scope: finite paths through nondeterministic transition
relations and a normalized two-outcome rational-risk carrier using exact
natural-number masses. No floating-point approximation, no claim that
Qwen's deployed sampler uses these particular normalized masses.

New mechanically checked results:

- NondetReachable is inductive and ranges over every valid finite
  transition, not only one preselected synchronized sequence.
- Initial-state safety and step-invariant safety imply safety for every
  nondeterministically reachable state.
- Forward simulation weakens R3's overly strong universal paired-step
  hypothesis: every concrete successor must admit some related abstract
  successor. It preserves reachability and safety under explicitly stated
  safety reflection.
- A finite countermodel shows a safe initial state still admits an unsafe
  nondeterministic successor without step preservation.
- BinaryFiniteMass is normalized by safeWeight + unsafeWeight = total
  with total > 0. RiskAtMost compares rational risk to a nonnegative
  rational budget using exact integer cross-products.
- Zero risk is equivalent to zero unsafe mass in this binary finite carrier.
  A normalized 1-safe/1-unsafe example satisfies a 1/2 bound but violates
  the zero-risk bound. Its observed safe output cannot certify zero risk.
- Under an additional support-soundness premise linking every positive
  unsafe mass to a real transition, an inductive safety invariant forces
  zero unsafe mass.
- Countermodel: zero assigned probability for an unsafe branch does
  not prove no unsafe transition exists. A pathwise universal property
  differs from support-relative probability-zero safety.

Unproved obligations:
- An actual model's tokenizer, decoder, hidden-state transition relation,
  randomness source, support, temperature/top-k/top-p policy and numerical
  semantics must be mapped to the abstract machine; this is not supplied
  by abstract Lean proofs, Git metadata or Agent agreement.
- The two-outcome exact mass carrier is NOT a general measure-theory or
  multi-step stochastic-process formalization. It is the smallest
  nonvacuous, falsifiable probability building block.
- Conditional probability, temporal risk accumulation and statistical
  estimation are not proved in R4. Theoretical claims are restricted to
  the named assumptions, finite carriers and proof terms.


### R4 latest-main integration

The prior duplicated-declaration fault was mathematically reproduced and
repaired in a source-scoped experiment. Since then another Agent's independent
mainline changes merged a distinct safe remedy, placing observable-dependency
frame proofs in their own file and eliminating the duplicate symbol. R4
therefore reuses the *current* upstream R2.1 kernel and variation-frame
file without carrying an obsolete alternate definition fix. The original
counterexample remains historical evidence, not a claim that main is still
broken.

Proof qualification must compile all three current files (Recursive LEGO,
Variation Frame, Latent Input) with the current exact source and verify the
expanded theorem set without axioms.
