# Creative Preservation External-Composition Pilot R1

Date: 2026-09-11
Standing: `EXTERNAL_PRESERVATION_COMPOSITION_PILOT_ACCEPTED_R1`

## Purpose

This pilot asks a replacement question, not an Ordivon feature-development question:

> Can mature preservation standards and external projects replace the preservation mechanics that Ordivon was beginning to implement itself?

The answer for the tested scope is **yes, with bounded exceptions**.

The pilot deliberately uses twelve heterogeneous works from the frozen 302-work archive and materializes every input from its exact historical Git revision/blob. Current worktree bytes are never substituted.

## Corpus

The 12-work / 86-file corpus covers:

- raster artwork;
- audio;
- video;
- text publication;
- historical HTML/JavaScript;
- Godot playable/source trees;
- STEP CAD;
- KiCad EDA;
- deterministic derived-preview lineage;
- cross-work relations;
- and a historical carrier absent from current HEAD.

Frozen corpus receipt: `artifacts/creative-preservation/pilot-r1/corpus-v1.json`.

## 1. Software/content identity — SWHID

Software Heritage's official `swh.model 8.4.1` implementation was used locally. No Software Heritage network/archive lookup was required.

Every representative carrier received a content SWHID. Eleven directory-root works also received directory SWHIDs; each directory SWHID was independently recomputed twice from an exact-revision materialization and remained identical.

Decision: **ADOPT**.

Long-term roles become:

```text
SWHID                  = intrinsic content/directory identity
Git repo/revision/path = local resolution context
Ordivon work_id        = creative/domain identity
```

Do not invent an Ordivon-native software persistent-identifier scheme.

Receipt: `artifacts/creative-preservation/pilot-r1/swhid-pilot-v1.json`.

## 2. Transfer/fixity packaging — BagIt

Library of Congress `bagit-python 1.9.0` created a BagIt v1.0 / RFC 8493 package over all 86 exact frozen files using SHA-256 manifests.

Observed:

- 12 works;
- 86 payload files;
- 4,200,279 payload bytes;
- `Payload-Oxum = 4200279.86`;
- fresh reopen + BagIt validation: PASS.

Decision: **ADOPT**.

Do not create a custom Ordivon transfer/fixity package schema.

Receipt: `artifacts/creative-preservation/pilot-r1/bagit-transfer-pilot-v1.json`.

## 3. Formal format identification — external, but not yet graduated

FIDO 1.6.1 successfully ran over exact frozen carriers. The strong pass disabled filename-extension matching (`-noextension`) to prevent suffix guesses from masquerading as format identification.

Observed with its PRONOM v109 signature set:

- 6 content/signature identifications;
- 5 unidentified objects;
- 1 extension-only weak match.

Examples of strong identification included PNG, WAV, MP4, HTML and STEP. Godot/KiCad/MDX gaps were left unidentified rather than filled by Ordivon heuristics.

However FIDO's bundled/updater signature set is PRONOM v109 and is stale relative to newer preservation-tool signature sets. Direct acquisition of current Siegfried was blocked by current external-network throughput/reachability.

Decision: **PROVISIONAL / NOT GRADUATED**.

The Creative Library suffix table remains presentation-routing only. It must never be cited as preservation format identity.

Receipt: `artifacts/creative-preservation/pilot-r1/format-identification-fido-v109.json`.

## 4. External AIP engine — a3m feasibility

`a3m 0.8.1` was run in its embedded-server mode under Python 3.12.13. The workstation's system Python 3.14 was intentionally not modified; a uv-managed Python 3.12 environment was used because a3m's pinned dependency set is not currently compatible with Python 3.14.

Only two missing external commands were required for the tested flow:

- `tree 2.3.2`;
- `atool 0.39.0`.

Both were downloaded from the Arch package repository and extracted workspace-locally. The system package database was not modified.

### Direct ingest result

All 12 heterogeneous source roots generated AIPs successfully.

The AIPs contained:

- BagIt structure;
- METS;
- PREMIS objects/events/agents;
- SHA-256 fixity;
- format identification;
- ingestion and message-digest events;
- preservation-generated metadata such as directory-tree records.

This demonstrates that Ordivon does not need to invent its own AIP, PREMIS-event, or preservation-agent ontology.

### Direct-ingest policy defect

Exact PREMIS-level verification found:

```text
expected frozen Git files      86
PREMIS originals exact-matched 83
missing                         3
unexpected originals            0
```

The three missing files were exactly:

- `media:one-bell-three-rooms/.gitignore`;
- `game:nine-wells/.gitignore`;
- `game:signal-garden-evidence-petals/.gitignore`.

Inspection of a3m 0.8.1's default workflow confirmed a hard-coded `remove_hidden_files_and_directories` step. Its implementation recursively removes files/directories whose names start with `.` and files ending in `~`.

The stable `--processing-config` protobuf surface has no setting that disables this step. A custom workflow programming API exists but is upstream-unstable.

