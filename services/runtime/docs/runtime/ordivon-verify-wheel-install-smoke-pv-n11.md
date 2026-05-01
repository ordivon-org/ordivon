# PV-N11 — Wheel Install Smoke

## Purpose

Install the locally built wheel into an isolated venv and prove the
installed package works without relying on the private repo source tree.

## Why PV-N11 Exists

PV-N10 proved the separated package context produces clean wheel artifacts.
PV-N11 proves those artifacts can be installed and executed away from the
private repo — import, entrypoints, schema access, and trust ladder semantics
all preserved.

## Install Environment

- Wheel: `.tmp/ordivon-verify-package-context/dist/ordivon_verify-0.1.0-py3-none-any.whl`
- Venv: isolated, temp directory, PYTHONPATH cleared
- Install: `pip install --no-deps --force-reinstall` from local wheel
- No editable install, no repo source on path

## Results

```
📥 Import:        ✅
📥 Module entry:  ✅  (DEGRADED from temp dir — expected)
📥 Console entry: ✅  (DEGRADED from temp dir — expected)
📐 Schemas:       ✅  (5/5 at sys.prefix/schemas/)
🧪 Quickstart:    ✅  READY
🧪 Bad fixture:   ✅  BLOCKED
🔍 Source leak:   ✅  none (resolves to site-packages, not repo src/)
```

## Schema Resource Fix

PV-N10 wheel had 17 members without schemas. PV-N11 adds `[tool.setuptools.data-files]`
to the generated package pyproject.toml, making 5 schema JSON files available
at `sys.prefix/schemas/` after pip install. Wheel now has 22 members.

## Trust Ladder After Wheel Install

| Fixture | Result | Expected |
|---|---|---|
| Quickstart | READY | READY |
| Standard external repo | READY | READY |
| Clean external repo | DEGRADED | DEGRADED |
| Bad external repo | BLOCKED | BLOCKED |

All semantics preserved from the installed wheel — no repo source tree needed.

## What PV-N11 Proves

1. Ordivon Verify installs from local wheel and runs without private repo source.
2. Console entrypoint (`ordivon-verify`) works from installed package.
3. Module entrypoint (`python -m ordivon_verify`) works from installed package.
4. Schema resources are discoverable via `sys.prefix/schemas/`.
5. Trust ladder semantics (READY/DEGRADED/BLOCKED) are preserved.
6. No source-tree leakage — `ordivon_verify.__file__` resolves to site-packages.

## What PV-N11 Does NOT Prove

1. That pip install from PyPI would work (network install not performed).
2. That all expected package metadata (classifiers, description, etc.) is correct.
3. That public CI would pass.

## Remaining Release Blockers

- Public CI configuration
- Final versioning + changelog
- Public alpha approval
- PyPI metadata quality review

## Boundary Confirmation

- Local wheel install only. No publish. No upload. No license activation.
- No public repo. Phase 8 DEFERRED. All NO-GO intact.

## New AI Context Check

A fresh AI reading root docs sees:
- PV-N11 proves Ordivon Verify works from installed wheel
- Import, module, console, schemas, quickstart, bad fixture: all pass
- No source-tree leakage
- No license activated, no package published, no public repo
- COV-2 partials remain (verification_debt warning-only, wave_files whitelist)

---

*Closed: 2026-05-01*
*Phase: PV-N11*
