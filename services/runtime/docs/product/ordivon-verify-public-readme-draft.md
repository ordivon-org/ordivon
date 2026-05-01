# Ordivon Verify

**Verify AI-generated work before you trust it.**

Ordivon Verify is a local-first, read-only CLI that checks whether AI/agent-generated work has honest receipts, visible debt, intact gates, and coherent documentation truth.

---

## The Problem

AI coding agents can write code quickly — but they can also:

- Claim "all tests pass" when tests were skipped
- Write "Skipped Verification: None" while leaving gates unrun
- Call a phase "sealed" with pending checks
- Silently weaken verification gates
- Hide pre-existing debt in prose without registering it
- Confuse CandidateRules with active Policy
- Treat JSONL ledgers as execution authority
- Produce receipts that look official but contradict themselves

Traditional CI checks code behavior. It does not check whether the claims agents make about their work are **honest**.

---

## What Ordivon Verify Checks

| Check | What it verifies |
|-------|-----------------|
| **Receipt Integrity** | No "sealed" with pending, no "skipped: none" with gaps, no overclaim language |
| **Verification Debt** | All debt registered, no overdue, no hidden skipped verification |
| **Gate Manifest** | Baseline gates match manifest, no silent removal or downgrade |
| **Document Registry** | Docs registered, no stale, no dangerous semantic phrases |

---

## Trust Report

```
ORDIVON VERIFY
Status:  READY
Mode:    standard

Checks:
  receipt integrity: ✓ PASS
  verification debt: ✓ PASS
  gate manifest: ✓ PASS
  document registry: ✓ PASS
READY means selected checks passed; it does not authorize execution.
```

### Status Ladder

| Status | Meaning | Action |
|--------|---------|--------|
| **BLOCKED** | Hard failure — contradictory receipt, overdue debt, missing required gate | Fix before proceeding. Do not claim complete. |
| **DEGRADED** | No hard failure — but warnings present (missing governance files, advisory mode) | Human review recommended. Address before moving to strict mode. |
| **READY** | Selected checks passed | Evidence of consistency. Not authorization. |

---

## Quickstart

### Native Ordivon Repo

```bash
uv run python scripts/ordivon_verify.py all
uv run python scripts/ordivon_verify.py all --json
```

### External Repo (Advisory Mode)

Create `ordivon.verify.json`:

```json
{
  "schema_version": "0.1",
  "project_name": "my-project",
  "mode": "advisory",
  "receipt_paths": ["docs/runtime"]
}
```

Run:

```bash
uv run python scripts/ordivon_verify.py all --root . --config ordivon.verify.json
```

### Moving to Standard / READY

Add governance files to reach READY:
- `governance/verification-debt-ledger.jsonl`
- `governance/verification-gate-manifest.json`
- `governance/document-registry.jsonl`

Then switch to standard mode:

```json
{
  "mode": "standard",
  "debt_ledger": "governance/verification-debt-ledger.jsonl",
  "gate_manifest": "governance/verification-gate-manifest.json",
  "document_registry": "governance/document-registry.jsonl"
}
```

---

## Agent Usage

AI coding agents should run Ordivon Verify before claiming completion. See `skills/ordivon-verify/SKILL.md`.

**Agents must not claim "complete" or "sealed" when Verify returns BLOCKED.**

---

## CI Usage

A GitHub Actions example is available at `examples/ordivon-verify/github-action.yml.example`.

- **BLOCKED** → CI should block merge
- **DEGRADED** → CI should require human review
- **READY** → CI can pass, but does not auto-merge

The example is reference only — not an active workflow.

---

## What Ordivon Verify Is NOT

- Not an AI model
- Not an IDE agent
- Not a trading bot
- Not an auto-merge tool
- Not a replacement for tests or CI
- Not a source of truth by itself
- Not SaaS (local CLI only)

---

## Current Maturity

Ordivon Verify is a **prototype / v0** product:
- Local-first CLI
- Dogfooded on fixtures (bad/clean/standard external repos)
- Agent skill and CI example documented
- Not yet packaged for public distribution
- No real customer validation yet
- Public repo / open-source boundary still under design

---

## License

License and public repository packaging are not finalized in this draft.

---

## Learn More

- [Product Brief](ordivon-verify-product-brief.md)
- [CLI Contract](ordivon-verify-cli-contract.md)
- [Adoption Guide](ordivon-verify-adoption-guide.md)
- [Quickstart](ordivon-verify-quickstart.md)
- [Agent Skill](../../skills/ordivon-verify/SKILL.md)
- [CI Example](../../examples/ordivon-verify/README.md)
