# Agent-native graphics R1 — consumer-rooted composition, not a new Engine

Status: **native catalog/visual truth contract verified; optional Vega spec and
renderer exercised; React Flow/WebGPU/3D production substitution NOT admitted**.
SourceCut: Ordivon monorepo `2e8a32c686213ea1f40ac7f838a00a8b0c9e3b39`.
Created: 2026-11-14. The historical source snapshot is authoritative only for
its creation-time Archive Archipelago Production, not a live inventory.

## Real consumers and authority edges

```text
Workstation original catalog (historical revision dd7e60d6…)
    -> Media Production's frozen catalog copy (source/...json)
    -> production-local archive_source.py [validated identities/relations]
       |-> generate.py -> existing SVG/GeoJSON + interactive/data.js
       |   -> build_interactive.py -> standalone HTML, current approved Output
       |-> generate_owner_summary_vegalite.py
           -> editable Vega-Lite v6 spec (optional, not Production Output)
           -> external pinned Vega-Lite/Vega -> SVG -> librsvg -> PNG (evaluation)

Studio Production / Claim / Output -> original approved bytes and standing
Runtime -> physical execution receipts, not scientific/creative acceptance
Artifact -> selected output profiles and independent byte readback
Research/Host/Web -> their own source facts and ordinary projections
```

The relevant semantic facts are Work IDs, owners and the explicitly catalogued
`DERIVATIVE_OF` / `CONSUMER_OF` relations. Geometric positions are *composition*,
not geography, dependency, chronological facts or semantic distance.

## Source-to-visual contract (candidate, NOT a formally ADMITTED LEGO)

- **I:** selected exact frozen catalog bytes + explicit Production intent.
- **O:** existing source-bound SVG/interactive representations and optional Vega-Lite chart spec.
- **S:** no persistent task state; validated catalog read per invocation; selected Production holds standing.
- **pre:** well-formed works with unique Work IDs; supported relation labels with both endpoints existing.
- **post:** all displayed work/owner/relationship counts derive from the selected catalog; source failures fail closed.
- **inv:** generation cannot add factual edges or silently relabel unsupported edges; source owner remains truth authority.
- **eff:** read selected source; write only chosen derived local outputs; no publication or mutation of source owner.
- **c:** UNKNOWN for general complexity and browser performance; reference snapshot generator test <1 s in current local trial, not a capacity guarantee.
- **epsilon:** UNKNOWN for human readability, subjective composition and cross-renderer appearance; SVG byte identity is exact only in the scoped frozen case.
- **prov:** frozen `catalogDigest` is a declaration; chart also retains the actual input file's SHA-256; tests and external renderer receipt are independently scoped evidence.
- **unfold:** `productions/archive-archipelago-001/archive_source.py`, `generate.py`, `generate_owner_summary_vegalite.py`, native unit tests and selected existing rendering tools.

These are architectural commitments and executed checks. The separate
`formal/ArchiveVisualSourcePreservation.lean` has a Lean-kernel-checked
abstract relation conservation/rejection model; Python parsing/refinement,
installed provider readiness and output approval are **not proved**. In particular do not replace native rendering/byte-equivalence tests
with a pure theorem about counting: it would miss the actual SVG, text and provider.

## Mature capability comparison and consumer decision

| Candidate | Incumbent | Consumer observation | Decision |
| --- | --- | --- | --- |
| Vega-Lite declarative counts | Existing Python cartographic artwork | Alternative exact-snapshot count chart rendered to real SVG/PNG; preserves owner/total facts but does not provide artwork's routes/map | **COMPOSE** as optional authoring source, do not replace map |
| React Flow typed graph edits | Existing standalone accessible HTML | Pure operation smoke test only; current 303-work HTML already has filter/search/keyboard/mobile checks | **HOLD** production replacement pending real browser/accessibility comparison |
| Three.js/TSL | Existing Blender GLB workflow | Mesh construction smoke test only; no browser GPU, scene round-trip, or performance result | **HOLD** replacement |
| Penrose, Motion Canvas, Vello, wgpu | Existing production authoring and rendering | Exact upstream source downloaded, no executable domain test yet | **REFERENCE_ONLY** until a new consumer warrants admission |

Selection rule: DELETE redundant custom work only after a full real consumer
refinement; otherwise reuse native/standard output and keep upstream in an
independent evaluation. No new engine, scheduler, registry, cross-owner truth
store, or mandatory generic Visual IR.

## Next obligations (business-ranked)

- **Q1/P0:** render/playwright inspect the actual optional chart and compare
  source counts and contrast against the real archived map; typed node-action
  behavior and source identity should have explicit negative controls.
- **Q1/P0:** test any promotion to a new Studio Output through actual Production
  and Artifact readback, not Runtime exit or simple SVG emission.
- **Q2/P1:** comparative browser testing of React Flow with the archived
  keyboard/search/mobile interaction contract; reject if accessibility regresses.
- **Q2/P1:** test Penrose constraint-layout or Three.js/TSL only after naming a
  failing map/interactive/3D consumer case and measurable cost/visual benefit.
- **Q2/P1:** the narrow Lean source-relation model is implemented and wired to
  the current formal gate. Full Python-to-Lean implementation refinement and
  visually meaningful properties remain UNKNOWN; retain native render/byte tests.
- **Q3/Q4:** postpone decorative component rewrites, universal visual DSL and
  performance micro-optimizations lacking a consumer bottleneck.

## Native quality gates

`python3 -m unittest tests.test_archive_graphics_source_truth tests.test_archive_vegalite_spec -v`;
select existing Media `models`, `production_context`, `creative_library` and
Studio checks when changed. Keep current approved Output digests unchanged.
