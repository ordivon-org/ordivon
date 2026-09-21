# Artifact Build & Delivery E2E — Authoring and Orchestration v1

## Scope

This layer converts an exact, approved artifact request into native-format build bytes and then composes independent verification/release evidence. It does **not** research or approve business claims, does not define a universal document AST, and does not replace Temporal, OOXML, PDF, WCAG, in-toto/SLSA, Office target renderers or delivery APIs.

The durable split is:

```text
approved content / native source
        +
delivery profile
        ↓
digest-bound request
        ↓
derived build plan
        ↓
format-specific build adapter
        ↓
native artifact bytes
        ↓
independent verification gates
        ↓
release manifest + provenance
        ↓
delivery adapter + exact read-back
```

The derived plan is an execution projection only. It is not durable workflow state. Temporal remains the durable workflow substrate when retries, timers, fan-out, cancellation or recovery are required.

## Shared request envelope

`artifact-delivery/request-v1.schema.json` carries only cross-format build/release inputs:

- request identity;
- exact delivery profile path + SHA-256 + profile id;
- exact source path + SHA-256 + source kind;
- optional exact material references;
- output directory;
- SLSA-compatible builder id and build type.

It deliberately does not carry slide nodes, paragraph nodes, worksheet cells, PDF structure elements, workflow statuses or delivery standing.

`validate-request` fails closed when the request schema is unavailable/invalid, referenced bytes drift, the selected profile fails its own schema, or the profile id does not bind the referenced bytes.

## Format-specific presentation source

`artifact-delivery/presentation-source-v1.schema.json` is the first format-specific semantic source contract. It is scoped to presentations only.

Current v1 native composition supports:

- presentation id/profile binding;
- locale and aspect ratio;
- explicit slide size;
- ordered slides with stable ids/titles;
- exact digest-bound slide-free PPTX authoring authority when a native template/master/layout chain is required;
- case-insensitive binding to the template's native PowerPoint slide-layout name;
- native OOXML placeholder-idx binding so title/body/subtitle geometry and inherited style remain template-owned rather than copied into an Artifact-specific layout model;
- free-form text elements with explicit geometry/typography when no native placeholder is appropriate;
- font-family admission against the selected delivery profile for explicit font overrides;
- fail-closed template digest, slide-size, layout, placeholder, bounds and duplicate-id checks.

A template referenced by presentation source is promoted into the request's resolved build-material set after exact SHA-256 verification. It therefore participates in the existing SLSA provenance material list rather than becoming an untracked visual dependency. The template file digest already binds its theme, slide masters and slide layouts; build receipts additionally record the selected native layout/master parts and template theme/master/layout part digests.

The current `python-pptx 1.0.2` adapter cannot open a true `application/vnd.openxmlformats-officedocument.presentationml.template.main+xml` POTX package. v1 therefore accepts a **slide-free PPTX authoring authority** carrying the same standard OOXML theme/master/layout/placeholder structures and explicitly does **not** claim POTX ingestion. We do not rewrite POTX content types or create a fake format identity merely to bypass that library boundary; a future writer/adapter may add native POTX input without changing the source/template semantics.

### Hybrid raster/native presentation composition

Presentation source v1 also supports a presentation-specific raster image element for high-fidelity migration and controlled hybrid authoring. This is not a universal image/document AST. Each PNG/JPEG is referenced by path + exact SHA-256, uses explicit slide geometry, and is promoted into the request's resolved build-material set. The builder preserves the source raster bytes in the OOXML media part and records the source/image binding in the build receipt.

Element order is the native PowerPoint shape order. A migration slide can therefore place an exact approved visual reference as the first full-slide shape, then add native editable PowerPoint text/placeholders above it. This lets legacy/high-fidelity visual authority remain stable while semantic/editable regions are migrated incrementally instead of forcing an all-at-once redraw.

Accessibility intent is explicit: a non-decorative raster requires authored alt text; decorative standing is carried as source/build intent. The current python-pptx adapter writes native `descr` metadata for non-decorative images but does not claim a stable high-level API for PowerPoint's decorative flag. Accessibility acceptance remains an independent target gate and cannot be inferred from source metadata alone.

