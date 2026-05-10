---
gate_id: path_map
display_name: Path Map Drift Detection
layer: L3C
hardness: hard
purpose: Verify generated path map matches repo reality. Detect manual drift and unclassified protected paths.
protects_against: "Stale architecture diagrams, orphan governance objects, silent file exclusion, generated views as source of truth"
profiles: ['full']
timeout: 30
tags: [governance, path-map, gos-pm1]
---

# Path Map Drift Detection

## Purpose

Verify that the generated path map (`docs/governance/generated/path-map.json`)
matches the current repo reality. Any manual edit to generated files, any new
file in a governed directory without a route, or any exclusion without required
metadata → BLOCKED.

## Protects Against

- Manual edits to generated path map views
- Files added to governed directories without governance classification
- Exclusions without owner/reason/review_date
- Generated views incorrectly claimed as source_of_truth

## Finding Codes

| Code | Severity | Meaning |
|------|----------|---------|
| PM-1 | BLOCKED | Path map drift — generated view inconsistent with repo reality |
| PM-2 | BLOCKED | Unclassified protected path — file in governed dir without route |
| PM-3 | BLOCKED | Exclusion missing owner |
| PM-4 | DEGRADED | Exclusion missing review_date |
| PM-5 | BLOCKED | Generated view authority violation — generated marked as source_of_truth |
| PM-6 | BLOCKED | Registered document unrouted — in registry but no path-map route |
| PM-7 | DEGRADED | Ambiguous route — file matches multiple routes without priority |
| PM-8 | BLOCKED | AI route not authorized — proposed classification without schema backing |

## Inputs

- `docs/governance/generated/path-map.json`
- `scripts/update-path-map.py` output
- `document-registry.jsonl`
- `path-map-rules.json`

## Output

- Exit 0: path map consistent with repo reality
- Exit 1: drift detected or blocked files exist