Decision: direct a3m source-root ingest is **FEASIBILITY PASS WITH POLICY BLOCKER**, not a production preservation authority.

Receipts:

- `a3m-pilot-pass1.json` — engine/AIP generation observations;
- `a3m-premis-fixity-v1.json` — correct PREMIS-level original verification;
- `a3m-mets/*.xml` — per-work METS evidence.

The early strict input-vs-all-AIP-object hash-multiset comparison in `a3m-pilot-pass1.json` is explicitly labelled diagnostic only. Preservation engines legitimately add metadata objects, so strict total-object-set equality is not an original-preservation criterion.

## 5. Standards composition closes the hidden-file gap

No a3m source patch or Ordivon restoration shim was introduced.

Instead, the corpus was composed through mature packaging:

```text
exact frozen Git roots
        ↓
BagIt RFC 8493 / SHA-256
        ↓
ZIP transfer container
        ↓
a3m 0.8.1 embedded ingest
        ↓
BagIt AIP + METS + PREMIS
```

The reason this works is structural: a3m's hidden-file cleanup runs before archive/package extraction. Hidden source files inside the transfer package therefore survive extraction and are subsequently represented as originals.

A single-work probe first proved `.gitignore` preservation by exact SHA-256 and size.

The full 12-work run then observed:

```text
frozen source files                  86
PREMIS original subset matches       86
missing frozen files                  0
hidden source files matched           3
AIP BagIt validation               PASS
```

Combined transfer ZIP:

`sha256:62c78514c1fed50b7075a05069aaec5380bba19964026b1ce57e28328cc48b4c`

Generated combined AIP:

`sha256:6b9a7b249426d18296e90f185cd61c282ee5f649166c76bce9e7b5f130838f67`

Combined METS:

`sha256:011cc1cc352f89de3684c37d89842354be23f57597032ac45f86e70938232195`

The generated AIP contains 91 `fileGrp USE="original"` entries because it also retains the submitted ZIP and extracted BagIt tag files. The claim is therefore **not** that the AIP contains only 86 originals; the claim is that all 86 frozen source files are mechanically verified as a PREMIS-original subset.

Decision: BagIt → ZIP → a3m composition is **PILOT ACCEPTED, NOT PRODUCTION AUTHORITY**.

Receipts:

- `a3m-bagit-zip-hidden-v1.json`;
- `a3m-bagit-zip-12work-v1.json`;
- `a3m-bagit-zip-12work-METS.xml`;
- `a3m-bagit-zip-12work-METS-summary.json`.

## 6. What is now safe to stop building

The pilot provides enough evidence to freeze growth of the following Ordivon-native mechanisms:

1. custom software/content persistent identifiers — use SWHID;
2. custom transfer/fixity package format — use BagIt;
3. custom AIP package ontology — external engines already produce BagIt AIPs;
4. custom preservation Object/Event/Agent ontology — use PREMIS/METS;
5. universal Ordivon `replayable=true/false` model — dispatch to format-specific mature systems instead;
6. extension-based preservation format identity — use current PRONOM tooling when admitted.

Existing Creative Archive structures remain migration/read-model evidence until the production external stack graduates. They are not deleted merely because a 12-work pilot succeeded.

## 7. Why a3m does not become production authority

a3m remains useful and technically promising, but this pilot does not promote it to production authority because:

- upstream describes 0.8.1 as proof of concept;
- its default workflow has a preservation-significant hidden-file policy;
- the stable ProcessingConfig surface cannot disable that policy;
- changing the workflow requires the unstable custom-workflow programming surface;
- long-term repository operations, off-machine durability, upgrade behavior and E-ARK conformance were not tested here.

Use a3m as an AIP-engine feasibility reference and lightweight comparison target.

## 8. Production path remains external

Preferred next production pilot:

```text
Ordivon Runtime
      ↓ cross-domain dispatch
Enduro
      ↓ preservation-domain durable workflow
Archivematica 1.18
      ↓
AIP / PREMIS / METS / repository storage
```

RODA Community remains the all-in-one comparison alternative and should be evaluated as a replacement candidate, not stacked on top by default.

The same 12-work frozen corpus and acceptance conditions should be reused unchanged. Do not create a new Ordivon benchmark for the next engine.

## 9. Graduation conditions for 302-work migration

Before replacing current archive authority for all 302 works, a production external stack must show:

- 86/86 frozen Pilot source files preserved under the same source-fenced corpus;
- current PRONOM-based identification rather than stale v109 signatures;
- configurable preservation policy without unstable code patches;
- standards-based AIP / METS / PREMIS output;
- explicit original vs derivative relationships;
- repository/storage durability and restore evidence;
- no silent promotion of digital evidence to physical/Human standing;
- materially less custom Ordivon preservation code/ontology than the system it replaces.

Only after that comparison should bulk 302-work migration begin.

## Machine-readable verdict

`artifacts/creative-preservation/pilot-r1/acceptance-r1.json`

Standing:

`EXTERNAL_PRESERVATION_COMPOSITION_PILOT_ACCEPTED_R1`
