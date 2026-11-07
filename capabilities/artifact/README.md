# Artifact — native digital output, evidence and delivery

**Owner:** `capabilities/artifact/`. Artifact constructs or verifies exact digital outputs against bounded, declared profiles. It is not a general filesystem, transport system, workflow engine, or consumer-domain quality authority.

## Current authority and history

- **Implementation truth:** current `artifact_core/`, `artifact_operations/`, `artifact_verifiers/`, `artifact_verification/`, `artifact_evidence/`, `artifact_capabilities/`, `artifact_trust/` plus selected `artifact-delivery/` schemas/bindings/locks.
- **Deployment truth:** live Runtime, Workstation, external providers and target consumers. A source test, registry snapshot or historical approval is not evidence of the currently installed binary/service.
- **Planning:** `planning/lego-plan-r2.json` is a planning projection, not an installed state or second LEGO registry.
- **Historical evidence:** `docs/ARTIFACT_CAPABILITY_DECOMPOSITION_WAVE_A15_R1.md` (and waves A1–A14 retained in Git history) and the dated R1/R2 closure/acceptance records are frozen source-cut observations. Historical line counts, paths, tool versions and statements of “current” availability must not override today's source and readback.

**Audited source snapshot (2026-11-07):** `f52091fb1c8f920b7114c813142d1e7795ae8664`: 425 tracked Artifact files, 16 taxonomy families, 19 verify bindings, 11 build bindings, 20 shadow profile files. These are not permanent invariants or proof of live deployment.

## Directory responsibilities

| Directory | Responsibility |
| --- | --- |
| `artifact_core/` | Exact bytes, Profile semantics, admission and capability bindings |
| `artifact_capabilities/` | Native builders and presentation/publication-specific production helpers |
| `artifact_operations/` | Canonical operation envelope, provider composition, exact receipts |
| `artifact_verifiers/` | Office, PDF, presentation and web specialist validators |
| `artifact_verification/` | Original delivery verification-stage orchestration |
| `artifact_evidence/` | Source snapshots, gate, target, delivery and readback evidence |
| `artifact_trust/` | Provenance, verification-summary attestations, signatures and policies |
| `artifact-delivery/` | Schemas, profiles, bindings, locks, examples and acceptance fixtures |
| `scripts/` | Family-specific verifier CLIs, Agent entrypoints, Temporal and tool adapters |
| `planning/` | R2 LEGO candidate decomposition, proofs/pressure experiments |
| `registry/` | Dated Artifact closure evidence, **not** Runtime PostgreSQL registry |
| `config/`, `systemd/` | Configuration and service manifests; **not** active-state evidence |
| `tests/` | Owner-native tests; `docs/` | Source-bound studies and historical acceptance |

Runtime Job artifacts (stdout, stderr, execution result) belong to Runtime process evidence. Artifact standing is instead a bounded claim about exact content. Game, Media, Research, Finance and other consumers retain their own domain-acceptance decisions.

## Core R2 decomposition

The five **semantic responsibilities** under investigation are SubjectCommitment (exact input bytes), ProfileSemantics (claims/non-claims), CapabilityBinding (qualified verifier/builder), EvidenceObservation (what was actually observed), and StandingDecision (what those observations justify). These are not five mandatory new files, registries or independently admitted formal LEGOs.

Build providers, verifier plugins, trust overlays, OCI package assembly and durable execution adapters remain replaceable/optional around that semantic core. In particular:

- Production Office/Web verification through Profile v1 and standards-first Profile v2 verification have separate evaluation backbones today. Profile v2 **shadow** mappings do not certify a production cutover.
- A verifier's stage `PASS` only supports its declared checks; missing claim-level keys remain `UNKNOWN`, not inferred success.
- No universal document/media/data AST, custom transport, proprietary registry, or mandatory Build → Verify → Trust → Package sequence.

Reference: `docs/ARTIFACT_VERIFICATION_SERVICE_R1.md` and `planning/lego-plan-r2.json`, checked against their current source files.

## Human guide: produce or verify one real outcome

