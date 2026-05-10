# Wiki Index Governance — DGP-8

Status: **CURRENT** | Date: 2026-05-09 | Phase: DGP-8
Authority: current_status | Owner: Governance

## Purpose

Define how Ordivon's knowledge navigation layer works. The navigation layer is a map, not the territory. It helps humans and AIs find current truth, active phases, archive warnings, and generated view boundaries without reading every file.

## Navigation Surfaces

1. **Current system map** (`docs/ai/current-system-map.md`) — Human-readable state overview.
2. **Knowledge map** (`docs/governance/knowledge-map.json`) — Machine-readable graph of all governed nodes.
3. **Reading graph** (`docs/ai/reading-graph.json`) — Ordered AI reading entry points.
4. **Registry index** (`ordivon-verify registry-index`) — Generated view of all RegistryObjects.
5. **Current truth entry map** (`docs/governance/current-truth-entry-map.jsonl`) — Authoritative truth register.

## Hard Rules

- Navigation is NOT source_of_truth by default. The current-truth-entry-map is the single truth register.
- Wiki index cannot override current truth map.
- Generated navigation (registry-index) is a generated_view — must not become truth.
- Archive nodes must carry archive warning in navigation.
- Generated view nodes must carry generated_view warning.
- Navigation must include non-authorization boundary.
- No external API, vector DB, or semantic search tool in this phase.
