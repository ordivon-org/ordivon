# Tools — Phase 0 Mapping

This directory exists per the AI-Native Project Object Model (canonical doc #5).

**Current state:** Tool scripts live in `scripts/` at the repo root — this is the
legacy location with ~20 hardcoded path references across `temporal_worker.py`,
`verify_infrastructure.py`, `AGENTS.md`, and 15+ governance scripts.

**Mapping:**

| Target (Object Model) | Current Location | Reason Not Yet Moved |
|----------------------|------------------|---------------------|
| `tools/` | `scripts/` | 20+ hardcoded `scripts/` references in source code |
| `tools/cli/` | `src/ordivon_verify/cli.py` | CLI is part of the Python package |

**Migration plan:** When the tool registry (`tool-registry.jsonl`) is introduced,
all scripts will be cataloged with their canonical paths, and hardcoded references
will be updated to use registry lookups instead of string paths. At that point,
`scripts/` will be renamed to `tools/scripts/`.

For now, all tool scripts remain accessible via `scripts/`.
