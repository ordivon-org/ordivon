# Ordivon Verify — CLI Contract

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-1
Tags: `product`, `verify`, `cli`, `contract`, `commands`, `exit-codes`, `report-schema`
Authority: `proposal` | AI Read Priority: 2

## 1. CLI Command Set

### 1.1 Required Commands (v0)

```
ordivon verify              Run all checks (receipts + debt + gates + docs)
ordivon verify receipts     Scan receipts for contradictions
ordivon verify debt         Check debt ledger invariants
ordivon verify gates        Verify gate manifest integrity
ordivon verify docs         Check document registry + semantic safety
ordivon verify all          Alias for `ordivon verify`
```

### 1.2 Optional Future Commands

```
ordivon init                Create ordivon.verify.json in current repo
ordivon explain             Explain a specific finding in detail
ordivon report --json       Output machine-readable JSON report
ordivon report --markdown   Output markdown report for PR comments
ordivon config validate     Validate ordivon.verify.json schema
ordivon config show         Display current effective config
```

### 1.3 Command-to-Checker Mapping

| CLI Command | Underlying Checker(s) | What It Verifies |
|------------|----------------------|-----------------|
| `ordivon verify receipts` | `check_receipt_integrity.py` | No "sealed" with pending, no "skipped: none" with gaps, no overclaim language |
| `ordivon verify debt` | `check_verification_debt.py` | All debt registered, no overdue, no high/blocking unaddressed |
| `ordivon verify gates` | `check_verification_manifest.py` | Manifest matches baseline, no gate removal/downgrade, no no-op commands |
| `ordivon verify docs` | `check_document_registry.py` | Registry invariants, freshness, dangerous phrases, semantic safety |
| `ordivon verify` | All above + `run_verification_baseline.py` | Combined trust report |

## 2. Input Assumptions

### 2.1 Repo Detection

The CLI auto-detects repo type by presence of key files:

| Files Present | Repo Type | Mode |
|--------------|-----------|------|
| `docs/governance/verification-debt-ledger.jsonl` + `docs/governance/verification-gate-manifest.json` + `docs/governance/document-registry.jsonl` | Ordivon-native | Full (all checks) |
| `ordivon.verify.json` at repo root | External with config | Configured (receipts + optional debt/gates) |
| Neither | External without config | Advisory (receipt scan only) |

### 2.2 Modes

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Full** | Ordivon-native repo detected | All checks active. Missing optional config is warning. |
| **Configured** | `ordivon.verify.json` found | Configured checks active. Missing optional files are warnings. |
| **Advisory** | No config, no Ordivon metadata | Receipt scan only. All other checks report "not configured." |

### 2.3 Local vs CI Mode

| Mode | Detected By | Behavior |
|------|-----------|----------|
| **Local** | `CI` env var unset or `ORDIVON_VERIFY_MODE=local` | Human-readable output, color, suggestions |
| **CI** | `CI=true` or `ORDIVON_VERIFY_MODE=ci` | Machine-parseable output, no color, strict exit codes |

## 3. Config File — ordvon.verify.json

### 3.1 Schema (v0.1)

```json
{
  "schema_version": "0.1",
  "project_name": "my-project",
  "receipt_paths": [
    "docs/runtime",
    "docs/product",
    "docs/ai"
  ],
  "debt_ledger": "docs/governance/verification-debt-ledger.jsonl",
  "gate_manifest": "docs/governance/verification-gate-manifest.json",
  "document_registry": "docs/governance/document-registry.jsonl",
  "mode": "standard",
  "output": "human",
  "checks": {
    "receipts": true,
    "debt": true,
    "gates": false,
    "docs": true,
    "semantics": true
  },
  "ignore_patterns": [
    "archive/",
    "node_modules/"
  ],
  "dangerous_phrases": [
    "live trading active",
    "auto trading enabled",
    "Policy is now active",
    "Phase 8 started"
  ]
}
```

### 3.2 Field Definitions

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `schema_version` | Yes | — | Config schema version for forward compatibility |
| `project_name` | No | directory name | Human-readable project identifier |
| `receipt_paths` | No | `["docs/runtime", "docs/product"]` | Directories to scan for receipt integrity |
| `debt_ledger` | No | — | Path to verification debt JSONL ledger |
| `gate_manifest` | No | — | Path to gate manifest JSON |
| `document_registry` | No | — | Path to document registry JSONL |
| `mode` | No | `"standard"` | `strict`, `standard`, or `advisory` |
| `output` | No | `"human"` | `human`, `json`, or `markdown` |
| `checks` | No | All true | Enable/disable individual check categories |
| `ignore_patterns` | No | `[]` | Glob patterns to exclude from scan |
| `dangerous_phrases` | No | Ordivon defaults | Additional project-specific dangerous phrases |

## 4. Exit Code Contract

