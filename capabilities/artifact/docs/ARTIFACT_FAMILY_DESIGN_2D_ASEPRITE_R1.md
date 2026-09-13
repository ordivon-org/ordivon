# Artifact E2E — Design 2D / Aseprite Horizontal Sheet R1

## Standing

`SHADOW_PROFILE_LOCAL_LIVE_PROVEN`

R1 covers one bounded source-to-derivative workflow: an exact `.ase`/`.aseprite` editable source is loaded by the Workstation-managed Aseprite binary and exported in batch mode as a horizontal RGBA sprite sheet plus Aseprite `json-array` metadata with frame tags listed. Artifact does not parse or replace Aseprite's editable file semantics.

The native command shape is fixed to batch mode with `--list-tags`, `--sheet-type horizontal`, `--format json-array`, and contract-bound output basenames. Two independent clean export directories must produce byte-identical PNG and JSON output. Their exact SHA-256 values and native sheet dimensions/frame count must match the object contract. The generated PNG is then independently delegated to `still-image-png-srgb-r1`.

## Managed authority

The current Workstation equipment projection resolves `game-aseprite-e1` to the managed Aseprite carrier under `/opt/ordivon/external/aseprite/1.3.17.2/aseprite`, bound by exact executable digest. The CLI reports `Aseprite 1.x-dev`; R1 therefore treats the Workstation equipment binding and executable digest—not the display string alone—as physical capability identity.

Aseprite's official CLI supports batch conversion, `--sheet`, `--data`, `--format`, sheet layout selection and tag listing; the `.ase/.aseprite` binary format is separately documented by the Aseprite project. R1 consumes those native capabilities instead of creating an Ordivon sprite AST.

## Current Game pressure test

At Game revision `14dfc8cf479468025ba786f5451df36ce91bfd58`:

- `rescue-expression.aseprite` deterministically regenerates `rescue-expression.png` byte-for-byte (`3c06b38a...`) and regenerates the retained Aseprite metadata JSON byte-for-byte (`0fdadf83...`). Native metadata reports 3 frames and the source tags `idle`, `move`, `impact`.
- `rescue-specialists.aseprite` deterministically regenerates `rescue-specialists.png` byte-for-byte (`f7e2f2c6...`). Its native Aseprite metadata reports one 72×24 frame. The repository's `rescue-specialists.json` is not Aseprite metadata; it is a Game-owned actor/role mapping and is deliberately outside Artifact interpretation.

Both generated PNGs independently pass `still-image-png-srgb-r1`.

## Boundary

Artifact proves exact source admission, exact managed exporter identity, deterministic native export, exact derivative/native-metadata digests, and PNG artifact conformance. Game owns the meaning of frame tags, actor/role identity, animation/gameplay semantics and caller-owned metadata. R1 does not claim other sheet modes, layer/slice/tilemap exports, palette conversions, artistic quality, rights, or cross-version reproducibility.
