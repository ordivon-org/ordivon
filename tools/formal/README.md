# One formal verification tool group

Run from Ordivon repository root: mise run formal:verify

The directory declares the currently verified latest stable native GitHub
releases. Update them together when newer stable releases are published.
Keep precise resolved versions and test both valid and invalid obligations.
This is an optional mise tool group; normal repo:ci does not download
the large proof systems. No new mathematical kernel, graph authority,
package manager or agent is created.

For read-only incremental input impact before contemplating another
expensive Formal run, use the already deployed repository source
consumer in tools/repo/evidence_validity.py with --current-sha,
--prior-sha and --formal-source-delta. It compares this runner's
historical SOURCE_FILES declarations and Git mode/blob identities;
it DOES NOT run Lean/Z3, certify the current binary toolchain,
replay a proof or grant proofReuseAdmissible. The native formal:verify
producer already emits the required original proof probes, source
blobs, binaries and observed resources, and GitHub CI validates those
receipts; retain that owner evidence. No new proof database or
shadow tool runner is necessary for source-only delta questions.

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

Data Owner now has an opt-in Lean 4.35 abstract digest/product-admission
model plus CrossHair PEP 316 symbolic checking of the Python classifier.
Use `mise run data:formal:verify`, which reuses this tool group's Lean
version; Data retains its I/O and consumer acceptance tests. No full
Python-to-Lean implementation refinement is asserted.

The Quint Apalache backend v0.62.1 currently fails download in this
environment: do not label Quint simulation as MODEL_VERIFIED.
Rocq/Isabelle/other heavy proof ecosystems are separate options pending
a reproducible installation source and an actually distinguishable consumer.


## Historical Formal receipts for evidence-first Agents (2026-11-14)

The existing Formal verifier already emits a source-qualified PASS JSON report
with Git blobs, toolchain binary/resource hashes and model probe results.
GitHub CI validates this exact report and now publishes it AFTER successful
validation using its existing pinned official Artifact Action. Artifact name:
ordivon-core-formal-<GitHub SHA>, retained 30 days. There is no new proof run.

The read-only existing repository evidence consumer can use the original
GitHub Check Run and official gh run download when explicitly requested:
tools/repo/evidence_validity.py --prior-sha FULL_PROOF_ANCESTOR_SHA
--current-sha FULL_CURRENT_SHA --formal-source-delta
--fetch-historical-formal-report.

The source-bound report is not a proof that an unchanged Git blob implies
unchanged installed consumers, dynamic loader behavior or verifier toolchain
across time. Those facts remain UNKNOWN, and proofReuseAdmissible remains
false. An unselected, missing or expired report does not cause retries.
