# Artifact Closure R2 — 2026-09-13

Standing: **ACCEPTED_BOUNDED**

## Decision

Artifact Build & Delivery keeps the mature external substrate already present rather than introducing another package or registry system.

```text
artifact / verification evidence
        ↓
OCI 1.1 + ORAS
        ↓
local Zot distribution provider
        ↓
subject + OCI referrers

release trust
        ↓
Sigstore standardized bundle
        ↓
provenance-locked Cosign verifier
```

Ordivon owns only thin orchestration, evidence binding, admission and verification. Zot owns local OCI distribution; Sigstore/Cosign owns cryptographic bundle verification.

## Cosign disposition

The apparent `3.1.0` versus `3.1.3` drift was an ambient-tool confusion, not a broken Artifact trust chain.

Ambient `/usr/bin/cosign` is Arch package `3.1.0-1` and is **not** the selected Artifact verifier. Artifact selects:

`/opt/ordivon/external/artifact-toolchain/cosign/3.1.3/bin/cosign`

The selected verifier remained exactly bound to the existing toolchain lock:

- version: **3.1.3**;
- binary SHA-256: `eeeb54d099d9ca2520e2cfd5068c9136b454bb1b7b1e027afda7938c497953e7`;
- Arch package SHA-256: `281c52a1020225d22638f46e4b687c18ecf06d4f796055604a90483d5e60cc69`;
- detached package-signature SHA-256: `a9d4441f15bec19285722f1681256e6baca5929eb54e7266522ffd233052b47b`;
- signer fingerprint: `EB3D764FF5D87E0818A3E0E5F05E8C12131AEB5E`;
- package-signature verification: **GOOD**;
- locked version match: **true**;
- locked binary digest match: **true**.

A fresh R2 live probe generated an ephemeral public/private key pair, emitted a standardized Sigstore v0.3 bundle with Cosign `attest-blob`, and verified that bundle through the Artifact verifier. The temporary signing directory was automatically removed and no private key was persisted.

Observed probe:

- bundle media type: `application/vnd.dev.sigstore.bundle.v0.3+json`;
- verification: **PASS**;
- authenticity: **VERIFIED**;
- embedded signed statement match: **true**;
- Cosign verification: **PASS**;
- transparency-log entries: **0** by design for this local public-key probe.

This graduates the public-key standardized-bundle path only. Keyless Fulcio/OIDC/Rekor identity/tlog release trust remains **NOT_EXERCISED**.

## Zot problem found

The existing Zot data itself was healthy, but its stopped Podman container still mounted configuration from an expired Runtime experiment workspace:

`/var/lib/ordivon/runtime/workspaces/ws-artifact-v2-substrate-r1-20260912/experiments/artifact-v2-substrate-r1/zot-config.json`

That file no longer existed.

The persistent registry store remained intact at:

`/root/.local/share/ordivon-workstation/artifact-v2-zot-r1`

Before the R2 closure smoke it still exposed the five pre-existing repositories:

1. `ordivon/artifact-v2-smoke`
2. `ordivon/pdu-sdu-34x10-golden`
3. `ordivon/presentation-native-smoke`
4. `tools/apache-tika`
5. `tools/docling-serve-cpu`

R2 therefore repaired **deployment authority**, not registry data.

## Stable Zot deployment

Artifact-v2 now owns the source deployment definitions:

- `config/zot/local-registry-r1.json`;
- `systemd/ordivon-artifact-v2-zot-r1.container`.

Implementation revision:

`4216e8d87dc5c62a459616f98bb7ec62e4ab5195`

The Zot config is materialized to:

`/etc/ordivon/artifact-v2/zot/config.json`

The rootful Podman Quadlet is materialized to:

`/etc/containers/systemd/ordivon-artifact-v2-zot-r1.container`

Source and materialized SHA-256 values are exact:

- Zot config: `5ca8131f6096c63d872f2bd4dfd506efabbad32c12a25eaec483ae9e909d8b7f`;
- Quadlet: `b8070d738ff819cc4a65b9daf0bcb803f345f813390eb2006a91e1d419a8c407`.

The Quadlet pins the exact existing image:

