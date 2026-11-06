---
name: media-native-processing
description: "When a real Ordivon Media/Studio consumer needs technical inspection of a selected AV file, audio programme, OpenTimelineIO timeline, or timed-text document, reuse the existing source-owned Studio processing profiles and native adapters via the Agent surface. Select by exact digests, compile a Runtime proposal, execute only through Runtime, and read raw evidence. Not for generic editing, publication authority, or installing speculative tools."
compatibility: "Project-level Agent Skill; Python 3 and Media source needed for discovery, installed native tools only for selected effects. Runtime local_linux required for the existing Bash probes."
metadata:
  source-authority: "Existing Ordivon Studio Agent surface and FFmpeg/FFprobe, ASWF OpenTimelineIO, IMSC/TTML ttconv"
---

# Media Native Processing — use existing capability, not a second engine

## Trigger and source authority

Use only after a caller identifies one selected source artifact and a real
consumer's requested technical profile. Ordivon Media owns profile selection and
technical interpretation; Runtime owns execution; source owners and Artifact own
actual bytes; downstream consumer/Distribution owns acceptance and publication.
An unknown tool, source or rights standing is **UNKNOWN**, not success or failure.

Primary implementation and contract:
- `capabilities/media/src/ordivon_studio/agent_processing.py`
- `capabilities/media/src/ordivon_studio/agent_surface.py`
- `capabilities/media/processing/README.md` and `processing/profiles/*.json`
- `capabilities/media/planning/lego-plan-r1.json`
- `capabilities/media/src/ordivon_studio/qc.py` (generic native FFprobe observation and profile-specific QC)

Read the current source rather than reimplementing FFmpeg, OpenTimelineIO,
TTML parsers, another registry, daemon, or queue.

For a consumer requiring raw container/stream observations rather than
an existing fixed Processing Profile, use the established
`ordivon_studio.qc.probe_media` directly under its authorized Runtime
execution; it delegates JSON to FFprobe. The Blob/CAS owner
`ordivon_studio.assets` does not perform technical QC. Do not create
another subprocess probe wrapper or infer profile approval from raw fields.

## Procedure — the shortest actual composition

1. From `capabilities/media`, discover the available Studio actions:
   `python3 scripts/studio-agent-surface.py`. Discover the source profiles
   with `python3 scripts/studio-agent-surface.py studio_processing_profiles
   --arguments '{}'`. This read is bootstrap-free on revisions that support
   dependency-light discovery. If the installed revision requires its pinned
   Studio Python environment, materialize per `scripts/materialize-python.py`
   and invoke via `.venv/bin/python`. Do not install external native providers
   during discovery.
2. Choose **one existing** catalog row: its `id` is the `profileId` argument; retain the exact `profileDigest`,
   `adapterPath` and `adapterDigest` from the exact returned catalog.
   `externalToolReadiness=not-observed` is not a claim of installation.
   If the adapter is missing or the kind unknown, stop selection and report
   the missing capability; do not invent a successful tool receipt.
3. Invoke existing `studio_processing_probe_plan` with the selected
   `profileId`, `expectedProfileDigest`, `expectedAdapterDigest`,
   consumer-selected `inputPath` and `evidenceDirectory`. It returns
   a **nonexecuting** plan including `execution` fields and
   `expectedReceipt`. A digest mismatch rejects the stale choice.
4. Submit the plan's concrete `execution` fields through the normal Runtime
   `workspace.exec` with the real Workspace ID. Confirm source bytes and
   native execution from the Job receipt, not from the discovery catalog.
   OTIO and TTML adapters already invoke `processing/bin/otiotool-pinned.sh`
   and `processing/bin/ttconv-pinned.sh`, resolving exact versions via
   `mise` and `uv tool run` only when selected. The ttconv CLI is `tt`, not
   `ttconv`; absence of global `otiotool` or `ttconv` on PATH does not prove
   these pinned adapters unavailable. Never install a duplicate provider.
5. Observe the exact Runtime Job and read the emitted `evidence.json`
   plus native tool observations. Bind artifact/profile/tool hashes and exact
   acceptance predicates to the **real consumer**. Negative fixture failure
   is an expected falsification result, not a tool-install success.
6. Delete only this invocation's disposable evidence/cache after its
   actual consumer has read it. Keep source masters, selected production
   artifacts and exact provenance with their owning system.

## Verification and formal boundary

The current four native profile families are AV structure (FFprobe), audio
loudness/true peak (FFmpeg), editorial timeline (OpenTimelineIO otiotool),
and timed text (TTML ttconv). From the Media root, run the applicable
existing processing/tests/smoke.sh, processing/tests/audio-smoke.sh,
processing/tests/otio-smoke.sh or processing/tests/timedtext-smoke.sh
only when changing that adapter or disputing its contract; avoid cosmetic tests.

As an R2.1 LEGO composition, discovery supplies source-bound IDs and digests;
the compiler consumes those IDs and produces a Runtime proposal; Runtime
produces effect evidence; the consumer checks the real postconditions.
The key invariant is **technical QC does not entail aesthetic, semantic,
rights or publication approval**. Source/probe drift, tool state, final
consumer acceptance and runtime cost stay explicit unresolved obligations
when not observed.

## Stop condition

Stop when the selected consumer has its exact real technical evidence or the
earliest missing precondition is identified. Never promote a probe catalog or
a success exit code into a broad Media production release verdict.
