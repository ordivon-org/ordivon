# Ordivon Verify — Secret and Private Reference Audit Plan

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-12
Authority: `proposal`

## 1. Audit Purpose

A future public Ordivon Verify wedge cannot leak private Core context, secrets, or internal dogfood noise. This document defines the audit that must be run before any public release.

**No audit has been executed. This is a plan only.**

## 2. Reference Categories to Scan

| Category | Examples | Risk |
|----------|---------|------|
| Secrets / credentials | API keys, tokens, passwords, `.env` content | Critical — never public |
| Broker references | Alpaca, broker URLs, paper/live trading | High — not part of Verify |
| Internal phase receipts | Phase 7P, DG-Z, Post-DG, paper dogfood | High — internal history |
| Private paths | `/root/projects/Ordivon/`, `/mnt/c/Users/` | Medium — misleading externally |
| Internal AGENTS context | AI onboarding docs, phase scaffolds | Medium — confusing externally |
| Private roadmap | Rust kernel, enterprise, commercial strategy | Medium — proprietary |
| Unpublished design notes | Architecture drafts, ontology evolution | Low — not harmful but not intended |
| Absolute user-specific paths | Home directory references | Low — breaks portability |

## 3. Suggested Audit Commands (Future)

```bash
# Secrets and credentials
rg -i "ALPACA_API_KEY|ALPACA_SECRET|API_KEY|SECRET|TOKEN|PASSWORD" \
   --type-not binary src/ tests/ docs/ examples/ skills/

# Broker and trading references
rg -i "alpaca|broker|live trading|paper trading|live.order|paper.order|Phase 7P|Phase 8" \
   --type-not binary src/ tests/ docs/ examples/ skills/

# Internal phase references
rg -i "DG-[0-9]|DG-Z|Post-DG|Phase 7P|Stage Summit|verification-debt-ledger|document-governance" \
   --type-not binary src/ tests/ docs/ examples/ skills/

# Private paths
rg "/root/projects|/mnt/c/Users|/home/" \
   --type-not binary src/ tests/ docs/ examples/ skills/

# Private repo references
rg "zycxfyh/Ordivon|private.*repo|internal.*only" \
   src/ tests/ docs/ examples/ skills/
```

## 4. Allowed Matches

Some matches are legitimate and should NOT be removed:

| Pattern | Why Allowed |
|---------|-----------|
| `ALPACA_API_KEY` in `.env.example` or docs | Documentation of env vars users must set |
| `verification-debt-ledger` in schema docs | Public schema documentation |
| `document-registry` in schema docs | Public schema documentation |
| `Phase 8` mention as "not yet" or "deferred" | Boundary statement |
| `DG Pack` mention as "private, not included" | Boundary statement |

These should be documented in the audit receipt with explicit justification.

## 5. Required Audit Receipt

Before public alpha, create an audit receipt with:

- Commands run
- Matches found (categorized)
- Allowed matches (with justification)
- Removed matches (before/after)
- Files cleaned
- Final decision: CLEAN / NEEDS_CLEANUP / BLOCKED

## 6. Tools (Future Options)

| Tool | Purpose |
|------|---------|
| `rg` (ripgrep) | Fast pattern search |
| `git-secrets` | Prevents committing secrets |
| `trufflehog` | Scans git history for secrets |
| `gitleaks` | Detects hardcoded secrets |

No tool has been run. This is a plan only.

## 7. Non-Activation Clause

No audit has been executed. No secrets have been found or removed. This document defines the audit that must be run before any public release.
