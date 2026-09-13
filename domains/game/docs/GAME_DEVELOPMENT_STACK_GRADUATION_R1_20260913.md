---
schema_version: 1
id: game.development-stack-graduation-r1-20260913
title: Game Development Stack Graduation R1
profile: engineering-acceptance
lifecycle: active
source_role: canonical-acceptance
visibility: internal
owners:
  - ordivon-game
updated: 2026-09-13
---
# Game Development Stack Graduation R1

## Decision

The selected external-first Godot development foundation is **READY** for formal greenfield product development within the bounded profile proven below.

This standing is about development mechanics, not player value, market fit, rights, store certification or commercial readiness.

## Proven chain

```text
Godot 4.7.1 host CLI
+ native project.godot / export_presets.cfg
+ GUT 9.7.1
+ godot-ci:4.7.1
        ↓
container headless import
        ↓
container Linux/X11 export
        ↓
real ELF executable
        ↓
host execution
        ↓
ORDIVON_GAME_COLD_START_OK
```

## Accepted components

| Capability | Carrier | Standing |
| --- | --- | --- |
| engine/runtime authority | Godot 4.7.1 official/native CLI | **READY** |
| native project semantics | `project.godot` | **READY / AUTHORITY** |
| native export semantics | `export_presets.cfg` | **READY / AUTHORITY** |
| Godot test framework | GUT 9.7.1 | **READY** |
| containerized CI/export carrier | `barichello/godot-ci:4.7.1` | **READY FOR OFFLINE BUILD/EXPORT** |
| real Linux exported executable | Godot Linux/X11 export | **READY** |
| executable cold-start | real ELF run on host | **PASS** |

## GUT evidence

Exact accepted upstream identity:

```text
GUT tag    v9.7.1
commit     aeb5d4f3f7f0a6c9b5e178876d6c99b791fda605
Godot      4.7.1
```

Acceptance result:

```text
1 / 1 tests PASS
3 assertions PASS
JUnit XML generated
```

Durable Runtime Job:

```text
job-01a09aaf-b3ab-7d33-8b11-bede97705dbc
```

A later redundant network re-clone timed out before test execution; that is not regression evidence and does not replace the exact-tag acceptance above.

## godot-ci acquisition and identity

Direct Docker Hub access was unreliable, so image acquisition used the existing mature Surfpath isolation mechanism rather than changing machine-wide routing.

Qualified transport:

```text
Surfshark WireGuard
KR / ICN egress
path sha256:1945fe0636c63e2cf00d4487c695a7c1d5ca3e24c5964ee4f0bad32526254f25
```

Image was downloaded into standard OCI Image Layout and imported into host container storage.

```text
image       docker.io/barichello/godot-ci:4.7.1
image ID    c22f67612c9eb0e7c52e18d391471ce5c6dba8e43c6d9ff43b77d6d85d9a3723
digest      sha256:15bab564bdd99ae61a12564fc25237130483d1e22da003dc7d039db6f6eded91
OCI layout  /var/cache/ordivon/game/godot-ci-4.7.1-oci
```

Container reports:

```text
4.7.1.stable.official.a13da4feb
```

## Real product-like smoke

Existing repo-owned project:

```text
experiments/production-smoke-r1/godot
```

was copied to an isolated temporary working directory and mounted into `godot-ci`.

The container performed:

```text
godot --headless --editor --import --quit
godot --headless --export-release "Linux/X11" /project/build/cold-start.x86_64
```

Result:

```text
size      73,473,208 bytes
mode      755
SHA256    ed7906d6641f30afcecd142e8fe8716720bab5b317c24dfeebc19ddcb09af30c
```

This SHA256 is identical to the previously accepted host-side bounded reproducibility baseline. Therefore, within this declared project/engine/template boundary, the selected CI carrier reproduced the same export bytes as the local path.

The exported executable was then executed on the host with `--headless` and produced:

```text
ORDIVON_GAME_COLD_START_BOOT
ORDIVON_GAME_COLD_START_OK
exit 0
```

Durable Runtime Job:

```text
job-01a09b08-24eb-75d1-935d-5eefab7947eb
```

## Windows Blender 3D authoring acceptance

The Workstation-owned Windows Blender carrier is accepted for Game 3D authoring through the ordinary professional-software binding:

```text
professional:blender:blender
→ executionTarget: windows_native
→ Blender 5.2.0 LTS
```

The acceptance used two independent Windows Blender processes: the first created and saved a real `.blend` containing a mesh, material, camera, light and keyed rotation animation; the second reopened that saved `.blend`, rendered a 128×128 Eevee PNG and exported a binary glTF 2.0 `.glb`. Godot 4.7.1 then imported the Windows-produced GLB and verified one mesh/surface, a material, one `AnimationPlayer`, and the `AcceptanceCubeAction` animation.

Standing: **READY for Windows-native 3D authoring and Blender→Godot interchange**. Interactive GUI ergonomics were not separately Human-tested; this acceptance proves the executable/authoring/export/consumer chain. Machine-readable evidence is retained in `evidence/blender-windows-game-acceptance-r1-20260913.json`.

A separate Workstation limitation was observed: under WSL memory pressure, Hyper-V `hv_sock` intermittently failed an order-7 contiguous allocation and temporarily blocked Windows-native dispatch. Reclaiming page cache and compacting memory restored the channel. This is an Operations/Workstation reliability concern, not a Blender compatibility failure.

## Bounded non-blocking limitations

### `libfontconfig.so.1` absent inside godot-ci image

The image logs that system font discovery is disabled because `libfontconfig.so.1` is absent. This is **not hidden** and is not generalized away.

Within the accepted profile it is non-blocking because:

- `godot --version` exits 0;
- `godot --headless --version` exits 0;
- project import succeeds;
- Linux/X11 export succeeds;
- exported artifact exactly matches prior host reproducibility hash;
- exported executable runs successfully.

Forward policy is to bundle product fonts for reproducible products rather than depend on ambient CI-system fonts. If a real product demonstrates a requirement for system-font discovery, the container image/package set must be re-evaluated at that time.

### Podman default bridge unavailable in current WSL

Current WSL/netavark cannot create the default Podman bridge. The build/export container does not require network access, so the accepted invocation uses:

```text
podman run --network=none ...
```

This is preferable to mutating workstation networking solely to make an offline CI build container create an unnecessary bridge.

## Scope of READY

`READY` means we can now start formal game product work using:

```text
Godot native project/config
+ GUT
+ Godot CLI
+ godot-ci for containerized build/export
+ existing Engineering / Artifact / Distribution owners downstream
```

It does **not** mean:

```text
player value proven
market fit proven
rights cleared
Steam AppID acquired
store certification passed
commercial release ready
```

Those claims must be earned by the appropriate later product and release evidence.

## Forward rule

Do not add more generic Game infrastructure merely to make the stack look complete. New dependencies activate only when a real product requirement demonstrates a substitution gap.

Machine-readable receipt:

```text
evidence/game-development-stack-graduation-r1-20260913.json
```
