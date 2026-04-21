# Modularity Audit 2026-04-18

## Scope

This audit reviews how the current repository structure in `financial-ai-os/` compares to the target 8-layer architecture:

1. Experience Layer
2. Capability Layer
3. Orchestration Layer
4. Governance Layer
5. Intelligence Layer
6. Execution Layer
7. Knowledge and State Layer
8. Infrastructure Layer

The goal is not to judge whether the repository is "clean" in the abstract. The goal is to measure how much of the target modular architecture is already real in code, how much is still transitional, and where the highest-risk gaps remain.

## Executive Summary

The repository is no longer a flat prototype. It has already entered a real migration phase:

- root-layer architecture folders now exist
- several core implementations have migrated to root layers
- the API now mounts a capability-driven `api/v1` path
- state DB foundations already moved into `state/db`

However, the repository is still strongly dual-track:

- `pfios/` remains the main business-truth container
- many new root-layer modules still depend on `pfios.domain.*`
- `knowledge/` and `execution/` are mostly structural shells
- some compatibility stubs still point to non-existent modules

In short:

The architecture direction is good. The structure is visible. But the repository has not yet completed the transition from "directory correctness" to "truth-source correctness".

## Status By Layer

### Experience Layer

Current location:

- `apps/api/app/`
- `apps/web/`

What is working:

- FastAPI app is alive and imports successfully
- `/api/v1` is mounted in [apps/api/app/main.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/apps/api/app/main.py:1)
- v1 routes now import and assemble cleanly

What is incomplete:

- the app still exposes both old top-level routes and new `/api/v1` routes
- experience-level contract cleanup is not done yet

Assessment:

- maturity: medium
- main risk: dual entry surface and maintenance overhead

### Capability Layer

Current location:

- `capabilities/`

Extracted modules:

- `analyze.py`
- `audits.py`
- `dashboard.py`
- `evals.py`
- `recommendations.py`
- `reports.py`
- `reviews.py`
- `validation.py`

What is working:

- product-facing entry modules now exist
- API routes mostly delegate into capability modules instead of directly stitching old internals

What is incomplete:

- many capabilities are still adapter-style wrappers over older `pfios` services
- capability contracts are not yet fully normalized
- some fields are still best-effort placeholders rather than durable product outputs

Example:

- [capabilities/analyze.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/capabilities/analyze.py:1) maps orchestrator output into response fields, but still hardcodes parts like `workflow` and leaves `report_path` / `audit_event_id` unresolved

Assessment:

- maturity: medium
- main risk: capabilities exist, but some are still thin facades rather than stable product modules

### Orchestration Layer

Current location:

- `orchestrator/context/`
- `orchestrator/runtime/`

What is working:

- context classes and builder have root-layer implementations
- runtime orchestrator has moved to [orchestrator/runtime/engine.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/orchestrator/runtime/engine.py:1)

What is incomplete:

- orchestration still directly depends on `pfios.domain.*`, `pfios.audit.*`, and `pfios.expression.*`
- workflow definitions, dispatch, contracts, scheduler, and router subareas are still mostly placeholders

Assessment:

- maturity: medium-low
- main risk: root-level orchestrator exists, but it still carries old-layer dependencies and has not yet become a clean runtime control plane

### Governance Layer

Current location:

- `governance/risk_engine/`

What is working:

- risk engine has a root implementation
- compatibility re-export from `pfios.governance.risk_engine` is in place

What is incomplete:

- `audit/`, `permissions/`, `guards/`, and `policies/` are not yet truly migrated
- governance remains much thinner than the target architecture expects

Assessment:

- maturity: low-medium
- main risk: governance exists as a layer name and risk check, but not yet as a full control plane

### Intelligence Layer

Current location:

- `intelligence/engine.py`
- `intelligence/models/`

What is working:

- root reasoning engine exists
- provider routing exists
- mock provider exists
- base provider interface exists

What is incomplete:

- `prompts/`, `tasks/`, `evaluators/`, `embeddings/`, and most of `schemas/` are still not active root-layer implementations
- some intelligence modules still depend on `pfios.domain.analysis.*`

Assessment:

- maturity: low-medium
- main risk: the layer exists, but only the thinnest slice of model orchestration has moved

### Execution Layer

Current location:

- `execution/`
- `skills/`
- `tools/`

What is working:

- `execution/` exists as an umbrella layer definition
- `skills/` and `tools/` still exist as recognized execution surfaces

What is incomplete:

- `execution/` itself contains no real implementation yet
- actual execution logic is still spread across legacy and adjacent modules
- report generation and wiki-writing responsibilities are not yet cleanly located under execution

Assessment:

- maturity: low
- main risk: execution is still an architectural intention more than an implemented layer

### Knowledge and State Layer

#### State Domain

Current location:

- `state/db/`

What is working:

- DB base/session/bootstrap/schema now live in root `state/db`
- `pfios.core.db.*` has become compatibility re-export surface
- active code paths already started switching to `state.db`

What is incomplete:

