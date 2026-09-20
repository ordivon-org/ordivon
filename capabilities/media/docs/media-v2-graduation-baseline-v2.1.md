# Media v2 Graduation Baseline v2.1

## Decision

Media v2 graduates by evidence gates, not by accumulating tools or by preserving historical R-number sequencing. The historical migration labels drifted as real consumer pressure changed the work (audio became R3, timed text R4, OTIO R5). This baseline therefore freezes stable graduation gates G1-G6.

Media v2 remains a thin composition/control/evidence plane over mature external media tools. It must not become a universal media engine, asset database, review platform, distribution SDK, or source-domain authority.

## External authorities

- Exact bytes use SHA-256 content identity; media types follow the IANA registry.
- Cross-system lineage should use W3C PROV concepts (Entity, Activity, derivation) when interchange is required rather than inventing a Media-specific provenance ontology.
- OCI/ORAS is the preferred immutable artifact packaging/distribution substrate when a real registry/release consumer earns it; tags are not identity and digest-addressed manifests are.
- C2PA is reserved for content-authenticity / signed provenance requirements; it is not required merely to hash or relate local production artifacts.
- Format-specific truth remains with the mature tool/standard already selected (FFprobe/FFmpeg, IMSC/TTML, OpenTimelineIO, Aseprite, etc.).

## Graduation gates

### G1 — Technical media evidence — PASS IN CURRENT SCOPE

Required: positive acceptance plus destructive negative rejection for the technical profiles actually used.

Current evidence: AV, audio/loudness, timed text, and OTIO external-first smoke paths.

### G2 — Production identity and lineage — PASS IN CURRENT V2 SCOPE

Required for each graduated production episode:

1. exact input/source identity;
2. exact production recipe/tool binding identity where mechanically relevant;
3. exact editable master identity when the medium has one;
4. exact runtime/delivery derivative identity;
5. explicit derivation relation without claiming byte equality when bytes differ;
6. fail-closed handling of stale or mismatched declared digests.

Current evidence now distinguishes the older accepted picture occurrence (`77d8...`), the reproducible current picture occurrence (`9f47...`), the exact narration occurrence (`798c...`), and the final A/V occurrence (`7d99...`). The current picture recipe reproduced `9f47...` byte-for-byte across the original R2 fresh run and the 2026-09-13 rerun; the older accepted picture remains a distinct preserved occurrence. The original R2 picture-vs-final-A/V equality comparison is explicitly corrected as a cross-stage comparison error rather than normalized away.

### G3 — Real external consumer — PASS (FIRST EPISODE)

At least one non-Media capability package must consume Media through the intended boundary. The first admitted consumer is Game / Station Zero v3 specialist sprite production. Game owns Actor/gameplay semantics; Media owns medium-specific production and technical evidence; Workstation owns exact equipment binding; Runtime owns physical execution.

### G4 — Review and acceptance — NOT YET GRADUATED

A real review episode must use a mature review surface when required and retain a digest-bound decision. Technical QC must never be promoted to semantic/aesthetic/editorial acceptance. No review platform is built merely to satisfy this gate.

### G5 — Distribution and destination verification — NOT YET GRADUATED

A naturally useful external delivery must use the provider-native effect and provider-native readback/observation boundary. Local transport success is not publication/currentness/acceptance. No static provider-policy database is sufficient evidence.

### G6 — Legacy retirement proof — NOT YET GRADUATED

Before final graduation:

- census remaining references from new Media v2 paths to legacy `ordivon_studio` media implementations;
- prove each demonstrated replacement with positive + destructive-negative evidence or an explicit retained delta;
- delete or quarantine superseded implementation paths instead of keeping two active authorities;
- retain historical evidence without retaining obsolete production authority.

## Non-gates

The following do not constitute graduation by themselves:

- installing more media applications;
- having an equipment catalog entry;
- a process exiting zero;
- a local file existing without digest/lineage evidence;
- a smoke fixture with no real consumer;
- a local `published` or `accepted` label without destination/reviewer authority.

## Current standing

`MEDIA_V2_GRADUATION = IN_PROGRESS`

G2 is closed for the currently admitted v2 production episodes and G3 has its first real external consumer. The next closure order is: real review episode -> provider-native distribution/readback episode -> G6 destructive legacy retirement audit. New future media types must earn their own format-specific lineage evidence rather than inheriting this standing automatically.