The generic `presentation-ultrawide-34x10-r1` delivery profile now provides the 34:10 PPTX/PDF target geometry needed for ultrawide presentation products. Its 3400×1000 render evidence size is a canonical QA raster, not a claim about a customer's physical display pixel matrix.

The same schema can carry `reference-map` entries for legacy migration without pretending those legacy bytes have already been semantically reconstructed. The native builder accepts only `sourceMode=native-composition`.

The first deterministic source fixture is `presentation-native-smoke-source-r1.json`. It is a semantic/build-path smoke and is not a PDU/SDU Golden candidate.

## Derived plan

`compile-request` maps the selected profile + source kind to a replaceable build adapter and derives:

- expected primary/companion outputs;
- profile-required gates;
- delivery targets;
- the four production phases `build → verify → package → release`.

The compiler binds the exact request SHA-256 and rejects a builder id/build type that does not match the selected adapter. This prevents provenance from naming one builder while different local mechanics execute.

Current adapters:

- presentation source v1 → `python-pptx` native OOXML;
- Markdown document source → Pandoc DOCX;
- HTML source → exact file-copy build boundary;
- native file → exact pass-through copy for profiles that already start from canonical native bytes.

The adapter map is replaceable implementation detail. Profile contracts and acceptance gates remain durable.

## Build stage

`build-request` executes only the **build** phase for currently supported adapters. Build PASS means:

1. request/profile/source/material digest bindings are intact;
2. request and source schema checks pass;
3. the selected adapter matches the declared builder identity;
4. the primary output file exists;
5. adapter-local checks pass.

For Markdown → DOCX, Pandoc's standard `SOURCE_DATE_EPOCH` input remains caller-owned rather than becoming an Artifact-specific timestamp field. When present, Artifact requires a non-negative base-10 integer, passes the exact value explicitly to Pandoc, and records it under `adapterResult.reproducibleBuildEnvironment`. When absent, `document-r1` build admission is unchanged: build PASS does **not** imply byte-for-byte reproducibility. A caller that requires reproducible DOCX bytes must freeze `SOURCE_DATE_EPOCH` prospectively and preserve the resulting build evidence; Artifact does not normalize post-hoc timestamps or invent a second clock contract.

For presentation source v1, the builder additionally runs native PPTX package/relationship inspection and presentation semantic checks. A separate `DocumentFormat.OpenXml` gate remains required for ISO/IEC 29500 validation; PowerPoint target rendering, visual QA, accessibility, PDF companion production and delivery read-back remain independent.

A v1 smoke has now proven:

```text
presentation source JSON
  → request/profile digest binding
  → derived adapter plan
  → python-pptx native PPTX
  → package/semantic PASS
  → DocumentFormat.OpenXml 3.5.1 PASS
```

This closes the previously missing **source → native artifact** segment without claiming release completion.

## Verification evidence and gate aggregation

`verify-stage` now executes profile-specific validators and emits two distinct evidence layers:

1. raw validator evidence, preserving the native output/truth boundary of Open XML SDK, qpdf, veraPDF, Nu Html Checker, Playwright and axe;
2. an in-toto Statement v1 using the approved SLSA Verification Summary v1 predicate for the summarized policy decision.

The VSA binds the exact artifact digest, the exact delivery-profile policy digest, verifier identity/version information and `verificationResult`. `resourceUri` uses the RFC 6920 `ni` URI form (`ni:///sha-256;...`) so content identity survives local/package path changes without inventing an Artifact URI scheme. Because these checks are Artifact profile checks rather than SLSA Build-track qualification, a successful local summary uses the standard `SLSA_BUILD_LEVEL_UNEVALUATED` value instead of claiming a SLSA level. Failed policy checks use `FAILED`. Raw validator JSON is **not** placed in `inputAttestations`, because that field is reserved for attestations consumed by the verifier; raw evidence remains separately digest-bound by package/release manifests.

