# PV-N3 — Public Quickstart Dogfood

## Purpose

Create and dogfood the first future-public Ordivon Verify quickstart. Validate
that a future external user can follow a clean quickstart, reach READY, and
understand the status semantics — without publishing anything.

## Quickstart Artifact Under Test

- `docs/product/ordivon-verify-public-quickstart-v0.md` — Public-style quickstart
- `examples/ordivon-verify/quickstart/` — Self-contained READY fixture
- `src/ordivon_verify/schemas/` — Prototype schemas
- `scripts/ordivon_verify.py` / `python -m ordivon_verify` — Entry points

## Scenario A — Native READY

```
uv run python scripts/ordivon_verify.py all
→ READY (exit 0)
```

## Scenario B — Package Module READY

```
uv run python -m ordivon_verify all
→ READY (exit 0)
```

## Scenario C — Quickstart Example READY

```
uv run python scripts/ordivon_verify.py all \
  --root examples/ordivon-verify/quickstart \
  --config examples/ordivon-verify/quickstart/ordivon.verify.json
→ READY (exit 0)
```

Quickstart fixture contents:
- `ordivon.verify.json` — standard mode config
- `receipts/clean-receipt.md` — clean receipt
- `governance/verification-debt-ledger.jsonl` — empty (no debt)
- `governance/verification-gate-manifest.json` — 2 gates
- `governance/document-registry.jsonl` — 2 registered docs
- `README.md` — fixture documentation

## Scenario D — Clean Advisory DEGRADED

```
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_clean_external_repo \
  --config tests/fixtures/ordivon_verify_clean_external_repo/ordivon.verify.json
→ DEGRADED (exit 2)
```

## Scenario E — Bad External BLOCKED

```
uv run python scripts/ordivon_verify.py all \
  --root tests/fixtures/ordivon_verify_external_repo \
  --config tests/fixtures/ordivon_verify_external_repo/ordivon.verify.json
→ BLOCKED (exit 1)
```

## Coverage Plane Confirmation

- Document registry checker passes with coverage summary
- No unclassified current-scope docs
- Quickstart docs are registered or explicitly governed
- No unsafe identity surfaces in quickstart content

## Product Interpretation

- READY: selected checks passed — evidence, not authorization
- DEGRADED: honest midpoint — governance incomplete, needs review
- BLOCKED: governance success — hard failure caught
- Quickstart is future-public draft only

## What PV-N3 Proves

1. A future external user can follow a clean quickstart
2. An example project can reach READY in standard mode
3. Schema references are discoverable
4. Public-style docs can be written without overclaiming
5. Coverage-aware governance survives public-facing documentation

## What PV-N3 Does NOT Prove

- No public repo, package publishing, or license activation
- No marketplace action, SaaS, or MCP server
- No real customer validation
- No Phase 8 readiness
- No production deployment

## Next Recommended Phase

PV-N4 — Private Package Install Smoke

---

*Closed: 2026-05-01*
*Phase: PV-N3*
*Task type: docs + example fixture + product dogfood*
*Risk level: R0/R1*
