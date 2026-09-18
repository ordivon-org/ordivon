# Host News Excision R1

Date: 2026-09-19

## Decision

External-news publication is not work-continuity authority and has been removed from the Host runtime surface.

Removed:

- news.list
- news.read
- news.publish
- NewsStore
- News Pydantic/contracts
- Host status and Doctor dependence on News publication state

Preserved:

- existing news_publications PostgreSQL table and rows;
- historical Alembic migration 0003_product_surfaces.py;
- historical documentation describing the old surface.

The preserved table is archival/migration data only. The running Host no longer reads, writes, validates, or reports it.

## Boundary

This change intentionally separates:

- Host: Task continuity + collaboration navigation
- News: external information product/application responsibility

No Task, Board, attention, or checkpoint state is migrated by this excision.

## Deletion proof

Acceptance requires:

1. package imports succeed without News modules;
2. MCP surface exposes exactly 10 work-control tools;
3. Host status succeeds without touching news_publications;
4. integrity/history Doctor remains healthy on Task/Board state;
5. complete test suite passes;
6. executable source has no News dependency outside historical migrations/scripts.
