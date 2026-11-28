# Media R11 execution refinement
Truth role: execution specification, not a second registry, currentness authority,
or claim that all tasks are complete. Extends planning/lego-plan-r1.json V01–V11
and Host Media Topic #32674. Exact starting source 63ea15e7d329df0bcf85cb07d0815356dfeeed4f.

## Goal, reality, change
Goal: a named consumer receives editable, source-bound expression with separately
qualified mechanical, semantic, rights and delivery standing. Media owns the
representation and production contract, not source-domain truth, physical
execution, equipment installation, artifact retention or human approval.
Reality: mature native tools already carry editorial, rendering, conversion and
measurement. Do not reimplement their algorithms. Native TTML wrapper and mise
configuration drift was invisible to the old three-file Agent plan (Host #32674,
job-01a21493-e50f-7587-aea3-9bee088eb5e9). Previous candidates have not yet
received final remote qualification at the starting read.
Change: replace entry-only identity with an explicitly selected finite local
source closure; reuse native Runtime dependency commitments. Preserve the entry
adapterDigest and public argument compatibility.

## Thought LEGO and source/consumer map
Use representation-first, formal-first, half-open rational time, exact byte
identity, UNKNOWN distinct from FALSE, natural owner, independent falsification,
and DELETE-CUSTOM -> REUSE -> COMPOSE. No mandatory new directories or brokers.

| Logic (18 questions, grouped into 13 responsibility domains) | Existing capability carrier | Consumer / boundary |
|---|---|---|
| L01 intent/audience/narrative | production_context, MEDIA.md/STUDIO.md | Production purpose, not domain truth |
| L02 source and claims | production_source_io, models, production_validation | traceable bounded claims |
| L03 medium/visual grammar/identity | creative_index, identity, visuals, Remotion, preview | editable observer-facing expression |
| L04 asset selection/rights | assets, editorial_asset_binding, cloudflare_r2 | exact selected Blob; rights separate |
| L05 production state | models, operation_impact | state and invalidation |
| L06 editorial | native OTIO | interchange and time ranges, not NLE state |
| L07 timed text | timed_text, ttconv, FFprobe | precise delivery mechanics |
| L08 equipment | equipment_discovery/capabilities/evaluation/plan/delivery | Workstation readiness and owner effect |
| L09 processing | agent_processing, native probe scripts | Runtime execution and raw observations |
| L10 perception | perception*, rich_perception* | observations, not semantic acceptance |
| L11 quality | qc, video, review, native profiles | technical vs perceptual review |
| L12 impact/delivery | operation_impact, runtime_receipt_validation, Artifact | exact recipient and independent acceptance |
| L13 learning/research (cross-cutting) | learning_context, research/trial_ledger (PG), observatory, ecology | reproducible learning, not source truth |

External reference paradigms: [OTIO time ranges](https://opentimelineio.readthedocs.io/en/latest/tutorials/time-ranges.html),
[FFprobe structured observations](https://ffmpeg.org/ffprobe.html),
[DTCG 2025.10](https://www.w3.org/community/reports/design-tokens/CG-FINAL-format-20251028/),
[SLSA provenance](https://github.com/slsa-framework/slsa/blob/main/spec/build-provenance.md).
These motivate bounded representation, native measurement, interoperable tokens,
and consumer-verified subject identity; no full compliance claim.

## P0 — selected local native source closure (V11 refinement)
I = profile ID, expected profile/entry adapter digests, optional expected local
closure digest, optional selected input digest, input path, evidence directory.
O = proposal with declared owner-local file closure, selection standing, and
native Runtime commitments when explicitly selected or input-bound.
S = source-owned immutable byte observations within each discovery, no global
cache, no additional registry. Scope = profile + adapter + applicable owner
mise/.python-version and TTML wrapper. Canonical digest = SHA256(compact
key-sorted JSON of versioned relative-path/digest rows, path sorted).
pre = supported exact profile, entry adapter, complete declared local source
set; selected digest agrees if supplied; selected input digest agrees if supplied.
post = selected local source set preserved, native commitment paths correspond
to observed local files, old API remains usable without claiming caller-selected
closure. inv = missing source not silently accepted; changed wrapper or owner
configuration invalidates previous selected closure even if entry digest is
unchanged; readiness/installed environment/opaque provider reads remain
unobserved. eff = read source; compile proposal, never execute or publish.
c = bounded file count + selected input byte hashing; no NLE or provider install.
epsilon = missing or changed member rejects; a runtime witness is not a proof
of provider consumption; no full transitive installed-environment claim.
prov = discovery source digest, runtime exact Job/Attempt/Artifact readback.
unfold = discovery -> exact selection -> native Runtime witness -> adapter
receipt/raw observation -> actual consumer verification.
Verification: old wrapper/config substitution RED; new stale selection and
missing file reject; compatibility and relocation tests; actual native positive
and stale Runtime admission negative, if execution infrastructure is available.
Model invariants are not universal implementation refinement proofs.

## Remaining work in dependency order
| Priority | Task | Acceptance |
|---|---|---|
| P0 | #2804/#2810/#2813 and new source closure normal integration | exact remote heads, normal CI and merge, no admin |
| P0 | restore original master/narration using existing scoped binding | exact selected Blob hash/size + explicit consumer readback; UNKNOWN until binding exists |
| P1 | explicit complete native gate | all four smoke providers + concurrent fixture isolation + disposable PG; preserve lightweight core |
| P1 | public token consumer | real Web owner reads same versioned artifact, no private imports/duplicate generators |
| P1 | dependency maturity | native compatible providers latest eligible; exact locks for reproduction, no gratuitous manifest pins; coordinate shared pnpm/uv |
| P2 | remove redundant repeated observations | before/after actual consumer parity, scoped measured savings, no global cache |
| P3 | alternative native substrates | MLT/OBS/VMAF/C2PA only when named real consumer and falsifiable demand justify |

All tasks retain independent evidence, natural owner, and UNKNOWN boundaries.
No placeholder media, speculative installations, broad directory migration,
third-party credential search, or unqualified cleanup of peer workspaces.
