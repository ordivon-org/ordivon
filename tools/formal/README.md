# One formal verification tool group

Run from Ordivon repository root: mise run formal:verify

The directory declares the currently verified latest stable native GitHub
releases. Update them together when newer stable releases are published.
Keep precise resolved versions and test both valid and invalid obligations.
This is an optional mise tool group; normal repo:ci does not download
the large proof systems. No new mathematical kernel, graph authority,
package manager or agent is created.

Lean 4: kernel-checked relational/refinement lemmas. The Media native-processing
admission model is also proved by this existing runner and binds its current
Python producer to the Git source cut. This DOES NOT prove the producer's
Python control flow refines the Lean model; see
`../../capabilities/media/formal/README.md` for the scoped obligations.
Z3 and cvc5: independent SMT SAT/UNSAT. Z3 also checks Media's
IEEE-754 loudness parameter admission model (SAT historical counterexample,
UNSAT strengthened invalid admission, SAT valid nonvacuity); Python refinement
remains UNKNOWN and native QC acceptance remains consumer-owned.
Verus: Rust proof obligations, including deliberately false postconditions.
Dafny: contract verification with a negative counterexample.
Quint: type-checking only; the rust evaluator ran a bounded simulation.
Alloy 6: finite SAT analyzer. No effect/installed-domain claim is implied.
Kani 0.68.0 and TLA+/TLC 1.7.4 already have native owners and are reused.

The Quint Apalache backend v0.62.1 currently fails download in this
environment: do not label Quint simulation as MODEL_VERIFIED.
Rocq/Isabelle/other heavy proof ecosystems are separate options pending
a reproducible installation source and an actually distinguishable consumer.
