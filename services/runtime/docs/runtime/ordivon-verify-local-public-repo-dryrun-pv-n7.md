# PV-N7 — Local Public Repo Dry-run

## Purpose

Create a local-only public-repo-shaped extraction of Ordivon Verify and prove
the curated wedge can stand alone without private Ordivon context.

## Dry-run Scope

- Source: private Ordivon repo
- Output: `.tmp/ordivon-verify-public-repo-dryrun/` (not committed)
- Manifest: `docs/product/ordivon-verify-public-repo-file-manifest.json`

## Generated Local Repo Shape

```
ordivon-verify-public-repo-dryrun/
  README.md                    (generated public README)
  pyproject.toml               (generated package metadata)
  src/ordivon_verify/          (package source)
  schemas/                     (5 JSON Schema files)
  ordivon_verify.py            (CLI wrapper)
  examples/quickstart/         (quickstart fixture)
  examples/github-action.yml.example
  skills/ordivon-verify/SKILL.md
  docs/quickstart.md
  docs/adoption.md
  docs/ci.md
  docs/pr-comments.md
  tests/unit/
  tests/fixtures/
```

## File Manifest Summary

- 16 copied (7 runtime, 2 schema, 4 examples, 3 docs/tests)
- 13 excluded (adapters, domains, orchestrator, capabilities, intelligence,
  apps, policies, docs/archive, docs/governance, docs/ai, docs/runtime/paper-trades)
- 0 missing required

## Audit Result

PV-N6 audit (re-run on source): 0 blocking findings.

Dry-run scan: 28 structural findings in generated repo — all in safe
negative/boundary context (e.g. "not production-ready", "evidence, not
authorization", "PFIOS/AegisOS are historical").

## Smoke Result

- manifest: valid, 16 include entries
- excluded paths confirmed absent: adapters, domains, orchestrator,
  capabilities, intelligence, apps, policies
- no private paths in generated repo
- source files not mutated

## What PV-N7 Proves

1. Ordivon Verify wedge can be extracted into a clean local repo shape.
2. Private Core paths are excluded per manifest.
3. Generated repo has README, pyproject.toml, package source, schemas.
4. Extraction is repeatable and does not mutate source.

## What PV-N7 Does NOT Prove

- No real public repo created.
- No package published.
- No license activated.
- No remote CI configured.
- Final pre-release audit on extracted repo still required.

## Boundary Confirmation

- Local dry-run only
- No public release / public repo / license activation / package publishing
- No CI change / SaaS / MCP server
- Phase 8 DEFERRED
- Coverage plane active

## Next Recommended Phase

PV-N8: Continue with remaining release blockers or cycle back to Core/Pack
development.

---

*Closed: 2026-05-01*
*Phase: PV-N7*
*Task type: tooling/docs/audit — local extraction dry-run*
*Risk level: R1*
