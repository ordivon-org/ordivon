# Creative Preservation External Composition R1

Status: RESEARCH/COMPOSITION DECISION — external mature practice first
Date: 2026-09-11

## Decision

Ordivon Creative Archive/Library will not grow into a home-grown digital-preservation framework.

Ordivon keeps only the residual semantics that mature preservation systems do not own well for this environment:

- `work_id`, owner/room/series and cross-domain work relations;
- Ordivon evidence standings that separate digital, physical, Human, publication and derived-projection claims;
- policy dispatch: which mature preservation/access/reproducibility system should handle a work;
- Runtime/Board orchestration and evidence comparison across those systems.

Preservation format identity, preservation events, package layout, Web capture/replay, software identity, emulation and long-term repository mechanics should be delegated to mature external standards/projects.

## Target composition

```text
Ordivon thin semantics / policy / standing
                |
                v
        Enduro ingest workflow
       (durable Temporal workflows)
                |
        +-------+-------+
        |               |
 Archivematica 1.18     a3m
 mature engine          experimental lightweight successor candidate
        |
 E-ARK SIP/AIP/DIP + PREMIS/METS + BagIt
        |
 preservation storage / AIP

specialized lanes:
  file identity      -> Siegfried + PRONOM
  validation         -> JHOVE / veraPDF / MediaInfo / MediaConch as appropriate
  source identity    -> SWHID + Software Heritage
  web                -> Browsertrix -> WACZ/WARC -> ReplayWeb.page
  media access       -> IIIF Presentation/Image APIs
  reproducible env   -> Nix/OCI; ReproZip where command-trace capture is useful
  build provenance   -> in-toto / SLSA; SPDX for software inventory
  legacy execution   -> EaaSI / emulation
  research objects   -> RO-Crate 1.3 as interchange/context metadata, not AIP replacement
```

## Primary preservation waist

### Preferred first pilot: Enduro + Archivematica

Reason:

- Archivematica is the mature preservation engine and already implements PRONOM-based format policies, identification, characterization, validation, normalization, METS/PREMIS and BagIt-based AIPs.
- Enduro was created to replace brittle Archivematica automation scripts and now provides durable/fault-tolerant preservation ingest workflows. It uses Temporal and can target Archivematica or a3m.
- This lets Ordivon call a preservation-domain engine instead of implementing another preservation workflow engine.

Do **not** let Enduro become a second global Ordivon Runtime. Its authority is bounded to preservation ingest/workflow. Ordivon Runtime remains the cross-domain orchestrator above it.

### a3m

Interesting future target because it is a lightweight, gRPC-oriented AIP creation engine designed to be embedded. However the upstream project explicitly labels itself a proof of concept. It must not replace the mature engine until an external-comparison pilot demonstrates sufficient coverage and operational maturity.

### RODA Community

RODA is a strong all-in-one alternative: OAIS repository with E-ARK, PREMIS, METS, risk/representation information and preservation functions. It should be evaluated as a *replacement alternative* to the Enduro+Archivematica repository path, not stacked on top by default. Running RODA + Archivematica + Fedora together would recreate integration scaffolding without evidence of need.

### Fedora 7 + OCFL

Fedora 7 is a modern repository option; Fedora has an OCFL storage layer and is appropriate when a flexible linked-data repository/API is the central need. It is not by itself a preservation-planning engine. Consider it only if the long-term repository/access API requires more than preservation AIP storage.

## Advanced project radar

| Project | What it should replace / provide | Local role | Standing |
|---|---|---|---|
| Enduro | custom ingest orchestration | preservation workflow waist | PRIMARY PILOT |
| Archivematica 1.18 | custom preservation pipeline, format policies, normalization/event metadata | mature preservation engine | PRIMARY PILOT |
| a3m | heavy preservation engine for AIP creation | future lightweight engine | EXPERIMENTAL |
| RODA Community | most archive/repository backend logic | alternative integrated repository | COMPARE, DON'T STACK |
| Software Heritage + SWHID 1.2 / ISO/IEC 18670:2025 | local-path-dependent software identity | software/source archival identity | ADOPT |
| Siegfried 1.11.6 + PRONOM v124 | extension-based format identification | file identification | ADOPT |
| JHOVE / veraPDF / MediaConch / MediaInfo | custom validity/characterization tests | format-specific validation | ADOPT BY FORMAT |
| Browsertrix | custom Web capture/QA | Web capture + QA | ADOPT FOR WEB |
| WACZ/WARC + ReplayWeb.page 2.5.x | custom historical HTML replay | Web preservation/access | ADOPT FOR WEB |
| IIIF Presentation 3 / Image 3 | custom media presentation protocol | interoperable media access | ADOPT WHERE USEFUL |
| EaaSI | custom VM/emulator preservation system | legacy GUI/game/software execution | ADOPT WHEN NEEDED |
| Nix / OCI | custom environment descriptors | reproducible executable environments | ADOPT |
| ReproZip | bespoke syscall/dependency capture | bounded Linux experiment capture | OPTIONAL |
| in-toto / SLSA 1.2 | custom build-provenance ontology | software/build provenance | ALREADY PARTLY ADOPTED |
| SPDX 3.0 / ISO 5962 | custom dependency/SBOM inventory | software inventory | ADOPT |
| RO-Crate 1.3 | bespoke research-object/context interchange | descriptive/interchange layer | ADOPT SELECTIVELY |
| OCFL 1.1.1 | bespoke transparent storage layout/versioning | optional storage layer | CONDITIONAL |
| InvenioRDM 14 | bespoke research deposit/discovery UI | research-data publication/discovery | OPTIONAL, NOT PRESERVATION ENGINE |
| CloudViPER | manually assembling preservation tool test VMs | external-tool evaluation sandbox | USEFUL LAB, NOT CORE |