| Exit Code | Status | Meaning |
|-----------|--------|---------|
| **0** | READY | All enabled checks pass. No contradictions. No overdue debt. All gates intact. |
| **1** | BLOCKED | Hard failure: receipt contradiction, overdue debt, gate removed/downgraded, dangerous phrase in current docs. |
| **2** | DEGRADED / NEEDS_REVIEW | Non-blocking issues: warnings, missing optional config, pre-existing noise, tool limitations. |
| **3** | CONFIG ERROR | `ordivon.verify.json` invalid, missing required field, schema version mismatch. |
| **4** | RUNTIME ERROR | Tool not found, file read error, unexpected exception. |

### CI Integration

```yaml
# Example GitHub Actions step
- name: Ordivon Verify
  run: ordivon verify
  # Exit 0 = pass, exit 1 = block, exit 2 = warning annotation
```

CI can choose to treat exit code 2 as pass (advisory mode) or fail (strict mode) depending on team preference.

## 5. Report Schema

### 5.1 Human Output (default)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Ordivon Verify — Trust Report
 Project: my-project
 Mode: standard | Repo: external (configured)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Status: READY

 Receipts    ✓  20 scanned, 0 contradictions
 Debt        ✓  0 open, 4 closed
 Gates       —  not configured
 Docs        ✓  31 registered, 0 stale
 Semantics   ✓  no dangerous phrases

 Trust decision: safe to proceed.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5.2 JSON Output (`--json`)

```json
{
  "ordivon_verify_version": "0.1.0",
  "timestamp": "2026-05-01T06:00:00Z",
  "project_name": "my-project",
  "repo_type": "external_configured",
  "mode": "standard",
  "status": "READY",
  "exit_code": 0,
  "checks": {
    "receipts": {
      "status": "pass",
      "files_scanned": 20,
      "hard_failures": 0,
      "warnings": 0,
      "details": []
    },
    "debt": {
      "status": "pass",
      "total": 4,
      "open": 0,
      "closed": 4,
      "overdue": 0,
      "high_blocking": 0,
      "details": []
    },
    "gates": {
      "status": "not_configured",
      "details": ["No gate manifest found. Skipped."]
    },
    "docs": {
      "status": "pass",
      "total_registered": 31,
      "stale": 0,
      "dangerous_phrases": 0,
      "details": []
    },
    "semantics": {
      "status": "pass",
      "violations": 0,
      "details": []
    }
  },
  "hard_failures": [],
  "warnings": [],
  "suggestions": [
    "Add gate manifest to enable gate integrity checks.",
    "Add debt ledger to enable debt tracking."
  ]
}
```

### 5.3 Markdown Output (`--markdown`)

```markdown
## Ordivon Verify — Trust Report

**Project**: my-project | **Mode**: standard | **Status**: READY

| Check | Result | Detail |
|-------|--------|--------|
| Receipts | ✅ | 20 scanned, 0 contradictions |
| Debt | ✅ | 0 open, 4 closed |
| Gates | — | not configured |
| Docs | ✅ | 31 registered, 0 stale |
| Semantics | ✅ | no dangerous phrases |

**Trust decision**: safe to proceed.
```

## 6. Check Taxonomy

### 6.1 Hard Failures (exit 1)

These always block:

| Failure | Detected By | Example |
|---------|-----------|---------|
| Receipt contradiction | `check_receipt_integrity.py` | "Skipped: None" but text says "X not run" |
| SEALED with pending | `check_receipt_integrity.py` | "SEALED" but verification list shows unchecked items |
| Clean working tree with untracked | `check_receipt_integrity.py` | "clean" but `git status` shows untracked |
| Stale baseline count | `check_receipt_integrity.py` | Doc says 7/7 but baseline is 11/11 |
| Ruff clean overclaim | `check_receipt_integrity.py` | "ruff clean" but global ruff would fail |
| CandidateRule as Policy | `check_receipt_integrity.py` | "validated" applied to CandidateRule |
| Open overdue debt | `check_verification_debt.py` | Debt with expiry before today, still open |
| High/blocking debt unaddressed | `check_verification_debt.py` | Debt severity high or blocking, still open |
| Gate removed from manifest | `check_verification_manifest.py` | Gate present last run, missing now |
| Gate downgraded (hard→soft) | `check_verification_manifest.py` | Hard gate changed to advisory/escalation |
| No-op gate command | `check_verification_manifest.py` | Gate command that always exits 0 |
| Manifest/baseline mismatch | `check_verification_manifest.py` | Manifest says 11 gates, baseline has 10 |
| Dangerous phrase in current doc | `check_document_registry.py` | "Phase 8 active" in current_status doc |
| Ledger as execution authority | `check_document_registry.py` | "ledger authorizes" in receipt |
| Phase 8 active phrase | `check_document_registry.py` | "live trading active" in current doc |

### 6.2 Warnings (exit 2)

These do not block but are reported:

