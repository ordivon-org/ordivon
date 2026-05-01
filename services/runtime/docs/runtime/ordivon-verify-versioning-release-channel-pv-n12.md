# PV-N12 — Versioning / Changelog / Release Channel Policy

## Purpose

Define release-channel, versioning, changelog, schema compatibility, and
maturity-claim semantics before any public alpha or package publishing.

## Versioning Decision

Generated package context version: `0.0.1.dev0` (was `0.1.0`).

Rationale:
- `0.1.0` could be misinterpreted as a public release version.
- `0.0.1.dev0` is deliberate — it signals "development snapshot, not a release."
- No semver commitment at prototype stage.
- Version bumps require explicit phase authorization.

See: `docs/product/ordivon-verify-versioning-policy-pv-n12.md`

## Changelog Decision

Changelog policy requires 9 sections per version entry:
Added, Changed, Fixed, Security, Governance, Breaking Changes,
Known Limitations, Release Channel, Verification Evidence.

Internal receipts are not public changelog. Public changelog must not
contain private debt IDs, internal phase names, or repo paths.

See: `docs/product/ordivon-verify-changelog-policy.md`

## Release Channel Decision

8-stage maturity ladder: internal prototype → stable.

Current: **private package prototype / private beta candidate.**

Each stage has explicit gate requirements. Public alpha requires:
final audit, license activation, public repo decision, public CI,
contribution policy, issue templates, changelog/versioning final,
schema compatibility policy, explicit human release summit.

No stage transition without explicit authorization.

## Schema Compatibility Decision

- Current `schema_version: "0.1"` is prototype.
- Breaking changes allowed before public alpha if documented.
- Public alpha requires schema compatibility notes.
- Public beta requires migration notes.
- Stable requires semver compatibility policy.
- PV-N11 schema location via `sys.prefix/schemas/` is an implementation
  detail — final packaging strategy may change before public alpha.
  This is documented as a known caveat in the compatibility policy.

## Current Maturity Verdict

```
Maturity:        private package prototype / private beta candidate
Version:         0.0.1.dev0
Published:       NO
License:         NOT ACTIVATED
Public repo:     NO
Public alpha:    NOT CLAIMED
```

## What PV-N12 Proves

1. Release-channel semantics exist and are explicit.
2. Versioning policy prevents accidental public-release overclaims.
3. Changelog governance ensures evidence-backed, section-complete entries.
4. Schema compatibility requirements are staged — no premature stability guarantee.
5. Package context version is prototype-safe.

## What PV-N12 Does NOT Prove

1. That release gates have been exercised (no release has occurred).
2. That public alpha gates are ready (they are defined but not passed).
3. That the schema compatibility policy has been tested across versions
   (only one version exists).

## Remaining Release Blockers

- Public CI configuration
- Public alpha summit approval
- Final audit on extracted public repo
- License activation decision

## Boundary Confirmation

- Release policy only. No release. No publish. No license.
- Phase 8 DEFERRED. All NO-GO intact.
- COV-2 partials remain explicit.

## New AI Context Check

A fresh AI reading root docs sees:
- PV-N12 defines release-channel policy, versioning, changelog structure.
- Package context version is 0.0.1.dev0 — deliberately not a release version.
- Maturity: private package prototype / private beta candidate.
- No license activated, no package published, no public repo.
- Schema compatibility is prototype-level.
- READY is evidence, not authorization.

---

*Closed: 2026-05-01*
*Phase: PV-N12*
