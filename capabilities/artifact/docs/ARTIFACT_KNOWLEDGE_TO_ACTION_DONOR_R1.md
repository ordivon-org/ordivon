# Artifact → Knowledge-to-Action Donor R1

## Standing

`DONOR_REFERENCE_NOT_CORE_ONTOLOGY`

This donor freezes the reusable knowledge produced by Artifact taxonomy/profile work without promoting the Artifact subsystem itself into the future Ordivon Core.

It is intentionally a **migration reference**, not a new universal ontology and not a runtime cutover.

## Source boundary

The donor is extracted from Artifact state at base revision:

`e38fa2b3ccf9200406595bdc744267c8faf3895c`

Its two primary semantic source authorities are digest-bound in the manifest:

- `artifact-delivery/taxonomy-v1.json`;
- `artifact-delivery/shadow-v2/profile-v2-mapping-manifest-r1.json`.

Every referenced profile, object-contract schema, live capability binding, isolated validator implementation and explicitly excluded infrastructure file is also SHA-256 bound.

## Coverage

R1 proves extraction coverage for:

- 15 taxonomy families;
- 15 represented families;
- 24 normalized profile-v2 entries;
- 16 live-proven shadow capability bindings;
- 16 isolated profile validator implementations across 10 standards-first families.

The donor therefore covers all currently operational Artifact families without requiring a new Artifact-specific runtime or ontology.

## Migration classes

### `DIRECT_REFERENCE`

Use when the existing knowledge can be indexed or relocated without changing its meaning:

- artifact classification facts;
- external standards references;
- evidence requirements/claims;
- `nonClaims` / result boundaries.

### `SEMANTIC_MAPPING`

Use when the existing object should survive, but its current Artifact schema must not be mistaken for a universal Core schema:

- object contracts;
- capability bindings;
- validation mappings.

These are candidates for future Common Contracts only after cross-domain pressure testing.

### `DO_NOT_PROMOTE`

Keep as replaceable execution/provider integration or historical implementation, not as Core ontology:

- legacy Artifact delivery orchestration;
- Temporal Artifact execution wiring;
- OCI package/release adapter;
- R2 mailbox transport implementation;
- toolchain doctor/environment probing.

## Per-profile donor model

Each normalized profile exports only the following bounded migration view:

```text
candidateProblemKey
classification
standards
targetAuthorities
objectContract reference
capabilityBinding reference
validatorImplementation reference
validationMapping
compositionCandidate
resultBoundary
migrationDisposition
```

`candidateProblemKey` is deliberately just a lookup key:

```text
artifact/<family>/<profile-id>
```

It is **not** a declaration that the future Ordivon Core must use this taxonomy or key shape.

## Composition boundary

The current Artifact profiles encode applicable tools/authorities and required evidence, but they do not universally encode a complete execution sequence.

Therefore every donor composition candidate carries:

`sequencing = NOT_ENCODED_DO_NOT_INFER`

This prevents the migration from inventing workflows that were never proven by the source.

Known compositions should be promoted later only when actual execution history or a domain method provides enough evidence for ordering and applicability conditions.

## Evidence history

The donor does not duplicate live proof data. Instead it retains exact references to each `LOCAL_LIVE_PROVEN` binding, including its proof keys and complete digest-bound source file. This preserves evidence history while avoiding a second source of truth.

## Preserved migration gaps

The donor records current absences rather than fabricating replacements:

- **14/24** profiles have an explicit object contract; **10/24** do not.
- **16/24** profiles have explicit `nonClaims`; **8/24** do not.
- **0/24** profiles encode a universal execution sequence; all 24 remain `NOT_ENCODED_DO_NOT_INFER`.

These are migration observations, not defects automatically repaired by the donor. In particular, the older production-v1 lineage should not be retroactively assigned epistemic boundaries or object contracts that were never actually proven.

## Validator boundary

Ten newer standards-first families now expose sixteen isolated profile-validator implementations: Audio has independent FLAC, RIFF/WAVE PCM, and Ogg/Vorbis profiles; Still Image has separate PNG and static SVG profiles; Design/2D has independent Tiled-native map and Workstation-managed Aseprite derivative validators. These are preserved as candidate validator capabilities:

- Dataset;
- Still Image;
- Audio;
- Moving Image;
- Geospatial;
- Design / 2D;
- Design / 3D;
- Software Release;
- Web Archive;
- Message.

The mixed legacy `scripts/artifact_delivery.py` is explicitly **not** promoted as a validator implementation because it combines production orchestration, compatibility and historical Artifact mechanics.

## Verification

Runtime regression job:

`job-01a09ab6-8a63-7823-a825-7bcd0c344321`

Final matrix:

- donor focused tests: **10/10 PASS**;
- full Artifact tests: **275 total / 273 PASS / 2 existing conditional skips / 0 failures**.

The exact verification receipt is frozen in `artifact-delivery/donor-r1/verification-r1.json` and binds the donor manifest SHA-256 plus the Runtime operation digest.

## What this proves

Artifact can now donate reusable assets in the form:

```text
Problem-class candidate
        ↓
Standards / domain knowledge
        ↓
Capability references
        ↓
Validation mapping
        ↓
Evidence requirements
        ↓
Result boundary
```

without donating:

```text
Artifact Runtime
Artifact scheduler
Artifact-specific workflow authority
Temporal wiring
transport implementation
legacy subsystem identity
```

This is the desired migration direction:

> Preserve proven knowledge; discard accidental infrastructure ownership.

## What this does not prove

R1 does **not** prove that Artifact's classification axes are universal Ordivon Core objects. It also does not prove that a profile is itself a reusable workflow, that all production-v1 profiles have adequate `nonClaims`, or that Game/Research/Software domains will accept the same Common Contracts unchanged.

Those questions belong to later cross-domain extraction and pressure testing.
