# Media v2 — OTIO editorial boundary R5

## Decision

OpenTimelineIO owns editorial interchange semantics. Media v2 does not create a second timeline model and Resolve does not own canonical editorial truth.

The pinned R5 tool is `opentimelineio==0.18.1`, matching the repository's existing Resolve optional dependency. Its official `otiotool` CLI already supplies timeline statistics, track/clip/media listings and source-range verification.

## External-first gate

```text
canonical .otio
  -> otiotool 0.18.1
       --stats
       --list-tracks
       --list-clips
       --list-media
       --verify-ranges
  -> retained raw inspection
  -> bounded profile assertions
  -> digest-bound EvidenceReceipt
```

R5 deliberately does not reimplement OTIO time arithmetic, traversal, adapters, or source-range validation.

## Important falsifier

`otiotool --verify-ranges` reports `SOURCE MEDIA OUT OF BOUNDS` for a deliberately invalid Clip but still exits with status 0. R5 therefore retains and evaluates the official inspection output rather than promoting process exit zero to editorial validity.

## Current Runtime Introduction snapshots

The official OTIO inspection reports:

- `assembly.v0.otio`: 78 seconds, one video track, eleven in-bounds clips; assembly skeleton.
- `assembly.v1.otio`: 78 seconds, one video track, one in-bounds picture-master clip.
- `assembly.v2.otio`: 78 seconds, one video track plus one audio track, two in-bounds clips; current A/V review candidate.

R5's current profile targets `assembly.v2.otio` without deleting historical v0/v1 snapshots.

## Resolve private delta

The following remain valid Resolve-specific adapter responsibilities for now:

- Windows/WSL path and Resolve scripting host discovery;
- runner installation into the Resolve/Fusion script surface;
- Resolve product/version/capability observation;
- local path materialization needed by the host;
- disposable Resolve project creation/import/readback/cleanup;
- evidence about Resolve-private state that OTIO explicitly does not represent.

The following are **legacy compatibility candidates**, not future Media ownership:

- generic timeline stats/traversal;
- generic clip/media-reference enumeration;
- generic OTIO source-range checks;
- generic OTIO serialization/deserialization;
- independent editorial time arithmetic where OTIO/otiotool already supplies the fact.

No new generic editorial validation should be added to `resolve_adapter.py`.
