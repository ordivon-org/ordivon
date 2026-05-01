# PV-N9 — Public Wedge Packaging Separation

## Purpose

Separate Ordivon Verify public-wedge package context from the private
Ordivon root packaging context, resolving the PV-N8 build artifact blocker.

## Why PV-N8 Was Blocked

PV-N8 build artifact smoke found 244 private core paths in the Ordivon wheel.
Root cause: `pyproject.toml` at the private root packages the entire repo.
Any `uv build` from root includes adapters/, domains/, orchestrator/,
apps/, policies/, and all internal governance docs.

## Packaging Separation Model

PV-N9 creates a LOCAL-ONLY package context under `.tmp/ordivon-verify-package-context/`
using a declarative file manifest:

1. `docs/product/ordivon-verify-package-file-manifest.json` declares what
   goes into the public wedge package (31 entries: 12 include, 19 exclude)
2. `scripts/prepare_ordivon_verify_package_context.py` reads the manifest
   and generates a clean output directory
3. Generated context includes: package source, schemas, examples, tests,
   public docs, generated pyproject.toml, README.md, LICENSE-PROPOSAL.md

## Package Context Shape

```
.tmp/ordivon-verify-package-context/
  README.md                          (generated — prototype README)
  pyproject.toml                     (generated — minimal deps)
  LICENSE-PROPOSAL.md                (generated — NOT ACTIVATED)
  ordivon_verify.py                  (CLI wrapper)
  src/ordivon_verify/                (package source)
  schemas/                           (prototype schemas)
  examples/quickstart/               (quickstart fixture)
  tests/unit/                        (schema + quickstart tests)
  tests/fixtures/                    (external repo fixtures)
  docs/quickstart.md                 (public quickstart)
  docs/release-readiness.md          (informational)
  docs/agent-output-contract.md      (methodology)
  skills/SKILL.md                    (Hermes Agent skill)
```

## File Manifest Summary

- 12 included (package_code, schema, example, test, public_doc)
- 19 excluded (private_core, legacy_runtime, internal_receipt, finance_broker)

## Script Result

```
  Files copied:             60
  Files generated:          3 (README, pyproject, LICENSE-PROPOSAL)
  Files excluded:           19
  Missing required:         0
  Blocking findings:        0
```

## PV-N8 Blocker Status

PV-N8 build artifact blocker REMAINS. PV-N9 created the packaging
separation but did NOT perform a build of the separated context.
The wheel/sdist from root pyproject.toml still includes 244 private
paths. A complete resolution requires:

1. Build from the separated package context
2. Verify artifact contents exclude all private paths
3. Integration test with quickstart fixtures

PV-N9 resolves the first precondition (declarative package manifest
and context generation). The build step is deferred to a follow-up phase.

## What PV-N9 Proves

1. Ordivon Verify can be described as a standalone package with explicit boundaries.
2. The set of files that constitute the public wedge is declarative, not ad-hoc.
3. A generated package context can be produced without private paths.
4. No license was activated. No package was published. No public repo was created.

## What PV-N9 Does NOT Prove

1. That a wheel built from this context would be clean (build not performed)
2. That the package would install and function end-to-end from PyPI
3. That the generated README and docs are sufficient for public adoption

## Remaining Release Blockers

- PV-N8: Build artifact from separated context
- Install smoke from wheel/sdist
- Public CI configuration
- Final secret/private-reference audit on generated context
- Versioning + changelog
- Public alpha approval

## Boundary Confirmation

- Local only. No publish. No license. No public repo.
- Phase 8 DEFERRED.
- All NO-GO boundaries intact.
- COV-2 partial gaps remain explicit.

## New AI Context Check

A fresh AI reading root docs sees:
- PV-N9 separated public-wedge package context from private root
- Package manifest: 12 include, 19 exclude
- Generated context: 60 files, 0 blockers
- PV-N8 build blocker remains (build not performed)
- No license activated, no package published, no public repo
- COV-2 partials remain (verification_debt warning-only, wave_files whitelist)

---

*Closed: 2026-05-01*
*Phase: PV-N9*
