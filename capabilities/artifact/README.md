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

**Profile authority and refinement:** `artifact_core/profiles.py` now
binds parsed JSON and SHA-256 to the same indexed source bytes, reuses
Draft 2020-12 Schema validation, and rejects malformed, ambiguous or
drifted Profile authority. The mixed v1 examples directory still permits
non-Profile request/source fixtures. Eight production v1 Profiles have a
checked v2 common-semantic interpretation (ID, family, construction,
outputs, primary renderer), **not** a proof that all v1 gates equal all
v2 evidence requirements. Build/Verify bindings also reject stale source
registries and ambiguous provider standing data. Reference:
`docs/ARTIFACT_PROFILE_AUTHORITY_REFINEMENT_R1.md`.

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
2. Discover executable MCP/CLI/native-target providers in the **current** execution environment. A binding is not proof of node-local provider availability. Probe the target node and exact Runtime identity using [Workstation inventory](../../platform/workstation/inventory/README.md) before selecting a local executable.
3. Resolve exact subject/Profile/optional contract identity and check immutable input digests and binding standing at admission.
4. Delegate native-format checks to specialist tools; preserve raw observations, explicit limitations and non-claims. Do not invent a cross-family “validated” boolean for unsupported assertions.
5. Invoke optional Trust, Temporal, OCI, transfer and publication capabilities only when the consumer needs them and through the actual effect Owner. A Job exit, signed bundle or uploaded file is not itself domain acceptance.
6. Return scoped OBSERVED / VERIFIED / UNKNOWN / FALSIFIED evidence; distinguish current source, installed provider and consumer readback. Never remove source solely because a static filename search found no references.

## Consumer-accepted workflows: current source contract

A `consumer.id` in a request only names the intended caller; it does **not** execute that caller. For each common artifact operation, use the native format producer, Artifact verification service, then an independently executed consuming reader/application:

| Consumer use | Native producer | Profile verifier | Separate readback | What still is not proven |
| --- | --- | --- | --- | --- |
| Game/runtime PCM asset | Python standard `wave` writer for fixture | libsndfile, FFprobe, SoX, FFmpeg WAVE matrix | `wave.open` sample/frame readback | Sound design, actual Bevy/Godot load, gameplay suitability |
| Media FLAC interchange | Reference `flac` encoder | FLAC full-stream + FFmpeg independent decode | FFmpeg decoded-PCM bytes readback | Mastering, copyright, playback quality |
| Still-image display | Pillow PNG writer with explicit sRGB chunk | pngcheck, ExifTool, ImageMagick/libvips | Pillow image dimensions and pixels | Aesthetics, accessibility, production display |
| Research/Finance flat dataset | PyArrow Parquet writer | PyArrow/DuckDB cross-reader | DuckDB ordered query and row readback | Data origin, statistical validity, financial correctness |

The actual executable examples and negative controls are `tests/test_artifact_consumer_acceptance.py`. The Skill's Human/Agent guide is `.agents/skills/artifact-work/references/consumer-acceptance.md`.

**Evidence boundary:** `scripts/artifact_verify.py` now records `requiredEvidenceAssessment` and `profileVerificationComplete`, separate from native verifier `status`. The existing `artifact-delivery/capability-bindings-v1.json` is the **single** operation/profile binding authority; `requireClaimResults` is enabled for native FLAC, WAVE and PNG, where explicit claimResults have been qualified. For these bindings, a native overall PASS without exact required claims and matching native-status pointers is a service FAIL. For as-yet unconverted formats such as Parquet, legacy native PASS is preserved but `profileVerificationComplete=false`; do not market that as complete claim-level validation.

Do not introduce a new `consumer registry` or a mandatory OCI/attestation stage merely because an artifact has multiple readers. Consumers own domain acceptance and deployment proof.

**Exact-byte identity across native verification:** `artifact_core/input_snapshot.py`
reuses standard library `os.open`/`fstat`, streaming SHA-256 and private temporary
files instead of another CAS. The service freezes the canonical Profile bytes.
For three qualified self-contained FLAC/WAVE/PNG bindings it also freezes the
subject and optional object contract, preserving basename/extension for native
tools. The temporary snapshots are deleted after verification. The new
`inputIdentity` records `EXACT_BYTES_SNAPSHOT` versus `ADMISSION_DIGEST_ONLY`.
Legacy sidecar-bearing formats retain path admission semantics until their
complete dependencies can be frozen without breaking relative references.
A verified snapshot says nothing about source pathname continuity or what a
later consumer opened; consumers must hash their actual inputs. A process
holding the same principal may still modify private files; no process-isolation
claim is made. See `tests/test_artifact_input_snapshot.py`.

**Byte fact pairing:** `artifact_core/contracts.py` derives `sha256` and `size`
from the same opened byte stream for `file_fact` and `FileCommitment`,
rather than combining digest with a later pathname `stat` call. Legacy
request admission reuses this existing commitment; the result remains
`ADMISSION_DIGEST_ONLY` until the corresponding dependency closure is
staged and verified. See the deliberate path-replacement regression in
`tests/test_artifact_core_registry.py`.

**Native executable post-run observation:** The service independently rereads
the native verifier's already-declared executable paths and compares actual
SHA-256 to the reported `tools` facts. An explicit contradiction invalidates
service PASS; missing tool inventories remain `NOT_EVALUATED`. This reuses
`FileCommitment`, not a new dependency registry. `toolIdentityAssessment`
cannot establish which executable bytes the earlier subprocess loaded,
whether imports/dynamic libraries changed, or full dependency completeness.
See `tests/test_artifact_tool_identity.py`.

**Native result identity:** `artifact_verification/native_identity.py` checks
reported Profile ID, subject SHA-256/size and object-contract SHA-256 against
the admitted input commitments. Contradictions reject service `PASS`, while
missing fields on legacy profiles remain `NOT_EVALUATED`. Complete Profile
evidence additionally needs native identity agreement. The three qualified
FLAC/WAVE/PNG profiles require every native identity field. An exception or
malformed provider result becomes a bounded failure. The associated model
checks 216 abstract cases; real provider and consumer tests remain necessary.

## Formal-first verification and genuine test retirement

The normative **safety property** is “a missing/unknown/failed or self-witnessing required claim cannot become complete Profile evidence.” The pure evaluator and its bounded executable refinement checker are `artifact_verification/claim_coverage.py` and `artifact_verification/formal/verify_claim_coverage.py`. The mathematical statement, source/proof bridge, limitations, Human/Agent guidance, and test-retirement argument are in `docs/ARTIFACT_CLAIM_COVERAGE_FORMAL_R1.md`.

Both `mise run verify` and `mise run queue` run this finite model check for real FLAC/WAVE/PNG Profile key sets, followed by necessary physical/consumer tests. Its finite PASS does **not** prove all JSON shapes, arbitrary provider outputs or consumer behavior. Four pure illustrative tests were removed once the stronger abstract-state cross-product checker replaced their explicit cases; real decoder, negative-admission, native file readback and end-to-end checks remain.

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