Verify-stage still emits an unsigned VSA first, because validator execution and signing authority are separate responsibilities. Production trust can now be added without changing the VSA semantics: `verify-signed-vsa` requires a standardized Sigstore v0.3 DSSE bundle, exact equality between the signed DSSE statement and the detached VSA JSON, exact artifact/profile/resource bindings, and an explicit signer → allowed `verifier.id` mapping from the shared attestation trust-policy contract.

The first admitted trust mode is a pinned self-managed public key. The public-key file itself is SHA-256 pinned by the trust policy, and Cosign must pass the selected toolchain digest/version check. A service-empty Sigstore `SigningConfig` is checked into the toolchain for local/self-managed signing so that signing cannot silently contact Fulcio, an OIDC provider, Rekor, or a TSA. Transparency logging can still be required by a different release trust policy; it is simply not an ambient side effect of local signing.

Keyless identity verification is intentionally **not yet claimed** on the current line with the selected GPG-verified Arch `cosign 3.1.3-1` package. The verifier rejects legacy bundles and accepts only standardized v0.3 bundles, uses a Cosign minimum of 3.0.6, and explicitly sets claim checking. That closes the April 2026 predicate/claim false-positive path and avoids the August 2026 legacy-bundle identity-bypass path. Keyless standing remains NOT_EXERCISED until the Fulcio/OIDC identity, issuer and transparency-log path has been exercised end to end. The selected verifier is now the GPG-verified Arch `cosign 3.1.3-1` package; that tool upgrade does not by itself create keyless identity evidence.

`aggregate-vsa-gates --allow-local-unsigned` remains available only for same-workspace development. Without that switch, every required VSA gate must provide a trusted signer id, a standardized Sigstore bundle and the out-of-band trust policy; otherwise aggregation fails closed.

Generic JSON gate composition and custom package relationship mechanics have been retired. `aggregate-vsa-gates` remains the Artifact semantic trust aggregator, but final release admission is no longer a Python boolean policy: Artifact submits verification/trust/assembly facts to `artifact-delivery/policy/release.rego`, and OPA evaluates `data.artifact.release.ready`.

## OCI package and release composition

The durable package boundary remains after verification/trust, but OCI 1.1/ORAS owns mechanical content identity and relationships. `scripts/artifact_oci_package.py` is intentionally a thin adapter: it validates Artifact-specific commitments and invokes pinned ORAS rather than serializing an Artifact-specific package index or release manifest.

The package preflight still distinguishes two gate classes:

- **verification/VSA gates** — `profileSchema`, `structural`, `dependency`, `semantic`, `visual`, `target`, `accessibility`, `conformance`, `deliveryReadback`;
- **assembly/provenance gates** — `companionPdf`, `releaseProvenance`.

Every verify receipt is rechecked against current raw-evidence/VSA bytes before OCI creation, so post-verification drift fails before packaging. The release subject contains the primary artifact and required companions as exact OCI layers. Verification gates are OCI Referrers carrying raw evidence + VSA and, for trusted production gates, the exact Sigstore bundle. The verify-stage report is a separate referrer; in-toto/SLSA provenance is another referrer when present.

```text
package/layout/
  oci-layout
  index.json
  blobs/sha256/*
```

There is no custom `package-index.json`, `release-manifest.json`, `artifacts/`, `evidence/` or `attestations/` relationship tree. OCI descriptors/referrers provide those mechanical relationships. VSA `resourceUri` continues to use RFC 6920 `ni` content identity, so Artifact trust remains content-bound rather than path-bound.

Trust remains explicit in two modes. Local unsigned development packages are `LOCAL_UNSIGNED_DEVELOPMENT` and OPA forces `releaseReady=false`. Production packages require trusted signer/verifier mappings plus standardized Sigstore bundles; after cryptographic verification, OPA grants `releaseReady=true` only when every required verification and assembly fact is present. Package creation alone cannot promote trust.

The live cutover was accepted on 2026-09-12 with both modes through the production Temporal worker: a local-unsigned workflow produced four OCI referrers with `releaseReady=false`, and a separate trust-signal workflow reached `CRYPTOGRAPHICALLY_VERIFIED`, four OCI referrers and OPA `releaseReady=true`.

## Temporal durable execution

