# Phase Receipt Standard — DGP-5

Status: **CURRENT** | Date: 2026-05-09 | Phase: DGP-5
Authority: current_status | Owner: Governance

## Purpose

Define the required structure for every Ordivon phase closure receipt. A receipt is phase closure evidence — it records what was done, what was validated, what debts remain, and what a new AI needs to know to continue. It is NOT release authorization.

## Required Fields

Every receipt must include:

1. **Phase** — Phase identifier (e.g. DGP-2, RG-10, RCP-O1).

2. **Status** — One of: CLOSED, PARTIAL, BLOCKED.

3. **Risk level** — R0 (no write/no auth impact) to R3 (write/auth impact).

4. **Authority impact** — Which authority layer was affected (e.g. current_truth only).

5. **Authorization impact** — Must state "none" unless phase explicitly changed authorization semantics.

6. **Files changed** — Exact list with paths.

7. **Implementation summary** — What was built/changed.

8. **Validation** — Raw command output, not "全绿" or "PASS". Include test counts, ruff output, reconciler counts.

9. **Known debts** — What was deliberately NOT fixed.

10. **NO-GO confirmation** — What the phase did NOT do, must NOT be inferred.

11. **New AI Context Check** — Can a new AI, after reading onboarding docs, understand what this phase did? Specific questions to verify.

12. **Git status** — `git status --short` or summary.

13. **Commit SHA** — If committed.

## Hard Rules

- Claim ≠ Evidence. A receipt saying "已完成" without raw command output is incomplete.
- Receipt is evidence, not authorization. CLOSED does not mean merge/release/deploy.
- Receipt must not say "全线闭合" unless every predicate is verified by reproducible command output.
- Receipt debts are explicit governance acknowledgments, not hidden omissions.
