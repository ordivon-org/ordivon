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
