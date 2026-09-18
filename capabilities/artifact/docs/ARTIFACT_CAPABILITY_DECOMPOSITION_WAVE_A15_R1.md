# Artifact Capability Decomposition — Wave A15 R1

## Standing

MANIFEST_DRIVEN_FACADE_REDUCTION_COMPLETE_DROP_GATES_SATISFIED

Wave A15 executes the A14 compatibility-retirement manifest instead of rediscovering the architecture.

## One-sentence boundary

A15 moves the remaining Presentation reference-projection and material-snapshot implementations to canonical owners, converts request/build/verify/presentation entrypoints into thin owner delegates, satisfies all ten A14 private DROP gates, and preserves every supported Delivery CLI verb and compatibility name.

## A14 contract executed

A14 froze 51 live top-level Delivery callables with five target dispositions.

A15 implements the bounded work authorized by those retirement gates:

- move Presentation OPC/reference projection implementation;
- move material snapshot implementation;
- thin request/plan/build/verify compatibility entrypoints;
- expose DirectPython presentation compatibility services;
- delete the ten private wiring helpers whose gates become satisfied;
- keep all 20 CLI verbs.

A15 does not remove a supported CLI command or public compatibility name merely to reduce line count.

## Presentation reference projection owner

New module:

artifact_capabilities/presentation/reference_projection.py

It owns:

- normalized POSIX relative-path validation;
- normalized SHA-256 commitment validation;
- safe ZIP member-name checks;
- OPC relationship-base and target resolution helpers;
- exact parent-package identity binding;
- exact member digest/size fencing;
- replay-safe projected output behavior;
- project_opc_members;
- compose_reference_hybrid_source.

The module consumes Core file facts and Core JSON validation directly and does not import artifact_delivery.

Delivery retains project_opc_members and compose_reference_hybrid_source as thin compatibility/CLI delegates.

The existing eight-test OPC projection contract continues to pass through those Delivery wrappers, while A15 also adds a direct-owner exact-projection smoke test.

## Artifact Evidence snapshot owner

New module:

artifact_evidence/snapshot.py

It owns:

- utc_now;
- snapshot_materials;
- exact material file facts;
- immutable-input snapshot timestamping and boundary note.

Delivery retains snapshot_materials as a two-line compatibility delegate because the snapshot CLI verb remains supported.

utc_now no longer exists in Delivery.

## DirectPython compatibility services

DirectPythonOperationProvider now exposes public composition methods for:

- build_presentation_source;
- build_semantic_svg_presentation_source;
- verify_document_dependencies.

Existing methods already own:

- validate_delivery_request;
- compile_delivery_plan;
- execute_build_stage;
- execute_verify_stage.

Delivery now delegates these compatibility entrypoints directly to DirectPythonOperationProvider.

This removes duplicated admission/build/verification wiring from the facade while preserving existing return contracts.

## Ten A14 DROP gates satisfied

The following private Delivery wiring functions were removed after their A14 retirement gates became true:

- _selected_external_file
- _presentation_build_hooks
- _resolve_request_path
- _admit_presentation_source
- _admit_semantic_svg_source
- _primary_suffix
- _request_output_name
- _document_dependency_hooks
- _document_dependency_stage_verifier
- _verification_stage_hooks

Their behavior remains available through canonical owners and DirectPython provider composition.

## Additional moved private implementation

The following implementation helpers also leave Delivery with their owner migration:

- utc_now
- _normalized_posix_relative
- _normalized_sha256
- _safe_zip_names
- _relationship_base
- _resolve_relationship_target

They are recorded in the retirement manifest as A15 retired/moved symbols.

## Compatibility manifest after A15

The machine-readable authority remains:

artifact-delivery/compatibility-retirement-manifest-v1.json

Post-A15 live Delivery surface:

- 35 live top-level callables;
- 20 CLI verbs;
- 20 retired symbols recorded across A14 and A15.

Current live dispositions:

- KEEP_COMPAT_WRAPPER: 30
- KEEP_CLI: 4
- DEPRECATE: 1

There are no remaining MOVE_TO_OWNER or DROP live entries from the A14 plan.

The one remaining DEPRECATE seam is _delivery_trust_toolchain_config, retained for historical mutable Delivery-local Cosign constant compatibility.

## Historical architecture-test migration

A15 intentionally deletes the Delivery-local verification hook factory. Older A7/A8/A9/A10 tests had frozen the source location of verify-stage wiring.

Those tests were updated to assert the current canonical authority:

artifact_operations/providers/direct_python.py

They still check direct binding to Document, PDF, OpenXML, and Web verifier owners; they no longer require retired wiring to remain in the Delivery facade.

No production behavior was changed to satisfy those stale textual assertions.

## Dependency standing

Production Python imports of artifact_delivery remain zero.

Current production Delivery dependencies remain explicit CLI edges only:

- scripts/artifact_agent_surface.py
- scripts/artifact_delivery_toolchain_doctor.py
- artifact_operations/providers/delivery_cli.py as explicit legacy fallback

Default Runtime/Temporal execution remains:

Temporal -> ArtifactOperation -> DirectPythonOperationProvider -> canonical owners

## Delivery facade size

Line-count trajectory:

- decomposition start: approximately 3922
- A2: 3458
- A3: 2822
- A4: 2242
- A5: 2028
- A6: 1737
- A7: 1616
- A8: 1546
- A9: 1520
- A10: 1442
- A11: 1408
- A12: 1408
- A13: 1197
- A14: 1180
- A15: 750

A15 removes approximately 430 lines from the Delivery facade while preserving its supported names and CLI surface.

Relative to the original approximately 3922-line monolith, Delivery is reduced by approximately 80.9 percent.

## Verification evidence before final gate

A15 decomposition tests: 8 PASS.

Legacy Delivery: 79 tests, 0 failures, 2 conditional skips.

OPC projection compatibility suite: 8 PASS.

Temporal durability contract: 12 PASS.

A2–A15 plus OpenXML environment plus OCI targeted bundle: 97 PASS.

Full Artifact regression: 398 tests, 0 failures, 4 conditional skips.

Candidate full-regression Runtime Job:

job-01a0b3f5-aa0f-75d0-895c-14664cdcb70d

compileall and git diff --check remain required in the fresh completion gate.

## Architectural standing after A15

The major implementation extraction program is effectively complete.

scripts/artifact_delivery.py is now predominantly:

- CLI parser/dispatch;
- thin compatibility wrappers;
- Trust compatibility seam;
- a small set of compatibility aliases/constants.

The next wave should not restart broad decomposition.

A16 should be a narrow endgame review around:

1. the single DEPRECATE seam _delivery_trust_toolchain_config;
2. whether CLI parser/dispatch should become a dedicated CLI module without changing the script entrypoint;
3. whether legacy Python compatibility wrappers need an explicit deprecation/version policy;
4. whether DeliveryCliOperationProvider should remain indefinitely as a fallback or receive a retirement condition;
5. final minimality and dependency-cycle audit.

A16 should optimize final architecture clarity rather than line count.
