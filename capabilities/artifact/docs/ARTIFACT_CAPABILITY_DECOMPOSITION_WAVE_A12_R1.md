# Artifact Capability Decomposition — Wave A12 R1

## Standing

GENERIC_ARTIFACT_OPERATION_SOCKET_EXTRACTED_TEMPORAL_ADAPTER_THINNED

Wave A12 introduces a stable Artifact operation contract and moves exactly-once receipt fencing plus current Delivery/OCI CLI mapping out of the Temporal support layer.

## One-sentence boundary

Artifact Operations owns operation envelopes, immutable input/output commitment fencing, replay-safe local receipts, and provider substitution; Temporal owns durable sequencing/retry/waiting only, while Artifact semantic owners and replaceable providers own build/verify/trust/package behavior.

## New package

artifact_operations now contains:

- contract.py — operation envelope and public trust-material contract;
- receipt.py — generic exactly-once local receipt fence;
- executor.py — stable operation executor over a replaceable provider;
- providers/delivery_cli.py — current compatibility provider mapping stable operations to the historical Delivery and OCI CLIs.

## Stable operation envelope

The generic envelope has schemaVersion 1, kind ordivon.artifact-operation, operationId, operationKind, inputs, and options.

Current bounded operation kinds are prepare, build, verify, verify-trust, and package.

This vocabulary is independent of Temporal activity naming and independent of CLI flags.

## Receipt fence ownership

Generic receipt fencing now lives in artifact_operations.receipt.

It owns:

- deterministic operation key derivation from operationKind plus operationId;
- exclusive local lock acquisition;
- abandoned-attempt cleanup when no receipt commit marker exists;
- exact immutable-input identity checks on replay;
- exact output digest/size checks on replay;
- deterministic operation-directory roles;
- atomic receipt commit;
- replay result reconstruction.

Its result kind is ordivon.artifact-operation-result and receipt kind is ordivon.artifact-operation-receipt.

The fence has no knowledge of profiles, builders, verifiers, trust policy, OCI, or Temporal.

## Replaceable provider seam

The current compatibility implementation is artifact_operations.providers.delivery_cli.DeliveryCliOperationProvider.

Only this provider contains the legacy CLI vocabulary such as compile-request, build-request, verify-stage, aggregate-vsa-gates, OCI package flags, artifact_delivery.py, and artifact_oci_package.py.

This is intentional. It establishes a replaceable socket without forcing A12 to simultaneously rewrite all remaining CLI/facade behavior.

A later provider can call Python owners directly without changing Temporal or receipt semantics.

## Temporal adapter

scripts/artifact_delivery_temporal_support.py is now a compatibility adapter.

It no longer owns subprocess execution, fcntl receipt fencing, CLI command construction, or operation receipt implementation.

Historical methods prepare/build/verify/verify_trust/package remain so existing Temporal activity names and workflow-history shape are not needlessly changed in A12. Each method now translates its historical activity payload into an ordivon.artifact-operation envelope and delegates to ArtifactOperationExecutor.

This preserves current Temporal workflow activity names while changing the internal execution socket.

## Temporal history boundary

A12 deliberately does not rename existing Temporal activities or the workflow name. Doing so without explicit Temporal workflow versioning could create replay compatibility risk for in-flight histories.

Therefore A12 changes the activity implementation boundary, not durable workflow history identifiers.

A future migration may introduce a single generic operation activity only with explicit workflow versioning/migration evidence.

## Trust material

Public trust-material envelope validation now belongs to artifact_operations.contract and remains secret-rejecting before durable history.

Provider-side exact trust file verification remains in the provider because it binds physical files immediately before execution.

## Compatibility surface

ReceiptFencedArtifactExecutor remains in scripts/artifact_delivery_temporal_support.py as a thin adapter for existing callers/tests.

Its methods construct generic operation envelopes and delegate to ArtifactOperationExecutor. The support file retains compatibility aliases for operation_key and file_fact and the existing CLI diagnostic helper route, but no longer implements the CLI or receipt fence.

## Verification evidence

A12 tests were written before implementation and observed RED because artifact_operations did not exist, Temporal support owned receipt fencing and CLI vocabulary, there was no stable operation envelope, and no replaceable provider boundary existed.

After extraction:

- A12 decomposition tests: 6 PASS;
- generic executor build replay: PASS;
- Temporal durability contract: 12 PASS;
- A2–A12 plus OpenXML environment plus OCI targeted bundle: 76 PASS;
- full Artifact regression: 377 tests, 0 failures, 4 conditional skips;
- compileall: PASS;
- git diff --check: PASS before the final commit gate.

Candidate full-regression Runtime Job: job-01a0b3b9-16d7-7712-86ba-0b42c66bfb69.

## Measured boundary shift

The historical scripts/artifact_delivery_temporal_support.py shrank from approximately 228 lines to 115 lines.

A forbidden-vocabulary census on that support file returns no subprocess, fcntl, compile-request, build-request, verify-stage, aggregate-vsa-gates, OCI package flags, or Delivery CLI path constants.

Those current compatibility details are isolated in the replaceable delivery_cli provider.

## Architectural standing after A12

The dependency direction is now:

Temporal workflow -> Temporal compatibility adapter -> ArtifactOperationExecutor -> ReceiptFence + replaceable provider.

The current provider still maps operations to the legacy Delivery/OCI CLI. That remaining dependency is intentionally localized rather than hidden.

The next bounded wave should be A13: replace the legacy Delivery CLI provider with direct Python owner composition and reduce scripts/artifact_delivery.py toward a true CLI/compatibility facade, without changing the ArtifactOperation or Temporal contract.
