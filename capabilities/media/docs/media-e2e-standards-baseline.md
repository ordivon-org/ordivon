# Media E2E — external standards baseline R1

Status: Engineering-consumption baseline for the current Media owner. This document does not create a new Media Foundation, source-domain authority, publication authority, or universal Media runtime.

## 1. E2E objective

A mature Media path must make the following chain recoverable and falsifiable for each applicable output profile:

```text
source-owner fence
→ bounded Media/Studio representation intent
→ exact editable/source and Asset identities
→ transform/editorial lineage
→ exact rendered/delivery bytes
→ profile-specific mechanical QC
→ accessibility/provenance/rights evidence applicable to the medium
→ bounded review decision
→ delivery handoff
→ destination/readback evidence owned by the destination/Distribution boundary
```

The output is not mature merely because a file renders, a tool exits zero, or a manifest names a digest.

## 2. Authoritative reference families

These references constrain profile design; they are not all mandatory for every Production.

| Concern | External authority / mature practice | Media admission in R1 |
| --- | --- | --- |
| programme loudness / true peak | ITU-R BS.1770-5 (11/2023); EBU R 128 v5 (11/2023) | **Core measurement semantics.** Acceptance target remains profile-specific. EBU -23 LUFS is a broadcast profile, not a universal web target. |
| prerecorded synchronized-media accessibility | W3C WCAG 2.2, Guideline 1.2 | **Core decision requirement when applicable.** Mechanical caption timing is machine-checkable; semantic caption completeness/audio-description need remain separate review evidence. |
| rich subtitle/caption interchange | W3C IMSC Text Profile 1.3, Recommendation 2026-05-21 | **Conditional delivery profile.** Do not claim IMSC conformance until a produced document is exercised against an appropriate conformance implementation/consumer. |
| editorial cut interchange | Academy Software Foundation OpenTimelineIO | **Retained.** OTIO carries editorial cut data and external media references; it is not treated as a lossless replacement for NLE-private state. |
| finished multi-version AV mastering | SMPTE ST 2067 IMF family | **Conditional.** Admit for finished masters requiring multi-language/territory/version interchange; not required for ordinary web video. |
| still-image descriptive/rights metadata | IPTC Photo Metadata Standard 2025.1 + ISO XMP mapping | **Conditional interoperability profile.** Existing Asset rights/provenance remains owner-local until a real still delivery requires embedded/exchanged IPTC/XMP. |
| verifiable content provenance | C2PA Content Credentials specification 2.4 | **Conditional provenance profile.** Existing digest/provenance records do not imply C2PA credentials. Admit signing/credential machinery only for a real publication/consumer requirement. |
| production/VFX color management | ACES 2 + OpenColorIO | **Conditional color-managed profile.** Screen-first SDR remains Rec.709/sRGB. Admit ACES/OCIO when camera, HDR, EXR, VFX, multi-vendor or archive/remaster requirements produce real pressure. |
| DCC ↔ asset-manager bridge | OpenAssetIO | **Pattern retained, implementation not admitted.** Its bridge-not-database architecture matches Media's boundary discipline, but there is no current multi-host asset-manager duplication requiring adoption. |

Reference roots observed for this baseline:

- https://www.itu.int/rec/R-REC-BS.1770
- https://tech.ebu.ch/publications/r128
- https://www.w3.org/TR/WCAG22/
- https://www.w3.org/TR/ttml-imsc1.3/
- https://opentimelineio.readthedocs.io/
- https://www.smpte.org/standards/st2067
- https://iptc.org/standards/photo-metadata/iptc-standard/
- https://spec.c2pa.org/specifications/
- https://docs.acescentral.com/
- https://opencolorio.org/
- https://docs.openassetio.org/

## 3. Profile-gated acceptance model

### A. Universal Media-owner gates

Every Media projection must preserve OMPC source-authority, standing/currentness, observer, omission/loss, identity, temporal and action boundaries. These gates precede medium-specific production checks.

### B. Studio production gates

When authoring/rendering is actually present, applicable gates include:

1. exact Production and source-owner fence;
2. exact selected Asset/Blob identity and durable byte authority;
3. declared output profile;
4. transform/editorial provenance sufficient to recover the chosen result;
5. profile-specific mechanical QC;
6. explicit rights/attribution standing for selected Assets;
7. accessibility evidence when the medium/audience requires it;
8. review evidence only for unresolved decisions that genuinely depend on perception, meaning, culture or human consequence.

### C. Delivery-boundary gate

Media can prove the package and handoff identity. It cannot promote a local package to externally published/current/accepted merely because delivery was attempted. Platform receipt/readback remains with Distribution/destination authority.

## 4. AV-SDR profile floor

For a bounded prerecorded SDR AV output, the current minimum executable floor is:

- one exact output Blob digest;
- one expected video stream with exact codec/dimensions/rational frame rate/pixel format/color primaries/transfer/matrix/range;
- explicit expected audio presence and, when profile-bound, stream count/index/codec/sample rate/channel count/layout;
- measured programme integrated loudness and true peak using BS.1770-family tooling;
- acceptance loudness/peak thresholds supplied by the output profile, not by a hidden global default;
- exact TimedText source identity when captions/subtitles apply;
- TimedText cues mechanically checked against exact media duration and delivery-lock state;
- semantic caption completeness and audio-description need explicitly evaluated or explicitly left unresolved;
- exact source/transform/provenance/rights lineage.

Current implementation deliberately does **not** equate WebVTT/SRT export with IMSC conformance or WCAG outcome.

## 5. Conditional profile admission

Do not add a technology because it is prestigious. Open a conditional profile only when the Production or downstream consumer presents its trigger:

```text
multi-version finished master        → IMF candidate
camera/HDR/EXR/VFX/multi-vendor      → ACES/OCIO candidate
rich worldwide subtitle interchange  → IMSC candidate
still metadata interchange           → IPTC/XMP candidate
verifiable public provenance         → C2PA candidate
multi-host asset-manager duplication → OpenAssetIO candidate
```

Each admission requires: exact consumer, exact loss/failure if omitted, bounded implementation, executable verification, and a rollback/rejection path.

## 6. R1 golden-chain evidence target

The existing `runtime-introduction` Production is the first bounded AV golden candidate because it already has a revision-bound Runtime source, Claims, Asset/Blob lineage, OTIO snapshots, TimedText, a 78-second selected picture master, 48 kHz narration, and an exact rendered AV candidate.

R1 does not change its `review` standing. The current chain must first prove:

```text
source binding present
+ exact output bytes recoverable
+ output digest re-hashes correctly
+ video/audio profile facts re-probe correctly
+ loudness/true-peak re-measure correctly
+ timed text exactly fits the selected media duration
+ destructive wrong-profile cases reject
+ full repository and optional Resolve-adapter regression remain green
```

Human voice-quality judgment, semantic caption completeness, audio-description need, current external platform acceptance, and current live Resolve-host round-trip remain independent evidence requirements rather than inferred success.

## 7. Non-goals preserved

R1 does not admit:

- Universal Media Framework / Engine / Runtime / SDK;
- a global Media truth database;
- one universal delivery profile;
- one universal loudness target;
- automatic C2PA signing;
- mandatory IMF or ACES for ordinary outputs;
- an assertion that OTIO preserves every Resolve-private effect;
- an assertion that machine caption timing proves accessibility outcome;
- an assertion that local delivery means external publication.
