# Artifact E2E — Software Release Family R1

## Standing

`SHADOW_PROFILE_LIVE_PROVEN`

Software Release R1 validates a bounded, single-platform OCI image release object. It does not replace Engineer E2E or build software itself.

The boundary is explicit:

```text
Engineer / build system
    ↓ candidate bytes
Skopeo normalization
    ↓ final OCI Image Layout
Artifact Software Release R1
    ├─ OCI identity/config
    ├─ rootfs read-back
    ├─ SBOM
    ├─ frozen-snapshot vulnerability evidence
    ├─ secret evidence
    └─ network-disabled runtime acceptance
```

## First bounded profile

`software-release-oci-image-r1`

```text
family          software-release
representation  container-image
format          OCI Image Layout / OCI image manifest
platform        linux/amd64
purpose         release + deployment
```

R1 selects OCI Image Format 1.1 semantics and a single manifest. Multi-platform image indexes, registry policy and deployment orchestration remain outside R1.

## Artifact identity

A key early falsifier was that a Podman `containers-storage` image digest and the digest of the Skopeo-normalized OCI layout need not be the same. Transport/storage normalization can change representation metadata.

Therefore R1 defines the release Artifact identity as:

> the manifest descriptor digest in the **final OCI Image Layout**.

Builder-local storage identities are provenance/source evidence only.

The live object identity is:

`sha256:974f718df05cab8852f96363b0404d51777748d5bbc6e665cb36a58f961af018`

with:

- config `sha256:c69aaec3d29824d684c24ed268536e3d7ce4c6a026aa9012eb62c526681e817d`;
- layer `sha256:d26bb946928facdcdf8de9b80bd07e0ae70dd2bdc1b2f01af4aa5170c804e9d8`;
- linux/amd64;
- entrypoint `/app`;
- working directory `/`.

Every referenced descriptor is re-hashed and size-checked from the layout before it can contribute evidence.

## Object contract

Schema:

`artifact-delivery/shadow-contracts/software-release-oci-contract-v1.schema.json`

The object contract binds:

- final OCI manifest digest;
- OS / architecture;
- entrypoint / working directory;
- exact expected rootfs file digests;
- runtime network/exit/stdout/stderr behavior;
- frozen vulnerability-DB snapshot and maximum vulnerability count;
- maximum secret count;
- SBOM format and required package identities.

The smoke object binds `/app` to:

`23b4d1eeede0beafe83efee19c141fca536ac98fc936014f6217f65459f6f135`

## Patched build substrate vs Artifact authority

The first smoke built with host Go 1.26.5 was structurally valid and runnable, but the frozen Trivy DB found multiple HIGH vulnerabilities in the embedded standard library. R1 did not weaken the security threshold or allow-list the findings.

The smoke build substrate was upgraded to official stable Go 1.26.6, whose official archive was pinned by SHA-256:

`708effb774be8237570d0add163225abbdfaf4fca28b2611df167beba4feef89`

With the same source, the patched object produced zero vulnerabilities under the exact same frozen DB snapshot.

This demonstrates:

```text
Runnable != Releasable
StructurallyValidOCI != SecurityPolicySatisfied
```

Go remains builder evidence only. Artifact R1 never recompiles the candidate during verification.

## Reproducibility evidence

Two independent patched Go builds, followed independently by Podman OCI build and Skopeo normalization, produced byte-identical final OCI layout trees:

- same index;
- same manifest;
- same config;
- same layer;
- same `oci-layout` file.

This is source/build-substrate evidence. The per-artifact verifier consumes the resulting layout rather than rerunning the build.

## SBOM

Syft 1.50.0 generates SPDX 2.3 JSON directly from the exact final OCI layout.

The smoke SBOM:

- has `spdxVersion = SPDX-2.3`;
- identifies a CONTAINER package whose version/checksum is the final OCI manifest digest;
- identifies Go `stdlib go1.26.6`;
- contains three packages in the bounded smoke artifact.

R1 explicitly does **not** claim that SPDX 2.3 is ISO/IEC 5962:2021. ISO/IEC 5962:2021 corresponds to SPDX 2.2.1; SPDX 2.3/3.0 are separate specification revisions.

Live SBOM SHA-256:

`33dce89348e8ff280aa137deffc325a1c2ef620cb56fe8dedfa4ba50d5a07a56`

## Vulnerability evidence

Trivy 0.73.0 uses a frozen vulnerability-intelligence snapshot:

`/opt/ordivon/external/trivy-db/20260912-r1`

Database SHA-256:

`63b60b5493b28e6ce5b3a45753865055f890cea750b7138922963e25446975bf`

Metadata SHA-256:

`ad131f125e7913b23abbbe563e79920c333e52e290beb33a050bb640073a10b4`

The verifier runs with `--skip-db-update --offline-scan`. Therefore historical PASS means only:

> zero findings under this exact frozen vulnerability-intelligence snapshot.

It does not mean “no vulnerability can ever be discovered”.

Live vulnerability count: **0**.

Live report SHA-256:

`d6fc6f56c31f262af063076e7dcb6c6aae343726ec2e3ee7745e61a38972e86f`

## Secret evidence

Trivy secret scanning is run over the rootfs exported from the **final OCI-layout read-back image**, not the Engineer build directory.

Live secret count: **0**.

Live report SHA-256:

`a6c5d8891d95f2f82a12531c7401dfc0a7c453af08427fa997befa0226e6e370`

The environment safety layer does not permit creation of real test credentials solely to exercise a negative control. Therefore the negative policy decision is tested with a synthetic Trivy report object containing one secret finding, while the real scanner provides the clean-rootfs positive evidence.

## Read-back runtime

The exact final OCI layout is imported through Skopeo into a fresh temporary local tag. Podman creates the read-back container with `network=none`, exports the rootfs for file/security evidence, then executes that exact read-back image.

Smoke acceptance:

```text
exit code  0
stdout     ordivon-artifact-software-release-r1\n
stderr     empty
network    none
```

A test object with different runtime stdout passes the static OCI/security gates but still fails the Artifact contract.

## Falsifiers proven

Nine focused tests pass:

1. exact OCI release + matching contract → PASS;
2. valid OCI layout but wrong expected manifest digest → FAIL;
3. layer byte tampering → descriptor-integrity FAIL;
4. valid OCI bytes but wrong expected entrypoint → contract/config FAIL;
5. synthetic scanner report with one secret exceeds a zero-secret policy → FAIL;
6. host Go 1.26.5 negative-control image is runnable but frozen-DB vulnerability policy → FAIL;
7. changed runtime output while static gates pass → runtime contract FAIL;
8. non-Linux contract request → schema/profile FAIL before external evidence promotion;
9. frozen tool/DB identities match the proven substrate.

## Trust envelope boundary

Artifact R1 does not duplicate the existing generic release-trust machinery. SLSA/in-toto/Sigstore signing, provenance and release-policy authorization remain in the common Artifact delivery/release envelope.

The family profile verifies the software object. The generic trust envelope answers who/what attested to that object and whether release authority accepts it.
