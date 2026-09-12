# CycloneDX VEX acceptance R1

Date: 2026-09-12
Standing: `CYCLONEDX_1_7_SCHEMA_VALID + EXACT_SBOM_COMPONENT_BINDING + TRIVY_SBOM_VEX_INPUT_ACCEPTED`.

## Purpose

Security v2 does not create an Ordivon-specific vulnerability-disposition format. CycloneDX 1.7 already provides VEX semantics through vulnerability `analysis.state`, `justification`, `response`, `detail`, and `affects.ref`.

The preferred lifecycle keeps inventory and exploitability distinct:

`SBOM -> detached VEX -> remediation decision -> rebuild -> fresh SBOM/scan -> reverify`

A detached VEX is appropriate because an SBOM can remain stable while exploitability analysis changes.

## Physical R1 acceptance

Syft `1.50.0` generated a real CycloneDX 1.7 SBOM for `fixtures/clean`. The observed SBOM contained `packaging@25.0` with its provider-generated `bom-ref` and a unique BOM serial/version.

R1 then generated an acceptance-only detached CycloneDX VEX document. Its vulnerability ID is deliberately synthetic (`SECURITY-V2-ACCEPTANCE-R1`) so this test cannot be confused with a real vulnerability claim about `packaging@25.0`.

The VEX `affects.ref` used an exact CycloneDX BOM-Link to that component:

`urn:cdx:<sbom-uuid>/<sbom-version>#<exact-provider-bom-ref>`

Observed evidence digests:

- SBOM SHA-256: `8ba699aa70a684e0fadc85566b5c5763fef3125d4f17807d8883e34a238377e4`;
- VEX SHA-256: `904499d2846c98b1d3bb8a1d0413dfc284f184f882afd5a33caae22e0dcdde92`;
- CycloneDX 1.7 JSON schema SHA-256 used for acceptance: `71152f97948eeeca2fd4a1434a9d29aab35d377be11828b504d029dfeeb1925a`.

`check-jsonschema 0.34.0` validated the VEX against the official CycloneDX 1.7 schema.

Trivy `0.73.0` correctly rejected applying CycloneDX VEX directly to `trivy fs`, stating that CycloneDX VEX is used with a CycloneDX SBOM. R1 then followed the native provider composition:

`Syft CycloneDX SBOM -> trivy sbom --vex <detached-vex>`

That path succeeded without an adapter. The resulting Trivy JSON SHA-256 was `15bdacdbde203aa15d06491c1419d2187818be4eab32976198303c1c86a74f32`.

## Security binding contract

`ordivon_security_v2.vex` validates only the thin residual invariants Security needs:

- both artifacts are CycloneDX 1.7;
- every VEX `affects.ref` binds an exact component from the referenced SBOM through BOM-Link;
- vulnerability identities are unique within the VEX;
- analysis state is a CycloneDX state known to the current contract;
- `not_affected` requires a recognized CycloneDX justification and non-empty analysis detail;
- changed/missing component identity fails closed.

R1 tests explicitly falsify changed component references and unsupported `not_affected` assertions without justification/detail.

## Authority boundary

A syntactically valid VEX is **not** automatically authoritative. In particular:

- scanner detection does not establish exploitability;
- a producer assertion of `not_affected` does not become Security truth merely because it is valid CycloneDX;
- applicability/currentness/issuer authority still require Security policy and exact evidence binding;
- `in_triage` remains unresolved rather than silently clearing a vulnerability;
- after remediation, the artifact must be rebuilt and re-observed instead of reusing stale scan evidence.

R1 closes the standards-format, exact-component-binding, and native Trivy-consumption layers. It does not yet claim a full automated patch/remediation workflow.
