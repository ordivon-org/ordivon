# Post-DG-H2-R — Close VD-001 Ruff Markdown Preview Debt (Re-verification Receipt)

Status: **SEALED** | Date: 2026-04-30 | Phase: Post-DG-H2-R
Authority: `current_status` | Type: `verification-receipt`

## 1. Phase

Post-DG-H2-R — Re-verification and Stage Summit back-propagation for VD-001 closure.

## 2. VD-001 Investigation Result

VD-2026-04-30-001 was originally registered as "AGENTS.md ruff markdown preview issue"
(category: `pre_existing_tooling_debt`). Re-investigation proved:

- `ruff format --check AGENTS.md` → FAIL (exit 2). Reason: "Markdown formatting is experimental, enable preview mode."
- `ruff format --check --preview AGENTS.md` → PASS (exit 0). "1 file already formatted."
- `ruff format --diff --preview AGENTS.md` → PASS. Zero diff.

**AGENTS.md has no formatting defect.** The failure is exclusively a Ruff tool limitation
(preview feature-gate for Markdown formatting) combined with a command mismatch
(verification command lacked `--preview`).

### Failure Classification

| Class | Applies | Evidence |
|-------|---------|----------|
| `object_defect` | No | Zero diff with `--preview` |
| `tool_limitation` | Yes | Ruff requires `--preview` for Markdown |
| `command_mismatch` | Yes | Stable-mode check omitted `--preview` |
| `spec_mismatch` | Yes | "Ruff stable supports Markdown" is a false spec |

VD-001 closed by reclassification (`closed_by_reclassification`).

## 3. Why AGENTS.md Was Not Modified

The source-of-truth document (AGENTS.md) must not be mutated to satisfy a
misclassified checker. External tool output is evidence, not authority.
VD-001 was never an AGENTS.md problem — it was a tool maturity + command issue.

## 4. Files Changed

| File | Change | Commit |
|------|--------|--------|
| `docs/governance/verification-debt-ledger.jsonl` | VD-001 status open→closed, closed_at 2026-04-30, closure_reason closed_by_reclassification, evidence/notes updated | `af294d1` (prior) |
| `AGENTS.md` | Open debt summary updated to "none registered (VD-001-004 all closed)" | `af294d1` (prior) |
| `docs/governance/verification-debt-policy.md` | Added §8 failure_class + closure_reason framework, §9.3 VD-001 case study | `459747a` (prior) |
| `docs/governance/verification-signal-classification.md` | New document: signal classification rules from VD-001 lesson | `459747a` (prior) |
| `docs/governance/README.md` | Status CLOSING→CLOSED, debt table updated to 0 open, VD-001 removed from Post DG-Z | `0ee159e` |
| `docs/product/document-governance-stage-summit-dg-z.md` | §3 evidence matrix (0 open/4 closed), §5a VD-004 (CLOSED), §6 debt table (all closed), §9 AI context check (0 open debt), §10 recommendations (VD-001 removed) | `0ee159e` |
| `docs/runtime/post-dg-h2-close-ruff-preview-debt-receipt.md` | This receipt | `0ee159e` |

**AGENTS.md was not modified for VD-001.** The only AGENTS.md change in `af294d1`
was updating the open debt summary line to reflect the already-closed ledger state.
The file content was never a formatting defect — zero diff with `ruff format --diff --preview`.

### Commit Chain

```
af294d1 chore: close Ruff markdown preview debt       ← ledger + AGENTS.md
459747a docs: formalize verification signal classification from VD-001 lesson
4f9be1a docs: add verification signal classification reminder
bb3c07d docs: add verification signal classification rule to output contract
0ee159e chore: close Ruff markdown preview debt by reclassification  ← receipt + Stage Summit back-propagation (this commit)
```

## 5. Verification Debt Ledger

| ID | Status | Closure Reason |
|----|--------|---------------|
| VD-2026-04-30-001 | closed | closed_by_reclassification (tool_limitation + command_mismatch) |
| VD-2026-04-30-002 | closed | fixed_by_deletion (.coveragerc removed DG-6D) |
| VD-2026-04-30-003 | closed | fixed_by_deletion (.pre-commit-config.yaml removed DG-6D) |
| VD-2026-04-30-004 | closed | fixed_by_code_change (shallow copy → deepcopy, Post-DG-H1) |

**Registered open verification debt: zero (0).**

## 6. Non-DG F401 Note

4 F401 unused imports in Phase 5/H-era test files remain out-of-scope.
Not registered as DG debt. Not hidden. Classified as historical_noise.
To be addressed in future tooling hygiene phase.

## 7. Verification Results

| Check | Result |
|-------|--------|
| `ruff format --check AGENTS.md` (stable) | FAIL (expected tool limitation) |
| `ruff format --check --preview AGENTS.md` | PASS |
| `ruff format --diff --preview AGENTS.md` | PASS (no diff) |
| `ruff format --check --preview docs/* AGENTS.md` | PASS (90 files) |
| `ruff check docs/*` | PASS |
| `check_verification_debt.py` | PASS (0 open, 4 closed) |
| `check_receipt_integrity.py` | PASS (20 files, 0 hard failures) |
| `check_verification_manifest.py` | PASS (11/11) |
| `check_document_registry.py` | PASS (31 docs) |
| `check_paper_dogfood_ledger.py` | PASS (30 events, 16 invariants) |
| `run_verification_baseline.py --profile pr-fast` | 11/11 PASS |
| `pytest tests/unit/governance/ -q` | 192 passed, 0 xfail/xpass |

## 8. New AI Context Check

A fresh AI reading root docs + verification-debt-ledger + this receipt would understand:

- DG Pack foundation stage remains CLOSED.
- VD-001 was closed by reclassification, not file change. AGENTS.md unchanged.
- VD-004 was fixed in Post-DG-H1 (shallow copy bug). Tests now deterministic.
- Registered open verification debt is zero.
- Non-DG F401 historical noise remains out-of-scope and not hidden.
- pr-fast remains 11/11.
- Phase 8 remains DEFERRED.
- All live/broker/auto/Policy/RiskEngine NO-GO boundaries remain intact.
- Ruff Markdown checks must use `--preview` until Ruff stabilizes Markdown formatting.
- Checkers validate consistency/honesty, not action authorization.

## 9. Git Status

Working tree: clean after commit.
Commit hash: 6d037d6
Tag: post-dg-h2-close-ruff-preview-debt

## 10. Semantic Checks

- Closing VD-001 does not mean global tooling hygiene is complete — confirmed.
- Non-DG F401 historical noise remains out-of-scope until H3 — confirmed.
- DG Pack remains CLOSED — confirmed.
- pr-fast remains 11/11 — confirmed.
- Phase 8 remains DEFERRED — confirmed.
- Live trading, broker write, auto trading, Policy activation, and RiskEngine enforcement remain NO-GO — confirmed.
- AGENTS.md was not modified for a misclassified checker — confirmed.

## 11. Non-Activation Clause

This receipt closes verification debt VD-001 by reclassification. It does not authorize
any trading action, activate any Policy, modify any RiskEngine rule, or open any new phase.
All NO-GO boundaries remain in full effect.
