# Artifact Redecomposition R1 — From Delivery Pipeline to Standing Kernel

## Standing

EVIDENCE_GROUNDED_REDECOMPOSITION_PLANNING_ONLY

This document deliberately restarts architectural decomposition from current repository evidence at source revision 10d0f076c32621f50f7c60ef6f847e19ea2cc9ec.

It is not A16 and it does not authorize production code changes.

The purpose is to stop optimizing historical file boundaries and ask a more fundamental question:

What is the smallest Artifact-specific semantic system that explains both current build/delivery behavior and the newer cross-family verification service without absorbing Runtime, transport, native tool, consumer-domain, or human-preference authority?

## 1. What changed after A1–A15

A1–A15 succeeded at directional decomposition.

Current package-level import analysis finds:

- no strongly connected component with more than one project Python module;
- artifact_core.contracts is the dominant low-level dependency with 29 package-module importers;
- DirectPythonOperationProvider is the largest composition fan-out node with 17 project-module dependencies;
- production Python imports of artifact_delivery are zero;
- scripts/artifact_delivery.py is now 750 lines and primarily compatibility/CLI surface rather than runtime backbone.

Therefore the next architectural risk is no longer the historical Delivery monolith.

The new risks are semantic duplication, orchestration concentration, and boundary drift.

## 2. Intent versus current reality

### 2.1 Repository intent

README.md states that Ordivon should retain thin contracts, format-specific orchestration, evidence binding, trust gates, and durable-workflow integration while mature native formats/tools remain replaceable.

docs/artifact-build-delivery-e2e-v1.md explicitly rejects ownership of generic transport, storage, scheduler, browser, Office, PDF, font, accessibility, provenance standards, and native format semantics.

docs/ARTIFACT_VERIFICATION_SERVICE_R1.md defines a second narrow service: verify exact existing bytes against one exact Artifact profile through one already-live capability binding.

### 2.2 Current reality

There are now two major Artifact execution backbones.

Backbone A — Build/Delivery:

request-v1 → DirectPython operation provider → build / verify / trust / package → optional Temporal durability.

Its production Office/Web lineage still uses production profile-v1 semantics plus verification-stage orchestration.

Backbone B — Verification Service:

profile-v2 canonical/shadow record + exact subject commitment + optional object contract + capability-bindings-v1.json → scripts/artifact_verify.py → one family-specific verifier.

Current capability-binding registry contains 19 verify bindings, all requiring LOCAL_LIVE_PROVEN.

These two backbones overlap in purpose but do not share one minimal evaluation abstraction.

## 3. New kernel hypothesis

The smallest common Artifact semantic kernel is not a build pipeline.

It is an Artifact Standing Kernel:

Bind exact subject bytes to one declared profile, resolve one admitted capability, preserve exact evidence observations, and derive only the bounded standing justified by those observations.

The kernel has five irreducible semantic responsibilities.

### K1 — Subject Commitment

Question: Which exact bytes are being discussed?

Authority examples:

- SHA-256;
- file size;
- exact file/path binding where local execution requires it;
- optional exact object-contract bytes.

Current evidence:

- artifact_core/contracts.py;
- artifact_operations/contract.py.

It must not own transport, storage, download, upload, or producer process identity.

### K2 — Profile Semantics

Question: What claims are allowed to be evaluated for these bytes?

Current evidence:

- artifact_core/profiles.py;
- artifact_core/profile_v1.py;
- profile-v2 canonical/shadow records.

A profile is a claim/evidence boundary, not a workflow script.

### K3 — Capability Binding

Question: Which admitted implementation may evaluate or produce the requested claim?

Current evidence:

- artifact_core/bindings.py;
- artifact_core/build_bindings.py;
- artifact-delivery/capability-bindings-v1.json;
- artifact-delivery/build-capability-bindings-v1.json.

Capability binding should identify an implementation and standing without making that implementation part of Core ontology.

### K4 — Evidence Observation

Question: What was actually observed, by which bounded method, over which exact bytes?

Current evidence:

