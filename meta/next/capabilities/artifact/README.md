# Artifact capability family

Artifact is not one permanent Ordivon subsystem. It is a contextual set of capabilities for creating, transforming, validating, packaging and handing off digital artifacts.

Current source provider: `/root/projects/ordivon-artifact-v2`.

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