| Warning | Example |
|---------|---------|
| Missing optional config | No `ordivon.verify.json` in external repo |
| Pre-existing tool limitation | Ruff Markdown requires `--preview` |
| Historical noise (out-of-scope) | 4 F401 in pre-existing test files |
| Unregistered docs | `docs/` file not in registry |
| Stale but not dangerous doc | Doc last verified >30 days ago |
| Advisory mode active | Running with `mode: advisory` |

## 7. External Repo Adaptation

### 7.1 Quick Start for Non-Ordivon Repos

```bash
# Step 1: Create minimal config
cat > ordivon.verify.json << 'EOF'
{
  "schema_version": "0.1",
  "project_name": "my-project",
  "mode": "advisory",
  "receipt_paths": ["docs/runtime", "docs/product"],
  "checks": {
    "receipts": true,
    "debt": false,
    "gates": false,
    "docs": true,
    "semantics": true
  }
}
EOF

# Step 2: Run in advisory mode
ordivon verify

# Step 3: Review report, add debt ledger, upgrade to standard mode
```

### 7.2 Gradual Adoption Path

| Stage | Config | Checks Active | Blocking? |
|-------|--------|--------------|-----------|
| 1. Try | `mode: advisory` | Receipts only | No |
| 2. Adopt | `mode: standard` + receipt_paths | Receipts + docs + semantics | Yes (hard failures) |
| 3. Harden | Add debt_ledger | + Debt tracking | Yes |
| 4. Full | Add gate_manifest | + Gate integrity | Yes |

## 8. Security and Side-Effect Model

Ordivon Verify is **read-only by default**:

| Property | Guarantee |
|----------|-----------|
| **No network** | No API calls, no HTTP, no network I/O |
| **No broker/API** | No trading, no finance adapter, no order placement |
| **No file writes** | No files created or modified (except `--write-init` in future) |
| **No auto-commit** | No git operations, no staging, no commits |
| **No policy activation** | No RiskEngine, no Policy platform, no enforcement |
| **No execution authorization** | Reports trust; does not authorize any action |
| **Read-only filesystem** | Reads markdown, JSON, JSONL; never writes |

Future optional: `ordivon init --write` to create config file. Always opt-in, never automatic.

## 9. Relation to Existing Scripts

| Existing Script | PV-1 Role | PV-2 Mapped To |
|----------------|-----------|---------------|
| `check_receipt_integrity.py` | Reference implementation | `ordivon verify receipts` |
| `check_verification_debt.py` | Reference implementation | `ordivon verify debt` |
| `check_verification_manifest.py` | Reference implementation | `ordivon verify gates` |
| `check_document_registry.py` | Reference implementation | `ordivon verify docs` |
| `check_paper_dogfood_ledger.py` | Phase 7P-specific | Not part of PV (phase-specific) |
| `check_architecture.py` | Layer L4 | Included in `ordivon verify` — full mode |
| `check_runtime_evidence.py` | Layer L5 | Included in `ordivon verify` — full mode |
| `run_verification_baseline.py` | Orchestrator | `ordivon verify` — full mode equivalent |
| `evals/run_evals.py` | Eval corpus | Not part of PV (Ordivon-internal) |

### Implementation Note

PV-2 (`ordivon_verify.py`) wraps these scripts, not replaces them. Each checker remains independently runnable. The CLI adds:
- Unified command surface
- Config file discovery
- Mode selection
- Output formatting (human/JSON/markdown)
- Exit code normalization

## 10. Boundary Confirmation

This CLI contract is a **proposal**. It does not:

- Implement any code (deferred to PV-2)
- Reopen DG Pack
- Start Phase 8
- Enable any trading, broker, or live action
- Activate Policy or RiskEngine
- Require new dependencies
- Change existing checker scripts

## 11. PV-2 Implementation Sketch

```
scripts/ordivon_verify.py          # CLI entry point
  ├── parse_args()                  # argparse: subcommands
  ├── discover_config()             # Find ordivon.verify.json or detect Ordivon-native
  ├── run_receipt_check()           # Wraps check_receipt_integrity.py
  ├── run_debt_check()              # Wraps check_verification_debt.py
  ├── run_gate_check()              # Wraps check_verification_manifest.py
  ├── run_docs_check()              # Wraps check_document_registry.py
  ├── build_report()                # Assembles TrustReport dict
  ├── format_human()                # Rich table output
  ├── format_json()                 # JSON dump
  ├── format_markdown()             # Markdown table
  └── exit_with_status()            # Maps status to exit code 0-4

tests/unit/product/test_ordivon_verify_cli.py  # Tests
```

Tests should cover:
- All four exit codes
- JSON output schema validation
- Config file parsing (valid, invalid, missing)
- Mode selection (full, configured, advisory)
- Local vs CI output format
- Subcommand dispatch
- Checker integration (mock or real)