- `state/repositories/`, `state/services/`, `state/schemas/`, `state/snapshots/` remain mostly empty
- state business access is still mostly routed through `pfios.domain.*`

Assessment:

- maturity: medium for DB foundation
- maturity: low for full State Domain

#### Knowledge Domain

Current location:

- `knowledge/`

What is working:

- directory structure exists for `wiki`, `memory`, `indexes`, `ingestion`, and `retrieval`

What is incomplete:

- almost no real code has moved in
- wiki remains outside as a legacy top-level content area
- retrieval and ingestion are still architectural placeholders

Assessment:

- maturity: low
- main risk: knowledge has boundary definitions but not yet real operational ownership

### Infrastructure Layer

Current location:

- `infra/`
- root deployment files such as `docker-compose.yml`

What is working:

- structure exists for docker, monitoring, secrets, local, and cloud

What is incomplete:

- most infra directories are still placeholders
- live runtime still depends more on historical project wiring than on clear infra-layer integration

Assessment:

- maturity: low
- main risk: infrastructure layer is present structurally but not yet central to system operation

## Main Architectural Gaps

### 1. `pfios/` Still Holds Too Much Truth

The most important gap is not that root folders are missing. The most important gap is that `pfios/` still holds the majority of active business truth.

Examples:

- `orchestrator/runtime/engine.py` still depends on `pfios.domain.*`
- capability modules still consume `pfios.domain.*`
- state bootstrap still imports `pfios.domain.*.orm`

This means the migration has started, but the root layers are not yet the dominant truth system.

### 2. Some Compatibility Stubs Are Broken

Several files still re-export paths that do not exist in the repository.

Examples:

- [apps/api/app/services/object_service.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/apps/api/app/services/object_service.py:1)
- [apps/api/app/services/review_service.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/apps/api/app/services/review_service.py:1)
- [apps/api/app/services/recommendation_service.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/apps/api/app/services/recommendation_service.py:1)
- [apps/api/app/services/validation_service.py](/c:/Users/16663/Desktop/dev/projects/financial-ai-os/apps/api/app/services/validation_service.py:1)

These create false confidence because they look like migration compatibility layers while actually pointing at dead destinations.

### 3. `domains/` Has Not Yet Taken Over Business Semantics

The target architecture expects business meaning to move toward `domains/`.

Current reality:

- `domains/` exists only as structure
- `pfios/domain/*` still carries the actual business model, repository, and service code

This is one of the largest remaining differences between the repository and the intended design.

### 4. `execution/` and `knowledge/` Are Mostly Structural

These layers are named and documented, but most of their real implementation work is still ahead.

This creates a visual sense of completeness that the codebase has not yet earned.

### 5. Experience Layer Is Still Dual-Track

The application currently mounts:

- old direct routers
- new `/api/v1` routers

This is appropriate during migration, but it should be treated as temporary. Otherwise the Experience Layer will calcify into two public surfaces.

## What Has Been Successfully Improved

The repository has made real progress in a few important ways:

1. There is now a canonical architecture definition in docs.
2. The Capability Layer is real enough to route user-facing API work through it.
3. The root `shared/` layer is no longer purely theoretical.
4. The root `state/db/` foundation exists and works.
5. Root `orchestrator/`, `intelligence/`, and `governance/` implementations now exist for core slices.
6. Legacy imports are increasingly compatibility shims instead of primary implementations.
7. Import and smoke coverage has improved, reducing the risk of silent drift.

## Current Maturity Estimate

This is a practical estimate, not a mathematical score:

- architecture definition quality: high
- root-layer implementation depth: low-medium
- module boundary clarity: medium
- migration completeness: low-medium
- runtime stability for touched paths: medium
- overall modular completion versus target: still under halfway

In simpler terms:

The repository has crossed from "architecture idea" into "architecture in progress", but it has not yet crossed into "architecture is the actual system".

## Recommended Next Priorities

### Immediate

1. Remove or replace broken compatibility stubs in `apps/api/app/services/*`.
2. Continue migrating active code to root-layer imports instead of `pfios.*` when safe.
3. Keep import and smoke coverage growing with each migration slice.

### Short-Term

1. Move business truth gradually from `pfios/domain/*` toward `domains/*` and root state services.
2. Make `execution/` hold at least one real implementation path.
3. Start the first real `knowledge/` migration slice for wiki/retrieval ownership.

### Medium-Term

1. Collapse dual Experience Layer routes into one primary API surface.
2. Complete governance migration beyond the risk engine.
3. Normalize capability contracts so capabilities become stable product modules rather than response-mapping adapters.

## Final Assessment

The repository is structurally aligned with the target architecture, but only partially behaviorally aligned with it.

That distinction matters:

- structurally aligned means the folders, docs, and migration direction are mostly right
- behaviorally aligned means the actual system truth, execution paths, and ownership boundaries live where the architecture says they live

Today the repository is much closer to the first than the second.

That is still good progress. It means the project is no longer blocked on architectural confusion. It is now mainly blocked on disciplined migration execution.
