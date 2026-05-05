# Ordivon Governance-Application Boundary

Status: **current** | Date: 2026-05-05 | Phase: EG-1
Tags: `architecture`, `classification`, `dogfood-boundary`
Authority: `source_of_truth` | AI Read Priority: 1

## The Two-Layer Split

Ordivon's repo is split into two layers with fundamentally different governance
relationships:

```
                           Ordivon Repo
                    ┌─────────────────────────┐
                    │                         │
           ┌────────▼────────┐    ┌───────────▼──────────┐
           │  GOVERNED LAYER  │    │   APPLICATION LAYER   │
           │  (892 objects)   │    │   (726 files)         │
           │                  │    │                       │
           │  Each file has:  │    │  No registration      │
           │  - registry entry│    │  No classification    │
           │  - classification│    │  No checker coverage  │
           │  - checker cover │    │                       │
           │                  │    │  Governed indirectly  │
           │  Baseline BLOCKED│    │  via gate-driven mode │
           │  on failure      │    │  (lint, typecheck,    │
           └──────────────────┘    │   test, security scan) │
                                   └───────────────────────┘
```

## Governed Layer (892 registry objects)

These are Ordivon Verify's **own infrastructure** — the files that make Ordivon
Verify work. They are self-governed through the dogfood loop.

| Registry | Objects | What it governs |
|----------|---------|-----------------|
| `document-registry.jsonl` | 213 docs | Markdown/JSON/JSONL docs with `doc_layer` × `doc_authority` |
| `artifact-registry.jsonl` | 643 entries | Code files (tests, scripts, domains, src) with `artifact_class` × `criticality` × `layer` |
| `checker_registry.py` | 36 checkers | Checker maturity with `hardness` × `profiles` × `maturity` |

### Governed directories

```
docs/             213 files  →  document-registry.jsonl  (L0-L5 docs)
tests/            405 files  →  artifact-registry.jsonl  (test files)
scripts/           90 files  →  artifact-registry.jsonl  (build/CI scripts)
domains/          107 files  →  artifact-registry.jsonl  (domain models)
src/ordivon_verify/ 41 files →  artifact-registry.jsonl  (source code)
checkers/          36 pkgs   →  checker_registry.py      (verification checkers)
```

### Why tests/ and scripts/ share one artifact-registry.jsonl

They share the same classification schema (`artifact_class` × `criticality` ×
`layer`). tests/ are `artifact_class=test`; scripts/ are
`artifact_class=script`. Splitting them into separate registries would introduce
a second schema, a second checker, and a second set of naming conventions — with
no governance benefit. A unified registry enables cross-class queries like "all
L3 files with criticality ≥ 4".

## Application Layer (726 files)

These are the **products Ordivon builds**, not the governance infrastructure
itself. They are governed indirectly — not by file-by-file registration, but by
**gate-driven verification**: did the lint gate pass? Did the typecheck gate
pass? Did the test gate pass?

### Ungoverned directories

| Directory | Files | Why not in artifact-registry |
|-----------|-------|------------------------------|
| `apps/` | 324 | Frontend (Next.js) + API (FastAPI). Governed by ESLint, tsc, pytest, bandit. |
| `build/` | 103 | Build artifacts — governed by CI process, not code classification. |
| `knowledge/` | 64 | AI knowledge base (Agentic Pattern Library). |
| `capabilities/` | 35 | Capability definitions — bridge layer, may be partially governed in future. |
| `data/` | 30 | DuckDB data — not source code. |
| `governance_engine/` | 26 | Python runtime governance logic (risk engine, audit, approval). Governed by tests. |
| `state/` | 26 | State management layer. |
| `intelligence/` | 25 | Intelligence analysis. |
| `orchestrator/` | 24 | Orchestrator engine. |
| `shared/` | 19 | Shared utilities. |
| `packs/` | 18 | Domain packs (Finance, Coding). |
| `infra/` | 19 | Infrastructure code. |
| `execution/` | 10 | Execution engine. |
| `adapters/` | 11 | External adapters. |
| (other) | ~40 | Tools, services, evals, policies, etc. |

### Gate-driven governance for apps/

Rather than registering each of 324 React components individually, the apps/
directory is governed by the gates that Ordivon Verify checks:

```
Not:  apps/components/Button.tsx  →  artifact-registry.jsonl
But:  apps/ lint gate             →  checker "frontend-lint-gate"
      apps/ typecheck gate        →  checker "frontend-typecheck-gate"
      apps/ test gate             →  checker "frontend-test-gate"
```

These checker gates are themselves in `checker_registry.py` — the governance
infrastructure governs its own gates, and the gates govern the apps.

## The K8s Analogy

Kubernetes' own source code is not governed by a Kubernetes cluster. Ordivon
Verify's own application code is not governed by Ordivon Verify's artifact
registry. Both are governed by standard tooling (lint, typecheck, test, CI).

What Ordivon Verify governs is the **governance infrastructure itself**: the
documents that define truth, the checkers that verify claims, the tests that
validate invariants, the domain models that encode semantics.

## Naming: governance/ → governance_engine/

The directory `governance_engine/` (formerly `governance/`) is the Python runtime
governance logic — risk engine, audit system, approval gates. It was renamed to
eliminate ambiguity with `docs/governance/`, which contains governance
documentation (registries, ledgers, policies).

| Path | Meaning |
|------|---------|
| `docs/governance/` | Documentation about governance (registries, ledgers, policies as docs) |
| `governance_engine/` | Python implementation of governance (risk engine, audit, approval) |

## When to expand the governed layer

Add files to the artifact registry when:
1. They define Ordivon's core governance semantics (domain models, invariants)
2. Their failure directly impacts baseline correctness
3. They have a clear `artifact_class` in the existing schema

Do NOT add files when:
1. They are application code governed by external tools (lint, typecheck, test)
2. They are build artifacts or data
3. They would require adding a new classification axis — that signals a new
   registry, not an expansion of the existing one
