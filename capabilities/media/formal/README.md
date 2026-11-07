# Media native Processing admission: formal evidence boundary

This is an owner-scoped **model**, not a second executor, registry, or media codec.
The current R2.1 contract for `studio_processing_profiles` →
`studio_processing_probe_plan` is carried by the existing Python producer
`src/ordivon_studio/agent_processing.py`.

## Specification → model → proof

`MediaNativeProcessingAdmission.lean` models one discovered snapshot and one
requested Profile/Adapter identity. Its **Nat** IDs stand for opaque identity
tokens, not hash-function implementations. The model's `Admissible` requires:
exact profile ID, exact profile digest, exact adapter digest, adapter and path
presence, nonempty input, and nonempty evidence destination.

Lean kernel checks:
- A compiled proposal exists **iff** the abstract admission predicate holds.
- A proposal preserves both exact digest identities and the profile identity.
- Stale profile or adapter digests, missing adapter or missing input reject.
- Technical QC observation does not change publication approval.

Use the **existing Ordivon Formal toolchain**, from the repository root:

```bash
mise -C tools/formal exec -- lean ../../capabilities/media/formal/MediaNativeProcessingAdmission.lean
```

This source is also consumed by `tools/formal/verify.py` using the existing
source-scoped Lean proof gate; the CI source selection now includes Media's formal
model and exact Python producer.

## Implementation refinement is still UNKNOWN

The Python producer reads JSON profiles and adapter bytes, hashes them with
SHA-256, checks expected digests, and returns a nonexecuting Runtime proposal.
The model does **not** prove the Python implementation, path resolution, source
byte continuity between compile and dispatch, SHA-256 collision resistance,
Runtime's effect semantics, or native tool soundness. A source-cut reference
binds the file to the proof run but **is not a source-to-model refinement proof**.

The implementation witness `tests/test_agent_processing.py` exercises a
real profile edit and real adapter edit between discovery and compilation.
Retain that test until semantic implementation refinement is actually proved,
rather than deleting it merely because a Lean model theorem succeeds.

When an actual production consumes a plan, Runtime must independently bind
the exact selected bytes and tool prerequisites at the applicable execution
boundary; no current generic `studio_processing_probe_plan` result is a
permanent byte-immutability guarantee. Preserve the existing FFprobe/FFmpeg,
OTIO and timed-text native real-consumer checks for physical facts.

## Human versus Agent

**Human:** select a Production and real source, review its Claim, the exact
Processing Profile, the technical receipt, and separately judge rights,
quality and delivery acceptance. See `../docs/human-guide.md`.

**Agent:** use the already registered `media-native-processing` Skill,
discover the exact current digest-bound Profile, compile without effects,
run only through Runtime, observe the Job, and never elevate technical evidence
into publication authority. See `../../../.agents/skills/media-native-processing/SKILL.md`.

### Deletion/retirement criterion

A redundant specimen test can be removed only when a proof covers its exact
property **and** a valid implementation-refinement connection exists. Source
carrier integrity, real hardware/media tools and delivery remain actual
consumer evidence. Otherwise report `UNKNOWN`, not a fabricated proof.

## IEEE-754 loudness profile admission: Z3 model + source consumer

LoudnessProfileSafety.smt2 directly models the comparison semantics of the
existing qc.validate_loudness decision on binary64 values with a finite
measured programme. Its three Z3 answers are SAT / UNSAT / SAT:

1. The historical comparison-only decision can accept a NaN target.
2. The strengthened finite-parameter admission cannot accept a nonfinite
   selected target, tolerance or true-peak limit in this model.
3. A normal finite programme/profile remains admissible (nonvacuity).

This is an IEEE-754 MODEL property, not proof that arbitrary Python float
executions refine this SMT model. The source implementation adds explicit
math.isfinite checks for selected limits and rejects negative tolerance.
tests/test_qc.py is the selected actual Python consumer witness, with a native
FFmpeg measurement retained for the physical tool boundary.
tools/formal/verify.py invokes Z3 under existing source-scoped tool and Git-cut
evidence; CI checks all three answers rather than exit code alone.

A trial CrossHair path search against actual Python returned Not confirmed;
that result is UNKNOWN, not a theorem or permission to delete real consumer
verification. No extra CrossHair runtime/test scaffold is retained.

Human: invalid profile thresholds reject before QC. Correct the delivery
profile, then review technical receipts and separate rights/creative approval.
Agent: select the current Profile, reject nonfinite limits, execute the native
adapter via Runtime, and bind receipts to actual Production/Output consumers.
