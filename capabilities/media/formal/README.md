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


## Creative Library: version-bound acceptance (Lean proof + Python refinement)

`CreativeLibraryAcceptance.lean` is checked by the existing
`tools/formal/verify.py` native Lean 4 gate, with the proof source, Python
producer and bounded refinement witness in the existing Git SourceCut.
It specifies the predicate:

`CurrentBinding <=> semanticDigest(selected) == semanticDigest(accepted)
AND fileSha256(selected) == fileSha256(accepted), with all four known.`

Lean's kernel checked `current_requires_both_identities`, semantic-mismatch
rejection, absent-source non-promotion, missing-file non-promotion and a
non-vacuous positive example. The model uses `Option Nat` opaque digest
identifiers: it **does not** model JSON parsing, hash collision resistance,
filesystem read atomicity, actual archive authority or Human approval.

**Implementation refinement (bounded, not a universal proof):**
`creative_index_library._catalog_acceptance_relation` is a pure equality
decision over optional digest strings, called after the selected Catalog's
bytes are read. `tests/test_creative_index.py` checks all 625 cases of the
five-representative presence/equality quotient of its four identity inputs.
Because this quotient treats digest values only through equality and
presence, the test is a scoped refinement witness for the currently
audited source; it is not a kernel proof of Python or a theorem over arbitrary
language objects. The existing independent source-scoped proof gate binds
both this implementation and witness to exact committed Git blobs.

**Real consumer:** `creative_index.build_creative_index` reads the selected
`artifacts/creative-library/catalog-v1.json` and the older historical R1/R2
acceptance receipts. In the inspected SourceCut, both project with
`standing=HISTORICAL_ACCEPTANCE_NOT_CURRENT` and preserve their original
`declaredStanding`. Six actual derived preview bytes, three provenance
receipts and the manifest separately passed exact SHA-256 readback. These
media facts are not implied by the Lean theorem and remain provider/consumer
evidence.

**Tool invocation:**

```bash
mise -C tools/formal exec -- lean ../../capabilities/media/formal/CreativeLibraryAcceptance.lean
# After committing exact source and proof:
mise -C tools/formal run verify
```

The first command is for an immediate model edit check; the existing full
verifier requires all registered formal files to match committed HEAD.
No second proof engine, local registry or release gate was created.

**Test retirement:** the redundant synthetic mismatched-file acceptance
example was retired once the complete finite equality quotient covered the
pure decision property. Keep one source-to-Creative-Index integration witness
and exact historical Catalog bytes readback; neither a Lean abstract proof
nor the quotient covers actual JSON, disk, archive PG, browser or media effects.

Human: compare the *selected* Catalog ID and both digests; a historical PASS
is evidence for an older SourceCut, not proof your current Library is ready.

Agent: report model proof, bounded Python refinement, native byte readback,
and external browsing/rights acceptance separately. Missing either digest
remains UNKNOWN rather than FALSE or PASS; do not silently rewrite receipts.


## TimedText millisecond delivery precision: source ticks -> native consumer

The selected Production's editable TimedText uses positive integer
`ticksPerSecond` and source Cue intervals `startTick < endTick`.
WebVTT and SRT output only represent integer milliseconds, and W3C WebVTT
requires the end timestamp to be *strictly greater* than start.
Rounding distinct source ticks may collapse to the same delivery millisecond:
the former exporter generated `00:00:00.000 --> 00:00:00.000` for
`ticksPerSecond=10000, startTick=1, endTick=2`.

**Specification:** nearest-millisecond rational conversion with ties to
even, without binary64 float conversion. A source Cue can be exported only
if its two converted timestamps remain strictly ordered; otherwise reject
it without modifying source ticks or silently stretching its duration.

**Model and proof:** `TimedTextDeliveryPrecision.lean` models the pure
Nat quotient/remainder rounding rule and representability predicate.
Lean checks that admitted intervals have positive delivery duration, that
a collapsed interval or zero tick base cannot be admitted, and real
counterexample/positive/tie-to-even witnesses. These are abstract
mathematical claims about the selected conversion rule, not the Python
interpreter or the FFmpeg implementation.

**Implementation refinement:** `timed_text._milliseconds` computes
`round(Fraction(tick*1000, ticksPerSecond))` exactly. The shared
`_delivery_interval_milliseconds` controls both exports and is checked
by the delivery validator. `tests/test_timed_text.py` compares the
implementation with an independent `divmod` oracle over 9 time bases
and 92 distinct tick examples, including ties and large integers; this is
a bounded refinement witness and not universal proof.

**Real consumer:** Production `runtime-introduction` has nine locked
narration cues and exactly 78 seconds of source duration. Both actual
WebVTT and SRT exports parsed as nine positive-duration packets in native
FFprobe. The existing pinned TTML/ttconv native positive/negative smoke
also passed. Their exact bytes and codec/parser behavior are not proven
by the Lean model.

**R2.1 standing:** SPEC/MODEL/LEAN proof PASS, bounded source implementation
refinement PASS, native selected Production readback PASS; general
implementation refinement, arbitrary subtitle semantics and human
accessibility remain UNKNOWN. Source-derived files, rights claims, and
finished delivery are distinct from technical cue correctness.

Human: inspect the source cue time base before delivery, and edit a Cue
if its intended duration cannot be represented by SRT/WebVTT. Do not
discard higher-resolution timing just to silence an exporter.

Agent: call `validate_timed_text_delivery` with the actual media duration
before generating a delivery file, then call `export_srt` or
`export_webvtt` and inspect native parsed timestamps. An unrepresentable
Cue is a clear failure of that delivery format, not a reason to mutate
the canonical source time.
