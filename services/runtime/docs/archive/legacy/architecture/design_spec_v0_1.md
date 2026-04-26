# Design Spec v0.1

## Purpose

Version `v0.1` established the original end-to-end skeleton for PFIOS. That version proved the basic chain could run, but it did not yet fully separate architecture by ownership.

## Original Core Loop

`Observe -> Analyze -> Govern -> Express -> Persist -> Review -> Learn`

## What v0.1 Got Right

- Governance was already treated as distinct from reasoning.
- Reporting was recognized as separate from persistence.
- The system aimed to preserve auditability and long-term learning.

## What Needed Tightening

- Repo layout still centered too much on package internals.
- `wiki`, `policies`, `prompts`, and `workflows` sat beside the app without a fully unified boundary model.
- The split between knowledge and system state needed to become explicit at the root.
- Future risk existed around scripts, prompt sprawl, and route-layer business logic.

## Superseding Direction

The repository now adopts the eight-layer root structure defined in [ADR-001](../decisions/ADR-001-repo-structure.md). This keeps `v0.1` as historical context while making the current direction explicit.
