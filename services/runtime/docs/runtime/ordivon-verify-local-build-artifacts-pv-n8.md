# PV-N8 — Local Build Artifact Smoke

## Purpose

Build Ordivon Verify wheel/sdist locally and inspect artifact contents
for private core leakage. Does not upload, publish, or activate anything.

## Build Result

- Wheel: ✅ built (290 members)
- Sdist: ✅ built
- ordivon_verify present: ✅ yes

## Artifact Inspection

**BLOCKED: 244 private core paths in wheel.**

The current `pyproject.toml` is configured for the full private Ordivon
repo (`where = [".", "src"]`, includes `pfios*`, `apps*`, `domains*`, etc.).
The wheel artifact contains the entire private codebase:

```
apps/          40 files   ← FastAPI app, private
domains/       89 files   ← Domain models, private
capabilities/  29 files   ← PFIOS capability layer
orchestrator/  16 files   ← PFIOS workflow engine
shared/        18 files   ← Shared config/utilities
state/         16 files   ← Database models
intelligence/  16 files   ← PFIOS reasoning bridge
infra/         11 files   ← Infrastructure
execution/      8 files   ← Execution adapters
governance/     1 file    ← Core governance (whitelisted)
```

orxivon_verify package is present (11 files), but surrounded by 244
private core files.

## Verdict

**BLOCKED for public package publishing.** Ordivon Verify needs its own
package configuration (`pyproject.toml` with `where = ["src"]`, include
only `ordivon_verify*`) before a clean public wheel can be built.

The local build smoke itself succeeds — build + inspection works. The
blocker is `pyproject.toml` packaging scope, not the build tooling.

## What PV-N8 Proves

1. Wheel/sdist can be built locally.
2. Artifact inspection can detect private core leakage.
3. The pyproject.toml scope is the root cause of the leakage.
4. Fixing the package config is the required next step.

## What PV-N8 Does NOT Prove

- No clean public wheel exists.
- No package published.
- No upload occurred.
- No license activated.

## Boundary Confirmation

- Local build only. No upload. No publish.
- Phase 8 DEFERRED. Coverage plane active.

## Next Recommended Phase

PV-N9 — Package Config Hardening: reconfigure pyproject.toml to build
a clean ordivon_verify-only wheel, or create a separate pyproject.toml
for the public wedge package.

---

*Closed: 2026-05-01*
*Phase: PV-N8*
*Task type: packaging smoke / artifact audit*
*Risk level: R1*