`ghcr.io/project-zot/zot-linux-amd64@sha256:95a837a0afacf5b7edc0c92493f04beee6891989b8d2fd50a00cf65a1e6d4fd5`

and preserves the existing registry storage bind without copying or migrating it.

The resulting systemd service is `active`; its enablement is generated from the Quadlet `[Install]` relationship.

## Network boundary

The current WSL substrate cannot create Podman's default netavark bridge; a direct test failed with:

`Netlink error: Operation not supported (os error 95)`

The historical Zot container already used host networking. R2 retains `Network=host` rather than introducing a known-broken bridge dependency, while Zot itself binds only:

`127.0.0.1:5080`

This is a bounded workstation-local compromise, not a recommendation to use host networking for a public registry.

## OCI 1.1 roundtrip graduation

R2 performed a real roundtrip through the stable service using managed ORAS 1.3.4.

Subject:

- repository: `ordivon/artifact-r2-closure-smoke`;
- tag: `20260913-r1`;
- artifact type: `application/vnd.ordivon.artifact.r2.subject.v1`;
- manifest digest: `sha256:79b634b0500d769fdaf43d6284ce96004ea9802345226193f3a3a1979b9fc095`;
- payload SHA-256: `ce2fb16dd10090f3943d2e5c45185362882cffc450d02f62718b040ec1f1f950`.

Attached OCI referrer:

- artifact type: `application/vnd.ordivon.artifact.r2.evidence.v1+json`;
- manifest digest: `sha256:ffb38f3fb680614d837a09e3d7ea1ad34f7d93f1948a6541eadc5fa331a90e9a`.

The subject was pulled and byte-compared successfully. ORAS discovery returned exactly the expected referrer.

The Zot systemd service was then restarted. After restart:

- `/v2/` was healthy;
- ORAS discovery was byte-identical to the pre-restart result;
- the subject manifest digest was unchanged;
- the referrer digest was unchanged;
- the subject pulled again with the same payload SHA-256.

The small `ordivon/artifact-r2-closure-smoke` repository is intentionally retained as durable closure evidence. It is not an application artifact or production release.

## Reusable registry doctor

`scripts/artifact_registry_doctor.py` now checks:

- source Zot config boundary;
- source Quadlet boundary;
- source/materialized config identity;
- source/materialized Quadlet identity;
- Zot systemd service state;
- exact Podman image/network/rootfs/mount boundary;
- pinned image presence;
- loopback-only listener;
- OCI Distribution `/v2/`;
- catalog reachability;
- optional closure-smoke subject/referrer discovery.

Post-commit R2 execution: **11/11 PASS**.

## Artifact regression evidence

Before implementation commit:

- targeted Artifact/Sigstore/OCI/Temporal files: **85 run = 83 PASS + 2 environment-specific skips**;
- entire Artifact repository: **276 run = 274 PASS + 2 skips**;
- Artifact toolchain doctor: **17/17 PASS**;
- registry doctor: **11/11 PASS**.

The two full-suite skips are existing local-environment capability boundaries rather than R2 failures. The complete toolchain doctor independently resolved its currently selected Nu/veraPDF paths as PASS.

## Final ownership boundary

| Concern | Owner after R2 |
|---|---|
| OCI layout / subject / referrers | OCI 1.1 + ORAS |
| Workstation-local OCI distribution | Zot |
| Zot lifecycle | Podman Quadlet + systemd |
| Zot deployment definition | Artifact-v2 source repository |
| Registry payload storage | existing Zot store bind |
| Standardized signature bundle | Sigstore bundle v0.3 |
| Selected verifier | provenance-locked Cosign 3.1.3 |
| Release admission and evidence composition | thin Artifact orchestration/policy |

## Nonclaims

R2 does not claim:

- public or multi-user registry readiness;
- TLS/authentication graduation;
- remote availability, HA, replication or disaster recovery;
- keyless Fulcio/OIDC/Rekor release trust;
- that transport/storage success proves artifact correctness, scientific validity, visual acceptance, business acceptance or destination delivery.

Those concerns remain separate and are activated only when a real consumer requires them.
