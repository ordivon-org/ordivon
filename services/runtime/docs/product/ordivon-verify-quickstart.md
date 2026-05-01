# Ordivon Verify — Quickstart

Status: **DRAFT** | Date: 2026-05-01 | Phase: PV-10
Tags: `product`, `verify`, `quickstart`, `public`, `draft`
Authority: `proposal`

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed
- A local repository (Ordivon-native or external)

## 1. Run on an Ordivon-Native Repo

```bash
# Run all checks
uv run python scripts/ordivon_verify.py all

# JSON output (for CI / programmatic use)
uv run python scripts/ordivon_verify.py all --json

# Individual checks
uv run python scripts/ordivon_verify.py receipts
uv run python scripts/ordivon_verify.py debt
uv run python scripts/ordivon_verify.py gates
uv run python scripts/ordivon_verify.py docs
```

Expected output: **READY** — all four checks pass.

## 2. Run on an External Repo (Advisory Mode)

Create `ordivon.verify.json` in your repo root:

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

Expected output:
- **DEGRADED** — receipts pass, but governance files (debt/gates/docs) are missing
- **BLOCKED** — if any receipt has contradictory claims

## 3. Move from DEGRADED to READY

DEGRADED means your receipts are clean but you're missing governance infrastructure. To reach READY:

### Step 1: Add a debt ledger

Create `governance/verification-debt-ledger.jsonl`:

```jsonl
{"debt_id": "VD-001", "opened_phase": "init", "category": "pre_existing_tooling_debt", "scope": "example", "description": "Example closed debt.", "risk": "None", "severity": "low", "introduced_by_current_phase": false, "owner": "team", "follow_up": "n/a", "expires_before_phase": "n/a", "status": "closed", "opened_at": "2026-05-01", "closed_at": "2026-05-01", "evidence": "Example.", "notes": "Example."}
```

### Step 2: Add a gate manifest

Create `governance/verification-gate-manifest.json`:

```json
{
  "manifest_id": "my-project-v1",
  "profile": "standard",
  "version": "1.0",
  "gate_count": 2,
  "gates": [
    {"gate_id": "ruff_check", "display_name": "ruff check", "layer": "L0", "hardness": "hard", "command": "ruff check .", "purpose": "Static analysis"},
    {"gate_id": "pytest", "display_name": "pytest suite", "layer": "L0", "hardness": "hard", "command": "pytest tests/ -q", "purpose": "Test suite"}
  ]
}
```

### Step 3: Add a document registry

Create `governance/document-registry.jsonl`:

```jsonl
{"doc_id": "config", "path": "ordivon.verify.json", "type": "config", "status": "current", "authority": "current_status", "last_verified": "2026-05-01", "stale_after_days": 90, "description": "Ordivon Verify config."}
{"doc_id": "readme", "path": "README.md", "type": "readme", "status": "current", "authority": "current_status", "last_verified": "2026-05-01", "stale_after_days": 90, "description": "Project README."}
```

### Step 4: Update config to standard mode

```json
{
  "mode": "standard",
  "debt_ledger": "governance/verification-debt-ledger.jsonl",
  "gate_manifest": "governance/verification-gate-manifest.json",
  "document_registry": "governance/document-registry.jsonl"
}
```

Run again:

```bash
uv run python scripts/ordivon_verify.py all --root . --config ordivon.verify.json
```

Expected: **READY** — all four checks pass.

## 4. Use in Agent Workflow

Add the Ordivon Verify skill to your AI coding agent. See `skills/ordivon-verify/SKILL.md`.

Agent workflow:
1. Agent completes task
2. Agent runs `ordivon verify all`
3. If BLOCKED → agent reports HOLD, does not claim complete
4. If READY → agent reports status with disclaimer

## 5. Use in CI

A GitHub Actions example is at `examples/ordivon-verify/github-action.yml.example`.

Key behaviors:
- BLOCKED → CI should block merge
- DEGRADED → CI should require human review
- READY → CI can pass (no auto-merge)

## 6. Interpret Results

| Status | What It Means | What To Do |
|--------|--------------|-----------|
| **READY** | Selected checks passed | Report evidence. Do not claim authorization. |
| **DEGRADED** | No hard failures, warnings present | Review warnings. Add governance files. |
| **BLOCKED** | Hard failure detected | Fix the failure. Do not proceed. |

**READY does not authorize execution, merge, deployment, trading, Policy activation, or RiskEngine enforcement.**

## 7. Common Mistakes

| Mistake | Why It's Wrong |
|---------|---------------|
| Treating READY as approval | READY means checks passed. The human reviewer is still responsible. |
| Treating BLOCKED as tool failure | BLOCKED is governance success — contradictory claims were detected. |
| Hiding DEGRADED warnings | Warnings today become BLOCKED in strict mode. Address them. |
| Using strict mode before governance files exist | Strict mode requires debt/gate/docs files. Start in advisory mode. |
| Letting agents self-certify without Verify | Agent claims must be verified. "I ran the tests" is a claim — Verify checks it. |
