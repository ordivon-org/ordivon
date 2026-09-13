# Artifact — Software Release / Linux ELF R1

## Standing

`SHADOW_PROFILE_LIVE_PROVEN`

`software-release-linux-elf-executable-r1` verifies a bounded final Linux/x86-64 native executable release. It is deliberately separate from the OCI image profile and from producer/build authority.

## Authority split

```text
Producer / Engineering
  source + toolchain + export preset/template
  build/export execution
  reproducibility evidence
             ↓ exact final bytes
Artifact
  byte identity
  ELF technical facts
  final-byte runtime readback
             ↓
Distribution / platform tooling
  signing / notarization / store upload / rollout
```

A valid Artifact PASS therefore does not mean that Artifact built the executable, and a reproducible producer build does not mean a platform release occurred.

## Mature external capabilities

R1 uses three existing system capabilities rather than a custom binary parser or custom sandbox:

- `file` / libmagic 5.48 for an independent descriptive file-class view;
- GNU `readelf` 2.47 for ELF header and program-interpreter facts;
- Bubblewrap 0.11.2 for bounded final-byte runtime readback.

The Bubblewrap invocation unshares the network namespace, mounts the exact release bytes read-only, exposes only `/usr`, `/bin`, `/lib*`, and `/etc` from the host as read-only runtime substrate, and supplies ephemeral tmpfs-backed HOME/XDG state. This is a readback environment, not a claim of complete security isolation against hostile code.

## Game pressure test

The current Game producer is the minimal Godot production cold-start slice. Game/Engineering independently owns:

- native `project.godot` and `export_presets.cfg` semantics;
- exact Godot editor identity;
- exact matching Linux release export-template identity;
- clean `.godot` state before each export;
- two complete cold exports with byte-identical SHA-256;
- producer-side execution of the exported binary.

The current exact final executable is 73,473,208 bytes with SHA-256:

`ed7906d6641f30afcecd142e8fe8716720bab5b317c24dfeebc19ddcb09af30c`

Artifact independently observes it as ELF64, little-endian, System V, x86-64, `ET_EXEC`, with interpreter `/lib64/ld-linux-x86-64.so.2`, and executes those exact bytes in the bounded Bubblewrap readback environment. The readback exits `0`, emits `ORDIVON_GAME_COLD_START_OK`, and writes no stderr.

## Claim boundary

R1 does not establish generic source-to-binary reproducibility, complete sandboxing, SBOM/vulnerability/signature/provenance properties, signing/notarization, store-generated package identity, store upload, rollout safety, cross-platform behavior, Game quality, Player Value, rights, or commercial readiness. Those remain separate capabilities/authorities.
