# Artifact Profile v2 — Shadow R1

## Standing

`SHADOW_SCHEMA_PROVEN`

Full Artifact regression after Design/3D pressure testing: **206 tests, 204 PASS, 2 existing conditional skips, 0 failures**.

Profile v2 is a shadow compatibility model. It does **not** replace `profile-v1.schema.json`, change Temporal routing, alter existing release gates, or authorize a production cutover.

Its purpose is narrower: prove that the taxonomy correction discovered through Office/PDF, Still Image and Dataset can be represented without losing existing production semantics and without creating a universal Artifact AST.

## Why v2 exists

Profile v1 was successful for its original bounded scope but its top-level `artifactClass` mixed different axes:

- `presentation`, `document`, `spreadsheet`, `web` behaved like artifact families;
- `fixed-view` was a representation;
- `accessible` was a purpose/conformance concern;
- `archive` represented a preservation purpose/profile.

Extending that enum to images, datasets, geospatial, media, 3D and software releases would preserve the category error.

Still Image and Dataset supplied the missing falsification pressure:

- Still Image requires format/profile facts, metadata observation and independent decoder evidence, but normally no artifact-instance schema contract;
- Dataset requires a reusable format/family profile **plus** a separate object-specific Dataset Contract and independent reader evidence.

The common waist is therefore not `artifactClass` and not a universal content model.

## v2 common core

`artifact-delivery/profile-v2.shadow.schema.json` contains only the cross-family structure that survived the current evidence:

```text
Profile v2
├─ classification
│  ├─ family
│  ├─ representation
│  ├─ format / media type
│  ├─ optional conformance profile
│  └─ purposes
├─ construction (optional)
├─ outputs
├─ targetAuthorities
├─ objectContract (optional)
├─ requiredEvidence
├─ profilePolicy
├─ deliveryDefaults
├─ nonClaims
└─ notes
```

### `classification`

The old overloaded class is replaced by orthogonal fields. `accessible` and `archive` are not legal families.

### `outputs`

Primary and companion outputs remain explicit. This preserves v1's distinction between an editable authority artifact and delivery companions such as PDF.

Exactly one primary output is a semantic invariant layered on top of JSON Schema.

### `targetAuthorities`

A target can be a native consumer such as Microsoft PowerPoint Desktop or an independent implementation matrix such as the Still Image decoder pair or Dataset reader pair. Tool choice itself remains outside the profile in capability bindings.

### `objectContract`

This field is optional by design.

Dataset R1 proves a case where it is mandatory: concrete columns, nullability and keys are instance/object-specific and must not become a global family profile. Still Image R1 proves that many artifact profiles do not need such a contract.

### `requiredEvidence`

The schema does not enumerate all future gates. Each family/profile declares named evidence claims with `required=true/false` and profile-specific parameters.

This preserves existing v1 gate truth values while allowing image/data/geospatial/media evidence to remain native to those domains.

### `profilePolicy`

Format/domain-specific policy stays here instead of inflating the common schema:

- PowerPoint aspect ratio, fonts and semantic/render policies;
- PDF conformance settings;
- PNG chunk/colour restrictions;
- Parquet flat-type and row-order policy;
- future OGC/SMPTE/Khronos rules.

The common schema intentionally does not understand those structures.

Geospatial R1 subsequently pressure-tested this boundary with CRS, geometry type, GeoPackage container rules and OGC conformance. It required no new common axis. It did force two useful generalizations: `objectContract` is generic rather than Dataset-specific, and `standard-validator` is a first-class target authority alongside native consumers and independent implementation matrices.

Audio R1 then added codec/container/decoded-content identity pressure without changing the common schema: native FLAC format policy stayed profile-specific, the exact sample-rate/channel/sample-count/PCM identity stayed in the object contract, and independent decoder agreement remained ordinary evidence under an implementation matrix.

Moving Image R1 added a second codec/container case with a different evidence topology: MediaConch supplies specialist implementation-check evidence, MediaInfo/FFprobe bind technical facts, and decoded-frame identity remains in the object contract. Its clean FFV1 checker can execute zero positive tests, which is retained as a profile-specific non-claim rather than requiring a new global schema field.

Software Release R1 adds software-supply-chain pressure without changing the common schema: final OCI manifest identity and container policy stay profile-specific, platform/rootfs/runtime/security expectations live in the object contract, and SBOM/vulnerability/secret/runtime observations remain evidence. Generic SLSA/in-toto/Sigstore trust remains outside the family profile in the common release envelope.

Design/3D R1 adds scene/mesh and consumer-coordinate pressure without changing the common schema. Khronos conformance remains a standard-validator authority, scene topology/bounds remain object-contract facts, and Blender coordinate conversion remains consumer-specific evidence rather than a new global coordinate field.

## Differential mapping proof

`scripts/artifact_profile_v2.py` maps both:

- all current production `profile-v1` examples;
- the standards-first Still Image and Dataset shadow profiles.

The generated mappings live in:

`artifact-delivery/shadow-v2/examples/`

and are digest-bound in:

`artifact-delivery/shadow-v2/profile-v2-mapping-manifest-r1.json`.

R1 currently maps **15 profiles**: eight production v1 profiles plus seven standards-first shadow profiles (Still Image, Dataset, Geospatial, Audio, Moving Image, Software Release and Design/3D).

For every production v1 profile, differential tests verify preservation of:

- ID;
- construction authority mode and locale;
- primary and companion outputs;
- editable/required output facts;
- primary and secondary native targets;
- required/disabled gate truth values;
- delivery defaults;
- unsupported target declarations;
- presentation aspect ratio, font policy, exact font declarations, semantic policy and render evidence;
- PDF conformance policy;
- notes.

The literal old `artifactClass` is not preserved because it is precisely the category error being removed. Its **meaning** is mapped into family/representation/conformance/purpose.

Examples:

```text
accessible
→ family=fixed-document
→ representation=fixed-layout
→ conformanceProfile=PDF/UA-2
→ purposes include accessibility
```

```text
fixed-view
→ family=fixed-document
→ representation=fixed-layout
```

```text
dataset-parquet-flat-r1
→ family=dataset
→ representation=columnar
→ format=Apache Parquet / application/vnd.apache.parquet
→ objectContract required by request digest
```

## Important non-goals

Profile v2 R1 does not:

- normalize artifact content into one AST;
- encode every industry standard into one schema;
- select tools;
- replace capability bindings;
- replace the Artifact request contract;
- move delivery effects into the profile;
- cut production over from v1;
- claim all 14 families are proven.

## Current migration rule

Production remains on v1 until all of the following are true:

1. v2 shadow mappings validate;
2. current v1 semantics are differentially preserved;
3. existing production Artifact regressions remain green;
4. a v1/v2 acceptance-equivalence run is performed on existing Golden artifacts before any cutover.

Therefore `profile-v2.shadow.schema.json` is an evidence-bearing candidate, not a production contract.
