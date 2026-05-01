# Ordivon Verify — Changelog Policy

> Defines required changelog structure, content, and governance.
> Not a release. Not a public availability commitment.

## Required Sections

Every changelog entry for a named version must include:

| Section | Required | Description |
|---|---|---|
| Added | Yes | New features, tools, checks |
| Changed | Yes | Modified behavior, config changes |
| Fixed | Yes | Bug fixes |
| Security | Yes | Security-relevant changes (even if no change: "No security changes.") |
| Governance | Yes | Policy, manifest, checker, contract changes |
| Breaking Changes | Yes | Even if none: "None." |
| Known Limitations | Yes | Explicit gaps, partial status, BLOCKED items |
| Release Channel | Yes | "private package prototype", "private beta candidate", etc. |
| Verification Evidence | Yes | Test counts, pr-fast status, build smoke result |

## Internal Receipts vs Public Changelog

- Internal phase receipts (`docs/runtime/*`) are evidence, not public changelog.
- Public changelog (`CHANGELOG.md` in package context) must be extractable
  from receipts but self-contained.
- Internal receipts may reference phases, debt IDs, and internal tooling.
- Public changelog must not contain: debt ledger IDs, internal phase names,
  repo paths, private tooling references.

## Version ↔ Changelog Binding

- Every version in changelog must match pyproject.toml.
- If no version is released, CHANGELOG.md must say "Unreleased" or
  "Development — no versioned release yet."
- The first public release header must match the version exactly.

## Placement

- Package context: `CHANGELOG.md` at root.
- Private repo: `docs/product/ordivon-verify-changelog-policy.md` governs.

---

*Created: 2026-05-01*
*Phase: PV-N12*
*Authority: current_truth / proposal*