## Immediate replacements / deletions

1. The Creative Library extension table is now explicitly **presentation routing only**. It is not preservation format identification. Formal format identity moves to Siegfried/PRONOM.
2. Do not create an Ordivon `replayable=true/false` preservation ontology. Dispatch by object class to Web replay, media validation, reproducible environment, or emulation systems.
3. Do not extend custom preservation event/agent/object receipts. Migrate preservation events and derivative relationships toward PREMIS; use in-toto/SLSA for software build provenance.
4. Do not build a custom SIP/AIP/DIP package model. Evaluate E-ARK packages produced by Archivematica/Enduro and compare against the current 302-work archive.
5. Do not turn `/raw` and `/derived` into a new media standard. Keep them as a local UI compatibility layer while piloting IIIF / WACZ / preservation DIPs.
6. Do not implement a custom SWHID algorithm. Use a maintained SWHID implementation/Software Heritage tooling and store the resulting intrinsic identifiers alongside local Git resolution hints.

## Do not replace yet

The following current capabilities are retained until the external path proves equivalent or better:

- PostgreSQL `creative_archive` as the current search/read model and migration source;
- 302 source-fenced work identities and 45 Ordivon cross-domain relations;
- original-vs-derived boundary and Human/physical standing separation;
- exact Git revision resolver used by the current local Library;
- current thin Creative Library UI.

These are comparison oracles, not permanent preservation-authority claims.

## Pilot corpus

Use a deliberately heterogeneous 12-work sample before bulk migration:

- static raster/vector artwork;
- audio;
- video;
- PDF/text publication;
- historical HTML/JS interactive work;
- Godot playable;
- CAD STEP work;
- KiCad EDA work;
- source-code-heavy work;
- a work with a deterministic derived preview;
- a work with a cross-work relation;
- a historical carrier absent from current HEAD.

## Pilot success criteria

The external stack must mechanically demonstrate all of the following before replacing current archive authority:

1. Original bytes remain fixity-verifiable and independently extractable.
2. Format identification records PRONOM PUID/signature evidence rather than relying on filename extension.
3. A standardized package is produced (prefer E-ARK-compatible AIP where supported).
4. Preservation actions emit PREMIS/METS-compatible events/objects/agents and retain derivative relationships.
5. Web works can be captured/replayed through WACZ/WARC tooling without giving the archived page ambient authority over the Library.
6. Software/source objects gain SWHID identifiers without losing local Git revision/path context.
7. Access copies remain distinguishable from originals and do not strengthen Ordivon physical/Human standing.
8. Failure is explicit; unsupported CAD/EDA/Game formats remain unsupported rather than being silently guessed.
9. The current 302-work catalogue can be rebuilt as a read/search projection from external preservation identities plus the thin Ordivon semantic layer.
10. External composition removes more custom preservation code/ontology than it adds in adapters and operations.

## Current local admission status

The workstation currently has Java 17, Go 1.26.5, Podman 6.1.1 and `uv/uvx`, but no Siegfried, DROID, JHOVE, veraPDF, SWHID CLI, RO-Crate, WACZ/warcio, Archivematica or RODA installation. A workspace-local `go install` attempt for Siegfried v1.11.6 timed out after 60 seconds and a direct GitHub request also timed out. No system package or preservation service was installed as a result.

Therefore the first external-tool replacement is **semantically admitted but physically blocked by current workstation external-network reachability**. Do not substitute a new home-grown identifier during that outage. Retry external acquisition through the Workstation network/equipment mechanisms when external access is healthy.

## Authority boundary after R1

`creative_archive` remains the current recovery/read-model authority only until the external preservation pilot graduates. `kind` in Creative Library is a UI presentation hint. It must never be cited as PRONOM identification, validation, or preservation evidence.

## Pilot R1 outcome — 2026-09-11

The heterogeneous 12-work / 86-file pilot has now mechanically validated several parts of this composition rather than merely admitting them by research:

- Software Heritage `swh.model 8.4.1` produced local intrinsic SWHIDs for all representative carriers and directory SWHIDs for all 11 directory-root works: **SWHID ADOPT**.
- Library of Congress `bagit-python 1.9.0` produced and revalidated an RFC 8493 SHA-256 transfer bag over all 86 exact frozen files: **BagIt ADOPT**.
- FIDO 1.6.1 ran successfully with `-noextension`, but its PRONOM v109 signature set is stale; formal format identity remains **PROVISIONAL / NOT GRADUATED** until a current signature set is admitted.
- a3m 0.8.1 generated AIPs for all 12 heterogeneous source roots, proving external BagIt/METS/PREMIS machinery can replace an Ordivon-native AIP/event ontology. Direct ingest also exposed a real policy defect: its default workflow removes hidden files, and the stable ProcessingConfig has no toggle for that step.
- The hidden-file loss was closed without patching a3m: `exact Git roots → BagIt → ZIP → a3m` preserved all **86/86** frozen source files as a mechanically verified PREMIS-original subset, including all three `.gitignore` files, with AIP BagIt validation PASS.

This is enough evidence to freeze growth of custom Ordivon software-ID, transfer-package, AIP and preservation-event machinery. It is **not** enough to migrate all 302 works or promote a3m to production preservation authority. The production comparison remains Enduro + Archivematica 1.18 versus RODA Community, using the exact same frozen pilot corpus and acceptance conditions.

Machine-readable verdict: `artifacts/creative-preservation/pilot-r1/acceptance-r1.json`.
