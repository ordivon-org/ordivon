# Ordivon Phase 1 R6 — Agent-native source-carrier classification

Scope: exact source form and semantic naming hygiene ONLY; no LEGO, dynamic consumer proofs, installed service attestation or physical path moves.

Exact source cut: `72bca509f709f7fd48c924157d0c2e15e861a4c0`. Source tree `613478062b3a7cf13891553bc656edf77cfd8f04`. Source path set hash `sha256:8bb5e2eda8dd2fe2ad5d7b56eade631ee2d6ef8f90222bbcd201c8ad95ff217b`.

## Source coverage on this exact Git tree

- Git paths: 5009 / 5009 in 30 mutually selected navigation zones.
- After explicit carrier refinement, older TEXT_OTHER_UNKNOWN_FUNCTION count 207 is now 0 on this cut; newly unseen forms still remain UNKNOWN.
- Finite nonmedia syntax read bound is 4 MiB, current SKIPPED_SIZE_BOUND 0.
- Binary/media source containers 45; known GeoPackage/glTF magic signatures are byte observations only.
- JSONL first-record-only parsing files 6.
- Filename/suffix-only source form carriers 192.
- Consumer / semantic identity / installed build / formal refinement remain UNKNOWN. None of these counts is a LEGO proof.

## Source-specific Agent naming examples

| Exact original source pathname | Candidate physical content form | Git blob short ID | Verification boundary |
|---|---|---|---|
| `docs/migration/receipts/artifact.commit-map` | `HISTORICAL_COMMIT_MAPPING_TEXT` | `1e85705be0bb` | `LEXICAL_SOURCE_FORM_ONLY` |
| `packages/composition/formal/EffectReplayFence.tla` | `TLA_PLUS_SPECIFICATION_TEXT` | `011ba1d59d3b` | `LEXICAL_SOURCE_FORM_ONLY` |
| `meta/next/evidence/data-lifecycle/data-products-r2/federated-catalog.dcat.jsonld` | `JSON_LD_OBJECT` | `5007dd18c220` | `SYNTAX_PARSED` |
| `capabilities/media/productions/archive-archipelago-001/render/works.geojson` | `GEOJSON_OBJECT` | `6f183069fac2` | `SYNTAX_PARSED` |
| `capabilities/media/productions/runtime-introduction/timeline/assembly.v0.otio` | `OPENTIMELINEIO_OBJECT` | `7e1b01ad5c5a` | `SYNTAX_PARSED` |
| `capabilities/media/productions/archive-archipelago-001/render/archive-archipelago-001.gpkg` | `BINARY_OR_MEDIA_FILE` | `ba731f85c153` | `SKIPPED_BINARY` |
| `capabilities/media/productions/convergence-object-001/render/convergence-object-001.glb` | `BINARY_OR_MEDIA_FILE` | `df04e9df0faa` | `SKIPPED_BINARY` |
| `capabilities/media/productions/convergence-object-001/source/convergence-object-001.blend` | `BINARY_OR_MEDIA_FILE` | `d0ba683032f8` | `SKIPPED_BINARY` |
| `services/runtime/platform/windows/Ordivon.WindowsJobLauncher.cs` | `SOURCE_CS` | `bf1aa4cd00e3` | `LEXICAL_ONLY` |
| `capabilities/media/productions/ordivon-book-v0/book.mdx` | `MDX_DOCUMENT_UNEXECUTED` | `9c7837c6a2e8` | `HEADING_EXTRACTED` |
| `platform/workstation/n8n/ordivon-n8n.container` | `PODMAN_QUADLET_UNIT_TEXT` | `c6e0922f3f92` | `LEXICAL_SOURCE_FORM_ONLY` |
| `capabilities/media/productions/archive-archipelago-001/interactive/archive-archipelago-001.html` | `HTML_MARKUP_UNEXECUTED` | `869a231ab418` | `TEXT_OBSERVED` |

These are *physical form* names. No Git source rename, CLI/API/MCP/Skill path change, new owner or production effect is performed.

## Lexical traps that Agents must not promote to implementation/authority

- .tla / .dfy / .als / .qnt: formal MODEL SOURCE, not a discharged proof about running software.
- .commit-map: historical Git migration receipt carrier, not current branch or live producer.
- .container / .pod: deployment declaration, not an active service or actual installed binary.
- .gpkg: geospatial SQLite container; not an Ordivon database backend migration.
- .glb / .blend: rendered/3D source, not executable Game logic.
- .jsonld / .geojson / .otio: parsed structured source, no schema or consumer correctness proof.
- .mdx / .html: unexecuted document/markup, not installed web product.
- .gitignore / CODEOWNERS: Git metadata and review routing; cannot be permanent LEGO identity/approval.

## Existing CLI interfaces to REUSE (no second source registry)

```bash
cut=$(git rev-parse HEAD)
python3 tools/repo/source_content_facets.py --source-cut "$cut" --summary
python3 tools/repo/exhaustive_coverage.py --source-cut "$cut" --static-python-consumers --summary
```

Exact static Python consumer hints are neither imports exercised at runtime nor verified consumers; binary and other-language links require separate real observations. The existing #983 Agent name resolver handles path/name ambiguity.

## Still-open Phase 1 facets

1. Actual function and lifecycle of each carrier; syntax form alone is insufficient.
2. Independent Research/Paper/Media/OSS source trees and historical Git cuts: separate source universes.
3. Exact source->binary->running process provenance on Linux and Windows: evidence boundaries held separately.
4. Seven physical prefixes retain two proposed display names; neither can silently override another.
5. Newly observed unknown extension or malformed source remains explicitly UNKNOWN, never guess-qualifies a LEGO.
