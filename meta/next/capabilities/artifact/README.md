# Artifact capability family

Artifact is not one permanent Ordivon subsystem. It is a contextual set of capabilities for creating, transforming, validating, packaging and handing off digital artifacts.

Current source provider: `/root/projects/ordivon/capabilities/artifact`.

Load only the capability families needed by the task:

- family/profile knowledge;
- authoring/build adapter;
- structural/conformance validator;
- target/native-consumer validator;
- visual/accessibility/QC evidence producer;
- package/trust capability;
- durable orchestration when required;
- distribution handoff when an external effect is required.

The active set may differ completely between PPTX, PDF/UA, PNG, GeoPackage, glTF, OCI software release or WARC tasks.


## Agent-facing entry point

Procedural discovery now uses the Agent Skills open format at `.agents/skills/artifact-work/`. This file is descriptive only; do not build a second Artifact skill registry here.
