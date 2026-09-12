# Artifact Build & Delivery E2E — Toolchain v1

## Boundary

The durable architecture is standards, responsibility boundaries, quality gates and evidence contracts. Concrete writers, converters, renderers and validators are replaceable selections. The composition does not create a universal document AST or an Artifact-specific file, workflow, provenance, accessibility or transport standard.

`artifact-delivery/toolchain-v1.plan.json` records current selections and rejected/blocking candidates. `artifact-delivery/toolchain-v1.lock.json` records exact observed versions and source/archive digests. Format profiles are machine-executable delivery contracts under the shared Draft-2020-12 schema; format semantics remain profile-specific.

## Shared profile matrix

The v1 contract now validates these concrete profiles:

- `pdu-sdu-presentation-r1`: PPTX primary, PowerPoint Desktop target, PDF companion.
- `document-r1`: DOCX primary, Word Desktop target, PDF companion.
- `spreadsheet-r1`: XLSX primary, Excel Desktop target.
- `pdf-fixed-r1`: ordinary fixed-view PDF; no PDF/A or PDF/UA claim.
- `pdf-accessible-r1`: PDF/UA-2 profile with veraPDF `ua2` conformance gate.
- `web-r1`: HTML primary, Chromium primary renderer, Firefox and WebKit secondary release renderers.

The profile contract carries required outputs, target renderer, delivery targets and quality gates. It does not introduce a shared semantic AST across presentations, documents, spreadsheets, PDFs and web artifacts.

## Verified composition

- Shared contract: JSON Schema Draft 2020-12 via `python-jsonschema 4.26.0`; the cross-format profile matrix validates.
- Durable workflow: reuse the existing Temporal substrate and its `temporalio 1.32.0` pin; no second Artifact workflow runtime is installed. The live `ordivon.artifact.delivery` workflow now composes receipt-fenced `prepare/build/verify/verify-trust/package` activities, pauses production execution for public trust material, and keeps signing secrets outside workflow history. A local unsigned run, a cryptographically trusted signal/resume run, deterministic replay of the 39-event trusted history, and cancellation-before-package have all passed against the existing local Temporal server.
- Observability: OpenTelemetry SDKs are imported and mechanically smoke-tested.
- Presentation generation: `python-pptx 1.0.2` generates OOXML that passes `DocumentFormat.OpenXml 3.5.1`; the exact simple probe also opens in Microsoft PowerPoint Desktop 16.0, exports native PDF/PNG, and survives digest read-back plus qpdf structure checking. The authoring layer supports a digest-bound slide-free PPTX style authority, native slide-layout selection and native placeholder-idx binding, preserving the template's theme/master/layout chain instead of reproducing it in a custom Artifact model. It also supports digest-bound PNG/JPEG slide media as an explicit presentation-specific hybrid layer; exact media bytes are preserved in OOXML and both template/media authorities are promoted to resolved provenance materials. A generic 34:10 profile has a native hybrid build/OpenXML smoke. True POTX ingestion remains a declared `python-pptx` limitation rather than a false compatibility claim.
- Presentation rejection evidence: `PptxGenJS 4.0.1` and `pptxgenjs-plus 4.3.2` fail the same Open XML SDK schema gate and remain outside production dependencies.
- Document conversion: Pandoc 3.10.2 was downloaded from its official release asset, matched its release SHA-256, and generated DOCX that passes the Open XML SDK validator. Word target acceptance remains separate.
- Spreadsheet generation: XlsxWriter 3.2.9 passes Open XML validation for minimal and styled XLSX probes. `openpyxl 3.1.5` is not the v1 final-emission writer because its generated styles fail the same strict validator.
- PDF structure/conformance: qpdf 12.3.2 performs ordinary structure checks. veraPDF 1.30.2 is official-signature verified and now has an executable profile gate. A normal PowerPoint-generated PDF was intentionally tested as PDF/UA-2 and correctly failed, proving that ordinary PDF bytes cannot be promoted to accessible standing by file extension or metadata-free assumption.
- Release assembly: the v1 release-manifest gate digest-binds profile, primary artifact, companions, evidence and optional/required in-toto/SLSA provenance. Manifest PASS is only package assembly evidence; it cannot launder missing target/visual/accessibility/delivery gates.
- Web: Nu Html Checker 26.9.7 (d73d94b), pinned by exact official release-asset SHA-256, performs standards conformance checks. Playwright 1.63.0 with Chromium 153.0.8010.12 launches headlessly and the axe Playwright adapter 4.13.0 reports zero violations on the deterministic fixture. Firefox 155.0 also launches successfully on the current host.
- Verification summaries: validator-produced results are projected as in-toto Statement v1 + SLSA Verification Summary v1 (`https://slsa.dev/verification_summary/v1`) with SLSA 1.2 semantics. The VSA binds the exact artifact and delivery-profile policy, uses an RFC 6920 `ni` SHA-256 URI for path-independent content identity, deliberately does not misuse `inputAttestations` for raw validator JSON, and does not claim a SLSA build level (`SLSA_BUILD_LEVEL_UNEVALUATED`).
- VSA authenticity: the shared attestation trust-policy contract maps an out-of-band signer to allowed `verifier.id` values. `verify-signed-vsa` accepts only the standardized Sigstore v0.3 JSON bundle, requires the DSSE payload JSON to equal the detached VSA statement, and then runs Cosign with explicit claim/predicate checks. The selected Cosign `3.1.3+dirty` binary comes from the Arch Linux repository package `cosign 3.1.3-1`; the package signature was verified through the Arch keyring (Carl Smedstad, fingerprint `EB3D764FF5D87E0818A3E0E5F05E8C12131AEB5E`) and the selected binary is SHA-256 locked and admitted only through the standardized-bundle verification path, with a minimum version of 3.0.6 and explicit `--check-claims=true`. The August 2026 legacy-bundle/keyless bypass is handled by rejecting legacy bundle shapes before Cosign runs; the advisory explicitly states that the standardized bundle path is not affected. Public-key mode is exercised and PASS. Keyless identity mode is implemented as a policy shape but remains NOT_EXERCISED until identity + issuer + transparency-log integration evidence exists. The distribution package is a verified tool-selection source, not a claim that the bytes are an upstream Sigstore release asset.
- Local signing boundary: `sigstore-local-signing-config-v1.json` is a standard Sigstore SigningConfig v0.2 with Fulcio/OIDC/Rekor/TSA service lists empty. It exists so self-managed/local signing does not silently create external transparency-log or identity-service effects. Public/keyless release signing remains an explicit operational action outside validator execution.
- Package assembly: the Temporal package activity now delegates OCI 1.1 layout/manifest/blob/referrer mechanics to pinned ORAS 1.3.4. Artifact-specific preflight still revalidates digest-bound verify receipts, VSA/Sigstore trust and optional provenance, while OPA/Rego owns the final `releaseReady` policy decision. Local unsigned packages remain `LOCAL_UNSIGNED_DEVELOPMENT` / `releaseReady=false`; cryptographically verified packages can reach `releaseReady=true` only when all required verification and assembly facts are satisfied. The retired custom `package-index.json` and `release-manifest.json` are no longer produced.

