# DG-1 Stage Notes — Document Governance Pack Hardening

Status: **current** | Date: 2026-05-02 | Phase: DG-1
Tags: `dg-1`, `stage-notes`, `truth-substrate`, `document-governance`
Authority: `source_of_truth` | AI Read Priority: 2

## Purpose

DG-1 converts Ordivon's Document Governance Pack from an existing registry/wiki/policy
system into a stable, detector-consumable truth substrate. It follows ADP-3-S, which
proved that detectors can consume DG metadata — now DG must become reliable enough
to be consumed.

## What DG-1 Is

- A formalization of the document classification, authority, freshness, supersession,
  and AI read path models that were previously scattered across multiple DG docs.
- A debt routing exercise that assigns ownership for all open ADP2R/DG debts.
- A gap analysis that documents current registry freshness coverage without fixing
  it inline (DG-2 will backfill).

## What DG-1 Is Not

- Not a registry backfill (DG-2)
- Not a new detector (ADP-4)
- Not a wiki rewrite
- Not a package release or public surface change
- Not action authorization or runtime enforcement

## Relationship to Other Phases

- ADP-3: Depends on DG metadata. DG-1 makes that metadata trustworthy.
- PV: Depends on public-surface classification. DG-1 defines the classification model.
- HAP/GOV-X: Consume phase boundaries and authority docs. DG-1 stabilizes those.
- DG-2: Will backfill freshness metadata, upgrade registry schema.

## Key Deliverables

1. Document Classification Index — 8 dimensions, 17 artifact types
2. Authority Model — 7 types, 7 invariants
3. AI Read Path Invariants — L0-L4, freshness requirements
4. Freshness/Supersession Model — by priority and authority
5. Debt Ownership Routing — 8 debts routed to owner phases
6. DOC-WIKI-FLAKY-001 disposition — currently deterministic

## Status

CLOSED. Next recommended: DG-2 (registry freshness backfill) or ADP-4 (detector precision).
