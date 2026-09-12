# Package: Artifact

Last census: 2026-09-13
Standing: **READY_FOR_REAL_WORK**

## Outcome scope

Create, transform, validate, package and hand off a digital artifact that the target consumer can actually use.

Artifact is not a universal file-generation engine. Validation is native-family and target specific.

## Mature external knowledge owners

There is intentionally no single Artifact standard. Select the standards of the artifact family and target, for example:

- W3C WCAG 2.2 and applicable accessibility standards for web/digital content;
- PDF/PDF-A/PDF-UA standards for PDF-family requirements;
- OOXML/ODF and application-native rules for office documents where required;
- media/container/codec standards for audio/video;
- geospatial standards for geospatial outputs;
- OCI/SLSA/in-toto and package-manager rules for software release artifacts;
- target platform specifications whenever they are stricter than generic format validity.

## Observed local capability

- `artifact-work` skill;
- accepted Artifact provider knowledge/evidence from `/root/projects/ordivon-artifact-v2`;
- Typst, qpdf;
- FFmpeg;
- ImageMagick;
- Blender;
- Godot;
- GDAL/OGR;
- Syft, Trivy, Skopeo and Cosign for relevant software/container artifact work;
- Python/Node ecosystems for format-specific authoring and validators;
- Runtime for controlled execution.

## Operating rule

Use the artifact-family native toolchain and validators. Do not normalize all documents/media/3D/data/software releases into one Ordivon representation.

A common acceptance pattern is:

`purpose/target -> native family -> author/transform -> structural validation -> semantic/native-target validation -> visual/accessibility checks when applicable -> packaging/trust -> handoff/read-back`

These checks may run in parallel or be omitted when irrelevant; this is not a required lifecycle sequence.

## Concrete current gaps

Only target-specific gaps count. The recent presentation work is a valid acceptance workload because it exposed a real failure class: structurally valid slides can still fail native visual composition/typography/background use. That class should be solved through presentation-native rendering and visual validation, not a new universal Artifact abstraction.
