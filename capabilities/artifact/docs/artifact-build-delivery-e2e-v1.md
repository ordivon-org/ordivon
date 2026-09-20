# Artifact Build & Delivery E2E v1

## Frozen boundary

This line owns the composition of mature tools into a recipient-usable artifact. It does **not** own Word, PowerPoint, PDF, font, accessibility, browser, provenance, queue, telemetry, storage, or artifact-transport semantics.

Long-lived contracts are the delivery profile and renderer support matrix, immutable material/output digests, quality/evidence gates, authority mode (`generated-managed` or `office-authored`), target-render acceptance, and destination read-back requirements. PPTX/DOCX writers, PDF tools, render workers and converters remain replaceable implementation details.

## R1 Presentation profile

Golden case: PDU/SDU. Primary output is editable PPTX for Microsoft PowerPoint Desktop on Windows. Required companion is PDF for portable/mobile visual consumption. Required target evidence is one digest-bound PNG per slide plus renderer identity. Required delivery destinations are Google Drive and the Windows workstation, each followed by read-back and digest equality.

A process exit, file existence, structural validity, or secondary-render success alone is never E2E graduation.

## No universal document AST

Durable inputs remain in their native standards: CommonMark/HTML prose, CSV/Arrow/Parquet data, SVG/raster assets, native Office templates and JSON configuration. Any writer/compiler AST is implementation-private.

## R1 gates

1. Profile: JSON Schema Draft 2020-12 validation.
2. Structural: OPC/PPTX package/relationship checks plus `DocumentFormat.OpenXml` `OpenXmlValidator` evidence.
3. Dependency: concrete render typefaces from slides, layouts and masters must be declared and target-satisfied when required; no silent fallback.
4. Semantic: placeholder policy, slide-count bounds and declared aspect ratio are enforced.
5. Visual: target-rendered PNG integrity plus digest-bound visual review. PNG presence is not visual PASS.
6. Target: one-shot Microsoft PowerPoint Desktop open, native PDF save and slide PNG export, with PPTX/PDF/PNG digests, renderer version and executable digest.
7. Delivery: use an existing API/mature transport, then read back every required output from every configured destination and require SHA-256 equality.

PowerPoint localized output names are treated extension-case-insensitively, and target evidence must bind the exact PNG name/digest map returned by the target run. A structurally valid 10:34 long canvas cannot pass a 16:9 profile merely because it is a PPTX.

The local Python helper does not impersonate ISO/IEC 29500 validation. PDF structure is delegated to qpdf; PDF/A/PDF-UA profiles must use mature conformance tooling such as veraPDF/PAC rather than extending the local checker into a custom standard.

## PowerPoint worker

`scripts/powerpoint_render_worker.ps1` is a bounded, one-shot target-environment acceptance worker, not an Office server daemon. It opens one immutable PPTX with installed Microsoft PowerPoint Desktop, saves the ordinary PDF companion with PowerPoint's native PDF format, exports per-slide PNGs, records hashes and renderer identity, then closes PowerPoint.

The R1 Windows smoke fixture has completed this path successfully, including exact Windows destination read-back. That proves the target substrate, not the PDU/SDU Golden artifact.

## Provenance

The runner emits an in-toto Statement v1 using the SLSA Provenance v1 predicate when explicitly supplied builder/build-type URIs. It does not define an `OrdivonArtifactProvenance` schema.

## Source and delivery transport boundary

Artifact E2E does not invent a transport protocol. Exact external inputs should use a mature API/object store or Runtime's configured immutable input authority; outputs should use provider APIs where available. Runtime `workspace.execBound` is an appropriate existing exact-input mechanism when an operator authority is configured, including for Windows. Missing authority/configuration is a deployment/resource fact, not justification for a new Artifact-specific transport.

## Current R1 standing (2026-09-09)

The PowerPoint/Windows smoke branch is end-to-end PASS. The original PDU/SDU Golden files remain frozen font-regression inputs. Script-aware font-fixed candidates have exact Google Drive write/read-back and secondary-render confidence, but their exact bytes have not yet reached Microsoft PowerPoint target acceptance because the current workstation lacks a mature configured source path to those Drive bytes. Full PDU/SDU R1 therefore remains `NOT_PASS`.

### Current Golden ingress pattern (R2)

For OOXML Golden sources whose frozen visual authorities are package parts, the external authority boundary binds the exact parent package once rather than manufacturing one transport object per package part. Runtime remains responsible for named-authority resolution and exact parent-byte verification through `workspace.execBound`; Artifact may then project explicitly declared OPC parts by exact member name, size and digest. The projection neither expands Runtime authority nor creates an Artifact transport protocol. The PDU/SDU 34:10 Golden uses this pattern in `pdu-sdu-34x10-runtime-package-input-set-r2.json` and `pdu-sdu-34x10-opc-member-projection-r2.json`.

### Production ingress configuration candidate (R2)

The source-bound operator configuration keeps three filesystem roles separate: Runtime's private external-file stage is `/var/lib/ordivon/runtime-input-ingress`; Workstation's durable ingress intent/receipt ledger is `/var/lib/ordivon/artifact-input-ingress`; and the final consume-only Runtime authority remains `/var/lib/ordivon/artifact-input-authorities/golden-r1`. `config/artifact-runtime-input-ingress-r2.json` is the JSON value intended for `ORDIVON_INPUT_INGRESS_JSON` after operator deployment; `config/artifact-input-authority-ingress-r2.json` is the Workstation config intended to be installed at `/etc/ordivon/artifact-input-authority-ingress.json`. Both use the `runtime-stage` carrier and an 8 MiB exact upper bound. No credential, signed URL or provider file ID is source-configured.

The Runtime download-host entry is the explicit `*` host-name sentinel because the native host file-parameter contract does not provide a durable public hostname contract. This does not relax transport safety: the Runtime ingress implementation still requires HTTPS/443, disables ambient proxy use, pins and revalidates DNS/public-address observations on each hop, and rejects loopback/private/link-local/CGNAT/documentation/multicast and other non-public destinations. The wildcard therefore relaxes only hostname naming, not network destination class or digest/size authority. Production activation remains separate from source configuration and is not implied by these files.
