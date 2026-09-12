---
name: artifact-work
description: Create, transform, validate, package, or verify digital artifacts such as PPTX presentations, documents/PDF, images, datasets, audio/video, GeoPackage, glTF/3D, and OCI software releases. Use when an artifact must be produced or checked against native standards, target applications, conformance validators, visual/semantic checks, or exact read-back evidence.
compatibility: Requires filesystem access. Executable providers may be exposed through MCP, CLI, APIs, local applications, or workflow systems; some target validation requires Windows/PowerPoint or specialist validators.
metadata:
  source-authority: ordivon-artifact-v2
  source-revision: 39b6281b9b59c5d9d372a04e36f845758a7c93cf
  migration-generation: ordivon-next-r1
---

# Artifact work

Use mature native formats, standards, tools, and validators. Do not invent an Ordivon document/media AST, package format, transport protocol, validator, or workflow engine when a mature owner exists.

## Workflow

1. **Define the artifact outcome.** Identify the artifact family, intended purpose, required outputs, target consumers, and what evidence will count as acceptance.
2. **Load only the relevant family reference.** Use the table below. Do not load unrelated family references into context.
3. **Discover executable capabilities in the current environment.** Inspect available MCP tools, harness tools, CLI/API providers, applications, and existing workflows. A provider listed in a reference is prior evidence, not proof that it is available now.
4. **Build the smallest sufficient working set.** Prefer deterministic programs for deterministic work and Agent reasoning only where semantic judgment or adaptation is required.
5. **Create or transform native artifact bytes.** Preserve exact source/material identities where they matter.
6. **Verify with independent evidence.** Run the native format/conformance checks required by the selected profile, then target/native-consumer, visual, semantic, accessibility, security, or read-back checks when applicable.
7. **Do not promote partial success.** Process exit, file creation, package creation, or one validator passing is not overall Artifact acceptance.
8. **Add durability, packaging, and trust only when required.** Temporal, OCI/ORAS, Sigstore, in-toto/SLSA, OPA, or similar providers are optional working-set capabilities, not mandatory Artifact layers.
9. **Keep external publication separate.** Upload/publish/provider effects belong to the applicable Distribution/provider capability and its own authority/read-back rules.
10. **Return bounded standing and evidence.** State exactly what passed, what remains unverified, and which evidence supports the result.

## Family references

- Presentation / PPTX / PowerPoint: [references/presentation.md](references/presentation.md)
- Still image / PNG: [references/still-image.md](references/still-image.md)
- Dataset / Parquet: [references/dataset.md](references/dataset.md)
- Audio / FLAC: [references/audio.md](references/audio.md)
- Moving image / Matroska + FFV1: [references/moving-image.md](references/moving-image.md)
- Geospatial / GeoPackage: [references/geospatial.md](references/geospatial.md)
- Design / 3D / glTF: [references/design-3d.md](references/design-3d.md)
- Software release / OCI image: [references/software-release.md](references/software-release.md)

If the requested family is not covered, use external standards and mature tools to establish a new bounded profile first. Do not widen an existing profile by analogy.

## General acceptance rules

- Native/provider formats remain authoritative where possible.
- `execution succeeded` does not imply `artifact requirement satisfied`.
- A conforming format can still fail an object-specific contract.
- A target application opening a file does not replace structural/conformance validation.
- Accessibility, visual quality, security, and human usability are independent evidence surfaces when applicable.
- External tool identity is replaceable; preserve capability requirements and evidence semantics rather than vendor lock-in.
- Do not weaken a profile merely because a required validator or target environment is unavailable. Report the missing capability explicitly.