1. Name the real consumer, primary native format, optional companion outputs, actual source and material identities, target app and acceptance predicates. An editable PPTX + PDF requires target-render evidence when its Profile requires it.
2. **Already have bytes?** Choose a specific Profile in `artifact-delivery/shadow-v2/examples/` and matching verification route in `artifact-delivery/capability-bindings-v1.json`. Consult `artifact-delivery/verification/request-v1.schema.json`; some families additionally require an object contract.
3. **Need to build?** Use `artifact-delivery/request-v1.schema.json` and `artifact-delivery/build-capability-bindings-v1.json` instead. Profile acceptance does not follow from Build success.
4. Verify the selected native tool is actually installed/available. Bind exact file, Profile and optional object-contract SHA-256 commitments; invoke the existing thin adapter for existing bytes:

   ```bash
   uv run python scripts/artifact_verify.py /absolute/path/request.json --output /absolute/path/result.json
   ```

5. Inspect exact evidence and target readback. Treat `PASS`, `FAIL`, `SKIP`, `NOT_RUN`, and missing checks separately. Domain use, human visual judgment and publication are independent responsibilities.
6. From this Owner root, `mise run verify` runs locked dependency verification, Ruff and `pytest -m "not integration"`. A green result does **not** establish external integration or currently installed deployment state.

## Agent guide: evidence before authority

The existing `.agents/skills/artifact-work/SKILL.md` is the Agent method entrypoint; load only the relevant format family reference.

1. Bind an actual consumer, SourceCut, outcome and evidence predicates. Prefer DELETE unnecessary custom → REUSE mature tools → COMPOSE → minimal evidenced adapter.
2. Discover executable MCP/CLI/native-target providers in the **current** execution environment. A binding is not proof of node-local provider availability.
3. Resolve exact subject/Profile/optional contract identity and check immutable input digests and binding standing at admission.
4. Delegate native-format checks to specialist tools; preserve raw observations, explicit limitations and non-claims. Do not invent a cross-family “validated” boolean for unsupported assertions.
5. Invoke optional Trust, Temporal, OCI, transfer and publication capabilities only when the consumer needs them and through the actual effect Owner. A Job exit, signed bundle or uploaded file is not itself domain acceptance.
6. Return scoped OBSERVED / VERIFIED / UNKNOWN / FALSIFIED evidence; distinguish current source, installed provider and consumer readback. Never remove source solely because a static filename search found no references.

## Mature external LEGO suppliers: reuse, do not reimplement

| Concern | Existing mature semantics/providers to qualify |
| --- | --- |
| Typed profile validation | [JSON Schema Draft 2020-12](https://json-schema.org/specification), family-native standards |
| OCI packages/distribution | [OCI Image](https://specs.opencontainers.org/image-spec/), [OCI Distribution](https://specs.opencontainers.org/distribution-spec/), ORAS/Zot when consumer-qualified |
| Authenticated supply-chain evidence | [in-toto Attestation](https://github.com/in-toto/attestation), [SLSA Provenance](https://slsa.dev/spec/v1.2/provenance), [Sigstore Cosign](https://docs.sigstore.dev/cosign/verifying/verify/) |
| Office/PDF/media/data/3D validation | Existing native Pandoc, PowerPoint, qpdf/veraPDF, FFmpeg, GDAL, glTF Validator, libvips/ImageMagick, PyArrow/DuckDB bindings where available |

Qualify an upstream project against exact user-facing acceptance and negative cases, version, license, maintenance, effects and replaceability. Use `.agents/skills/external-capability-evaluation/SKILL.md`. Mere GitHub discovery is not adoption.

## Cleanup, naming and retirement

- The name of a Profile, Python import path, schema, Temporal route, service, lock or provider is a consumer contract, not decoration. Prefer standard semantics; rename only with explicit compatibility/refinement evidence and consumer readback.
- The audited `scripts/artifact_r2_mailbox.py` + `config/artifact-r2-mailbox-r1.json` belong conceptually to transport, not Artifact standing. Their test and historical references exist; installed/dynamic consumers remain unclosed. Audit before removal or transfer.
- `docs/ARTIFACT_REDECOMPOSITION_R1.md` still references a historical `artifact_delivery.py` CLI **absent** from this source cut; do not infer it is current code.
- The A1–A14 historical decomposition-wave documents had no text-path consumers in the audited tracked source and are removed from this isolated source candidate; their bytes remain retrievable from the base Git revision. A15 remains because the R2 plan references it. This source-retirement evidence does not establish the absence of external/dynamic consumers.
- Caches (`.venv`, `__pycache__`, `.pytest_cache`) should be cleaned only with native local project tools after verifying ownership. Never recursively delete system files, active Runtime Workspaces, source materials or another Owner's state.
- Stop decomposition when further files only add glue. Existing semantic seams and consumer-accepted native tools take priority over a prettier directory tree.
