# Historical text and knowledge disposition — 2026-09-13

## Decision

Do **not** create a universal PostgreSQL mirror of Ordivon Markdown, README, logs, reports, design notes or repository documentation.

Git/source-owner repositories remain authoritative for document bytes and revision history. PostgreSQL is used only for bounded projections where queryable relational state has a demonstrated consumer. `ordivon-next/knowledge` contains curated metadata and reusable mappings, not a copy of every historical document.

## Current dispositions

| Material class | Durable/source authority | PostgreSQL treatment |
|---|---|---|
| Research programmes, current standing, source-backed findings and research/publication artifacts | owning Research repositories and exact Git revisions | `ordivon_assets.research_archive` projection |
| Creative/writing/game/media historical works | exact source-fenced Git history and Creative Archive evidence | `ordivon_assets.creative_archive` historical read model |
| Host v1 Task/Board history | retired Host v1 archive and integrity receipt | exact final snapshot projection in `ordivon_host_stage_r1.host_retired_final_20260912` |
| General project docs, READMEs, design notes, migration notes and operational logs | owning Git repository | no automatic PG mirroring |
| Stable reusable lessons, standards/method mappings and cross-project decisions | curated `ordivon-next/knowledge`, policies, capability/profile or migration records as applicable | add a PG projection only after a real query/consumer requires one |

## Admission rule

A text/document becomes a PostgreSQL record only when at least one of these is true:

1. it is needed as a relationally queryable domain object (for example a research standing/finding or Task/Board record);
2. it is required for provenance/identity of a registered asset;
3. a real repeated consumer needs indexed lookup beyond Git/search capabilities.

Otherwise retain the exact source in Git and curate only reusable metadata/mappings into Ordivon Next.

## Nonclaims

This decision does not mean unregistered text is unimportant or lost. It means registration, preservation and source authority are separate concerns. PostgreSQL registration is not the criterion for durable existence.
