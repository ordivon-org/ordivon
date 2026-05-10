# NO-GO Boundary Map — DGP-4

## Authorization Boundaries

- READY/PASS/CLOSED is NOT merge/release/deploy authorization.
- Owner is NOT approver. Owner is accountability metadata.
- Generated view is NOT source_of_truth.
- Snapshot is NOT current truth.
- Receipt is NOT permanent truth.

## Architectural Boundaries

- Do NOT introduce SaaS, bot, MCP server, AI judge, or agent runner without explicit phase authorization.
- Do NOT expand Trade/Health/Finance profile packs.
- Do NOT implement auto-fix without explicit scope and owner approval.
- Do NOT delete legacy code without governance phase.
- Do NOT make schema changes that weaken existing invariants.

## Truth Boundaries

- CandidateRule is NOT Policy without PolicyActivation.
- Lesson is NOT Policy.
- Proposal is NOT current truth.
- Archive is NOT current truth.
- Generated view is NOT source of truth.
- Registry index is NOT source of truth.
- Stage summit is NOT permanent truth by default.

## Evidence Boundaries

- Claim ≠ Evidence.
- Summary ≠ Closure.
- "全绿" ≠ Verified.
- Test pass ≠ Semantic correctness.
- CLI output ≠ Full truth.
- Snapshot ≠ Source of truth.
