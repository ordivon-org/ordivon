# Presentation / PPTX reference

## Bounded proven profile

- Family: presentation
- Native representation: OOXML PresentationML / PPTX
- Standard lineage: ISO/IEC 29500
- Prior standing: `LIVE_PROVEN_BOUNDED`

## Prior proven providers

- `ppt-master 6.4.0` at pinned commit `7879bbc811f86ed9e43df0053169d885cff942c7` — replaceable high-fidelity presentation authoring provider for semantic-SVG/design work and native editable PPTX export; use the local `ppt-master` authoring Skill as the bounded procedural adapter
- `python-pptx 1.0.2` — native OOXML authoring adapter for deterministic native composition
- `DocumentFormat.OpenXml OpenXmlValidator 3.5.1` — OOXML structural validation
- Microsoft PowerPoint Desktop 16.0 — native target open/render/PDF/PNG acceptance
- `qpdf 12.3.2` — ordinary PDF structural check
- digest-bound visual review — target-render visual acceptance
- destination read-back SHA-256 — exact delivered-byte identity

Treat these as prior evidence. Discover current providers before execution. `ppt-master` authoring success is not presentation acceptance; this profile remains the acceptance owner.

## Typical target-verified composition

For `verify-pptx-in-powerpoint` or equivalent:

1. construct/edit native PPTX;
2. validate OOXML structure;
3. open/render in the required PowerPoint target;
4. export and bind target PNG/PDF outputs if required;
5. perform required visual/semantic checks;
6. verify destination read-back when delivery is part of acceptance.

Optional, only when the task requires it: Temporal durability; OCI/ORAS packaging; Sigstore/in-toto/SLSA trust; OPA release policy.

## Boundaries

- OOXML structural PASS != PowerPoint target-render PASS.
- PowerPoint target PASS != accessibility PASS.
- Artifact release readiness != external publication/provider acceptance.
- Do not create a universal presentation/document AST.

## Source evidence

- `/root/projects/ordivon/capabilities/artifact/docs/SOURCE_AUTHORITY_ACCEPTANCE_20260912.md`
- `/root/projects/ordivon/capabilities/artifact/docs/artifact-build-delivery-e2e-v1-r1-status.md`