## WebKit host boundary

Playwright WebKit 26.6 was downloaded and pinned, but the Playwright fallback build targets Ubuntu 24.04 ABIs. The current Arch host provides newer incompatible SONAMEs (for example ICU 78 rather than ICU 74), so local WebKit launch is **not** accepted. We will not create ABI symlinks or fake older library identities. WebKit release acceptance belongs in an officially supported Playwright Ubuntu/CI/container runner.

## Current non-claims / blockers

- The repaired 8-slide PDU/SDU Golden candidates still require exact Microsoft PowerPoint primary-target render/visual/PDF/read-back closure after the Windows/WSL substrate becomes healthy.
- Pandoc DOCX and XlsxWriter XLSX have structural acceptance but not current Microsoft Word/Excel target standing because the Windows interop substrate is blocked independently.
- The PDF/UA-2 validator path is active, but no production source artifact is yet claimed PDF/UA-2 compliant.
- WebKit local Arch standing is blocked by supported-host ABI compatibility, not by HTML semantics.
- Figma remains an external design-system/component source rather than canonical Office document authority.
- The Artifact Temporal worker is deployed from `/root/projects/ordivon-artifact-v2` against production-green Temporal (`127.0.0.1:17233`). Detached-workspace apply remains forbidden. Source-authority acceptance, development-only durable-workflow evidence and runtime re-materialization are recorded in `docs/SOURCE_AUTHORITY_ACCEPTANCE_20260912.md`.

## Doctor

`scripts/artifact_delivery_toolchain_doctor.py` validates the cross-format profile matrix, selected package versions, deterministic PPTX/DOCX/XLSX generation through the shared Open XML SDK gate, qpdf/veraPDF availability, the pinned Nu Html Checker asset, validator-produced SLSA VSA structure/bindings, and local Chromium/Firefox browser smokes. The web-profile integration smoke requires HTML conformance + Chromium/Firefox + axe to pass while separately requiring the current Arch WebKit target gate to remain fail-closed. WebKit is reported as a supported-runner requirement rather than falsely promoted from an unsupported Arch launch. The doctor intentionally does not convert mechanical PASS into Office target, visual, PDF-profile conformance, WebKit release, cryptographic VSA authenticity, accessibility-use or destination-delivery PASS.

## Stable Artifact Python carrier

The production Artifact CLI no longer uses a repository-local `.cache/artifact-delivery-venv` as its default interpreter. `scripts/artifact_delivery_environment.py` publishes versioned generations below `/root/.local/share/ordivon-workstation/artifact-delivery-python-v1/` and atomically moves only the `current` symlink. Artifact now owns a standard `pyproject.toml + uv.lock` package closure under `artifact-delivery/python-uv/`; reconstruction uses `uv sync --frozen --offline` against exact CPython `3.14.6`, with all accepted distribution versions—including `lxml 6.1.3`—pinned in the lock. The generation binds the exact interpreter bytes and a byte-tree digest of the complete read-only `.venv`; the stable `bin/python` carrier re-verifies those identities and package/native-library observations before every delegated Artifact execution. No Workstation `isolated-equipment` or host `libxslt` package carrier is required by this Python runtime.

This closes a production-path defect rather than changing Artifact semantics: test workspaces may still create disposable environments, but Temporal, the toolchain Doctor and normal Artifact execution reference the stable managed carrier. The separate Temporal SDK environment remains separate by design. Pandoc, veraPDF, Nu Html Checker, Cosign, .NET and browser/Office targets retain their own selection/provenance gates and are not promoted by Python-environment readiness.
