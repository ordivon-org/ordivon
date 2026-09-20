# Distribution v2 R10 — free local distribution preflight

Status: **HISTORICAL / FORWARD EXECUTABLE RETIRED 2026-09-20**
## Purpose

R10 closes the platform-independent part of software-store distribution without buying a Steam App credit and without inventing a local Steam replacement.

The boundary is:

```text
product/build owner
    ↓ exact candidate directory A / B
Distribution local preflight
    ├─ exact tree freeze
    ├─ forbidden-path / Steam-exclusion collision gate
    ├─ Linux ELF64 x86-64 + dynamic dependency sanity
    ├─ provider-compatible Steam VDF template rendering
    ├─ clean install through mature rclone local sync
    ├─ A → B update with exact-tree stale-file detection
    ├─ B → A rollback
    ├─ uninstall + clean reinstall
    └─ launch from installed bytes
```

Distribution does not generate SBOMs, SLSA/in-toto provenance, Sigstore trust, vulnerability evidence, secret-scan evidence, or `releaseReady`. Those remain Artifact-owned release evidence.

## Steam boundary

The generated templates follow Valve's documented SteamPipe `AppBuild` / `DepotBuild` structure and use `ContentRoot`, `BuildOutput`, `Preview`, `Depots`, `FileMapping`, `FileExclusion`, `LocalPath`, `DepotPath`, and `Recursive` fields. The AppID and DepotID remain explicit placeholders.

R10 never logs in to Steam, never registers a build with Steam's backend, never creates a depot manifest or BuildID, and never claims a real SteamPipe Preview PASS. A real Preview/build requires a real app and an account with the corresponding app permission.

The local lifecycle test deliberately uses `rclone sync` rather than a custom updater. Its purpose is to validate candidate/install/update/rollback semantics and stale-file elimination; it does not copy SteamPipe chunking, CDN, entitlement, manifest, branch, or rollback infrastructure.

## Forward ownership

- Game/product owner: product semantics and candidate build bytes.
- Engineering: build process and reproducibility boundary.
- Artifact: release-object verification, SBOM/security evidence, provenance/trust and release standing.
- Distribution: provider mapping, delivery lifecycle, external-effect admission, provider-native execution/readback.
- Steam: SteamPipe, depots, manifests, BuildIDs, branches, CDN, client install and platform acceptance.

## R7 compatibility note

The older R7 `package-index.json` handoff represents historical pre-OCI Artifact integration. Current Artifact explicitly retired that custom relationship tree in favor of standards-based OCI/referrer mechanics. R10 does not consume or extend the R7 package-index helper. A future Artifact→Distribution release handoff must bind current Artifact release evidence directly rather than reviving `package-index.json`.

## Graduation language

A passing R10 receipt may claim only `LOCAL_DISTRIBUTION_PREFLIGHT_PASS_REAL_PLATFORM_DEFERRED`.

It may not claim Steam backend acceptance, SteamPipe Preview, Steam AppID/Depot/BuildID, Steam CDN install, public release, Artifact `releaseReady`, SBOM, provenance, signature trust, player value, or commercial readiness.
