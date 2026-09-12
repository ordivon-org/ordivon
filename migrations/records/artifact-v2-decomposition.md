# Artifact v2 decomposition — new Ordivon model

Source authority observed: `/root/projects/ordivon-artifact-v2@e06b17a517c4`

## Migration standing

### Historical Workstation -> Artifact v2

**Complete.** Artifact v2 is the accepted forward source authority. The historical Workstation-owned Artifact implementation was removed after differential execution and post-retirement Temporal proof. Git history remains provenance only.

### Artifact v2 -> Ordivon Next working-set model

**Partially complete.** The provider is registered, but the old `Artifact Build & Delivery E2E` identity still bundles several capability families that should be addressed independently in the new model. No implementation move is required yet.

## Decomposition

### 1. Artifact knowledge/profile catalog

Role: task-local knowledge, standards and acceptance profiles.

Current source material includes:

- artifact family taxonomy;
- Presentation/OOXML profiles;
- fixed-document/PDF profiles;
- still image;
- audio;
- moving image;
- dataset;
- geospatial;
- design/3D;
- software release;
- web archive;
- message;
- object contracts and target-authority concepts.

New-model treatment: **MIGRATE_KNOWLEDGE progressively.**

These are not one universal Artifact ontology. Each family should retain its native standards and validators.

### 2. Authoring / build adapters

Role: turn approved source/material into native artifact bytes.

Examples currently include:

- `python-pptx` for PresentationML;
- Pandoc for DOCX/text-document paths;
- XlsxWriter for XLSX;
- format-family scripts for image/audio/video/dataset/geospatial/3D/message/web archive;
- exact template/media bindings for presentation migration.

New-model treatment: **REGISTER CAPABILITIES**, not Core. Writers/converters remain replaceable providers.

### 3. Validators / evidence producers

Role: establish bounded conformance or acceptance facts.

Examples include:

- DocumentFormat.OpenXml `OpenXmlValidator`;
- qpdf;
- veraPDF;
- Nu Html Checker;
- Playwright/browser targets;
- axe;
- ImageMagick/libvips matrices;
- GDAL/GeoPackage validator;
- Khronos glTF validator;
- Syft/Trivy and software-release checks;
- target-render and destination read-back checks.

New-model treatment: **REGISTER VALIDATOR CAPABILITIES** individually or by family. Validator output remains native evidence where possible.

### 4. Target environments / native consumers

Role: validate behavior in the real consumer environment.

Examples include Microsoft PowerPoint Desktop, browsers, independent decoder matrices and standard validators.

New-model treatment: **REGISTER TARGET/VALIDATION CAPABILITIES**. They are not Artifact-owned runtime infrastructure.

### 5. Release package / trust envelope

Current mature owners:

- OCI 1.1 + ORAS for content-addressed package/relationship mechanics;
- in-toto + SLSA for provenance/verification statements;
- Sigstore for signature/trust bundles;
- OPA/Rego for explicit release policy.

Artifact-specific residual: profile requirements and the mapping from exact evidence/trust facts to artifact release readiness.

New-model treatment: mature package/trust mechanisms remain external capabilities; retain only profile-specific mappings and evidence relationships.

### 6. Durable orchestration

Current mature owner: Temporal.

Artifact currently supplies activities/adapters for prepare/build/verify/trust/package, but Temporal owns ordering, retries, cancellation and recovery.

New-model treatment: **Temporal is loaded in the working set when durability is needed.** Artifact does not own a scheduler/workflow engine.

### 7. Input transport and external distribution

Input byte authority/materialization uses Runtime or provider-native mechanisms where appropriate. Artifact must not invent a file-transport protocol.

External publication/provider effects belong to Distribution/provider APIs and require their own authority/read-back semantics.

New-model treatment: **outside Artifact capability family except for interface requirements.**

## What remains genuinely Artifact-specific

After decomposition, the durable Artifact-specific value is much thinner:

1. classify the artifact family and purpose;
2. select native standards/profile requirements;
3. select suitable authoring/build capabilities;
4. define required validation/target/read-back evidence;
5. bind exact source/material/output/evidence identities;
6. determine profile-scoped artifact standing/release readiness from those facts.

Everything else should stay with mature providers.

## Current migration verdict

Artifact is **not yet fully migrated into the new working-set model**, but its old Workstation migration is complete and its current v2 architecture is already close enough that no clean-room rebuild is justified.

Next action: extract family taxonomy/profile metadata and validator/capability records incrementally from the existing source authority while leaving the live Artifact worker and toolchain in place.