The stateless compiler remains the source of the derived execution plan, while the existing Temporal substrate now owns durable ordering, retries, cancellation and recovery. Artifact E2E does not introduce a second scheduler or an Artifact-specific workflow state machine. The production workflow is `ordivon.artifact.delivery` on `temporalio 1.32.0` and executes the following activity boundary:

```text
prepare → build → verify → [wait for public trust material] → verify-trust → package
```

Activity effects are receipt-fenced by `stage + operationId + immutable input commitments`. Each operation has one deterministic state directory guarded by an OS file lock. `activity-receipt.json` is the commit marker:

- the same operation id with the same committed inputs revalidates all output digests and returns the exact prior result with `replayed=true`;
- the same operation id with different inputs fails closed;
- an operation directory without a committed receipt is an abandoned attempt and can be rebuilt;
- committed output drift fails closed rather than being silently regenerated.

The Temporal worker and Artifact toolchain intentionally use separate Python environments. The worker runs in the existing Temporal environment; activities invoke the exact Artifact Delivery interpreter for JSON Schema, python-pptx and other format-specific dependencies. This avoids merging unrelated dependency authorities merely for orchestration convenience.

Production signing authority stays outside workflow execution. After validator VSAs exist, the workflow enters `WAIT_TRUST_MATERIAL`. The status query exposes only digest-bound artifact/VSA commitments. An external signer, KMS or identity service may then produce standardized Sigstore bundles; the supported launcher accepts only `trustPolicy`, `bundles` and `signerIds` public verification material and rejects unknown/secret fields **before** they are sent to Temporal. Private keys, passwords, KMS credentials and OIDC tokens are not part of the workflow contract. Direct misuse of the Temporal API remains outside this supported-interface guarantee, so operators must never send secrets as workflow input or signal payload.

The implementation has been exercised against the live local Temporal server, not only unit-tested:

- local unsigned development workflow: PASS with `LOCAL_UNSIGNED_DEVELOPMENT` and `releaseReady=false`;
- production trust-signal workflow: paused at `WAIT_TRUST_MATERIAL`, resumed with three signed VSA bundles, and reached `CRYPTOGRAPHICALLY_VERIFIED` / `releaseReady=true`;
- deterministic Temporal replay: the completed trusted workflow history replayed with no failure across 39 history events;
- cancellation at the trust wait: workflow cancellation produced no package operation;
- direct activity replay: a repeated package/build operation returns the committed receipt instead of duplicating the effect.

A hardened systemd worker unit and plan/apply deployment helper are defined and deployed from `/root/projects/ordivon/capabilities/artifact`. The helper still refuses to apply from a detached Runtime workspace. The accepted worker targets the production-green Temporal cluster at `127.0.0.1:17233`, and the checked-in development-only workflow fixture has completed prepare/build/verify/package without promoting release readiness.

## Next admissible implementation

The remaining Linux-local orchestration work is:

1. preserve the accepted independent source authority and guarded worker deployment; do not reintroduce Workstation as Artifact source owner or apply detached-workspace units;
2. complete the verify-stage matrix for gates that can run locally and preserve externally-blocked Office/WebKit/visual/delivery gates as explicit pending/fail-closed states;
3. decide and implement cryptographic authenticity for SLSA release provenance using the same Sigstore substrate or a separately authorized release-signer policy, rather than inventing another provenance format;
4. exercise the standardized-bundle keyless identity path with explicit identity/issuer/transparency-log/TrustedRoot integration evidence; an independently verified upstream Sigstore asset may later replace the GPG-verified distribution package as tool-origin hardening;
5. apply the now-implemented native template/master/layout/placeholder and digest-bound hybrid raster/native composition to a controlled PDU/SDU migration slice, preserving approved business content and separating inherited template styling, high-fidelity visual authority and editable semantic overlays;
6. migrate the PDU/SDU 8-slide case from `reference-map`/legacy authority toward native/hybrid semantic source without changing approved business content, with exact source/template/material provenance;
7. resume Microsoft PowerPoint/Word/Excel and supported WebKit target gates only when their external substrates are available.