- artifact_evidence/*;
- verifier outputs;
- VSA raw/evidence receipts;
- target-render and readback receipts.

Evidence must remain valid as an observation even before signature/trust overlay.

### K5 — Standing Decision

Question: Given the profile and admitted observations, what bounded claims can be made?

Current evidence is split today across:

- artifact_verification/stage.py;
- family-specific verifier result contracts;
- trust gate aggregation;
- package/release policy.

R2 should make standing an explicit semantic object rather than infer it from a particular workflow stage.

## 4. Everything else becomes a replaceable shell around the kernel

### P1 — Build Provider

Produce candidate bytes from admitted source/material commitments.

A build PASS creates candidate bytes. It does not imply Artifact standing.

### P2 — Verifier Plugin

Produce bounded evidence observations about exact candidate/existing bytes.

Current family verifier surface already behaves like a plugin ecosystem:

- 19 capability bindings;
- 17 verifier modules;
- data-driven entrypoint module/callable selection;
- per-binding required standing;
- optional object-contract requirement.

The current scripts should be treated as plugin implementations, not future Core modules.

### P3 — Trust Overlay

Authenticate or authorize evidence statements and standing.

Current artifact_trust/vsa.py contains at least four separable responsibility clusters:

1. VSA statement semantics;
2. trust-policy semantics;
3. Cosign/Sigstore toolchain and signature effects;
4. multi-gate aggregation.

Trust should overlay evidence/standing. Verification should not require cryptographic trust to exist as an observation.

### P4 — Package/Release Assembler

Assemble already-identified artifact/evidence/trust material into a release/package representation.

Current OCI stage is a 362-line orchestration function with 30 branches. That is a packaging plugin concern, not kernel semantics.

### A1 — Operation Adapter

Map a generic requested operation to kernel/services and providers.

DirectPythonOperationProvider currently has 17 project-module dependencies and is intentionally a composition root.

Its high fan-out is acceptable only if it remains wiring. Its 513-line class should not become a new semantic owner.

### A2 — Durable Runtime Adapter

Make an operation durable/replay-safe.

Temporal belongs here. Runtime process truth remains outside Artifact standing truth.

### A3 — CLI / Human Adapter

Expose stable command surfaces and diagnostics.

artifact_delivery.py, Toolchain Doctor, and Agent Surface belong here.

### X1 — Transport / Mailbox

Move exact bytes or grant bounded transport capabilities.

Artifact repository currently contains scripts/artifact_r2_mailbox.py, but the existing donor document explicitly classifies the R2 mailbox transport implementation as DO_NOT_PROMOTE.

This is not a kernel component.

### X2 — Toolchain Environment / Doctoring

Probe/install/check external execution substrates.

This is operational infrastructure and diagnostic evidence, not Artifact semantic authority.

## 5. The new canonical flow is not one pipeline

A key change is to stop forcing every artifact through one universal sequence.

The donor evidence explicitly records sequencing = NOT_ENCODED_DO_NOT_INFER.

Therefore R2 models a graph of optional transitions.

external/source bytes
→ optional Build Provider
→ SubjectCommitment
→ Profile + CapabilityBinding
→ Verifier Plugin
→ EvidenceObservation
→ StandingDecision
→ optional Trust Overlay
→ optional Package Assembler
→ optional Transport/Publication

No arrow above implies that a downstream step upgrades an upstream claim unless a profile/policy explicitly says so.

## 6. Major current divergences exposed by R1

### D1 — Two evaluation models

Office/Web production verification is still centered on artifact_verification.stage.execute_verify_stage, while standards-first families use profile-v2/capability-binding dynamic verifier routing.

This is the most important semantic duplication.

Target direction:

Both should eventually enter a common EvaluationRequest → EvidenceSet → Standing abstraction, while retaining different verifier plugins.

Do not force the production-v1 lineage into v2 until equivalence is proven.

### D2 — DirectPython provider is a composition root at risk of becoming a second monolith

Observed:

- 608 source lines;
- class body 513 lines;
- fan-out to 17 project modules;
- produce() alone is 168 lines with operation-kind branching.

Target direction:

Keep one composition root, but make operation handlers individually replaceable and prevent provider methods from becoming domain authorities.

### D3 — Trust is internally multi-responsibility

artifact_trust/vsa.py is 808 lines.

Observed clusters:

- VSA statement construction/verification;
- policy validation;
- Sigstore/Cosign selection/provenance;
- signed VSA verification;
- gate aggregation.

Target direction:

Separate pure trust semantics from external crypto/tool effects before adding more trust modes.

### D4 — OCI package stage is another orchestration concentration

execute_oci_package_stage is 362 lines with 30 conditional branches.

Target direction:

Treat OCI as a package plugin with explicit package input admission, release evidence plan, staging, OCI layout writer/referrer writer, and final release-standing evaluation.

Do not promote OCI-specific layout semantics into Artifact Kernel.

### D5 — Transport implementation is present despite explicit non-ownership

scripts/artifact_r2_mailbox.py owns Cloudflare R2 credentials, SigV4 presigning, provider inventory, and transfer-effect reconciliation.

Existing donor evidence already says this belongs to delivery infrastructure rather than Artifact classification/validation knowledge.

Target direction:

Quarantine/externalize rather than further integrate it into Artifact Core.

### D6 — Family verifiers are plugins in practice but not yet packaged as plugins

19 bindings already resolve profile/operation to module/callable with standing fences.

This is already the core shape of a plugin protocol.

Target direction:

Formalize the verifier plugin contract and common mechanical SDK without merging family semantics.

## 7. New LEGO decomposition

Kernel:

- K1 SubjectCommitment
- K2 ProfileSemantics
- K3 CapabilityBinding
- K4 EvidenceObservation
- K5 StandingDecision

Provider/plugin shell:

- P1 BuildProvider
- P2 VerifierPlugin
- P3 TrustOverlay
- P4 PackageAssembler

Execution/adapters:

- A1 OperationAdapter
- A2 DurableRuntimeAdapter
- A3 CLIAdapter

Compatibility/migration:

- C1 ProfileV1Adapter
- C2 DeliveryCompatibilityFacade

Explicitly external/quarantine:

- X1 TransportCapability
- X2 ToolchainEnvironment
- X3 ConsumerDomainAcceptance
- X4 HumanPreferenceAuthority

## 8. New questions are more important than immediate refactors

### Q1 — Can one EvaluationRequest represent both verification backbones?

Pressure test:

- one Office presentation profile;
- one Document profile;
- one standards-first family with object contract;
- one family without object contract.

Success means no loss of existing gate semantics and no forced workflow sequence.

### Q2 — What is the minimal EvidenceObservation schema?

It must express exact subject identity, evaluator/capability identity, method/tool identity where relevant, bounded claim result, evidence references, non-claims, and optional target/environment identity.

It must not become a universal artifact AST.

### Q3 — Is StandingDecision profile-owned or verifier-owned?

The verifier should report observations. The profile/policy should determine what those observations justify.

Current family result contracts sometimes combine both. This boundary needs pressure testing before implementation.

### Q4 — Can Trust be completely downstream of untrusted evidence?

Desired property:

The same evidence observation can exist locally unsigned, then later receive an authenticated assertion without rerunning the verifier.

### Q5 — Can v1 Office/Web verification become a verifier plugin without promoting profile-v2 prematurely?

A compatibility adapter may be required.

### Q6 — What should happen to R2 mailbox?

Choices to test:

- external delivery-infrastructure plugin;
- separate repository;
- retained quarantined compatibility tool.

It should not be treated as Artifact Kernel.

### Q7 — What is the lifecycle of compatibility surfaces?

Thirty Delivery wrappers and the legacy CLI provider should have explicit compatibility/version policy rather than indefinite accidental permanence.

## 9. Recommended next execution slices

Do not begin by splitting files.

### R2-S1 — Evaluation Model Pressure Test

Build an in-memory/provisional EvaluationRequest / EvidenceObservation / StandingDecision model and map four real existing profiles into it without changing production routing.

### R2-S2 — Trust Separation Audit

Map every artifact_trust/vsa.py function to statement, policy, sigstore-effect, or aggregation; prove whether those groups can be separated without circular dependencies.

### R2-S3 — Operation Composition Audit

Map DirectPythonOperationProvider.prepare_operation() and produce() branches into independent operation handlers and measure whether the provider can become a registry-backed composition root.

### R2-S4 — Package Plugin Audit

Decompose OCI packaging into package-plan/admission/staging/layout/release-decision nodes without modifying output bytes.

### R2-S5 — Externalization Audit

Classify R2 mailbox, toolchain doctor, environment setup, and publication/transport code into retain/quarantine/externalize.

## 10. Non-goals

R1 explicitly does not:

- rename the repository;
- promote profile-v2 to production;
- delete legacy profile-v1;
- replace mature native validators;
- invent a universal execution sequence;
- merge all family verifiers into one implementation;
- move Runtime/Temporal authority into Artifact;
- make transport or consumer acceptance part of Artifact standing;
- authorize implementation changes.

The result of R1 is a new problem decomposition, not another refactor wave.
