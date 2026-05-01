# Ordivon Verify — Versioning Policy

> Authoritative until Stage Summit overrides it. Not a release. Not a license.
> Not a public-availability commitment.

## Release Maturity Ladder

| Stage | Meaning | Allowed Claims | Current |
|---|---|---|---|
| internal prototype | Private dev; may break | "internal only" | — |
| private package prototype | Local build/install works | "private prototype" | — |
| private beta candidate | Candidate for private beta | "private beta candidate" | **current** |
| private beta | Internal team usage | "private beta" | not yet |
| public alpha candidate | Pre-audit public alpha | "public alpha candidate" | not yet |
| public alpha | Early public availability | "public alpha" | not yet |
| public beta | Broader public testing | "public beta" | not yet |
| stable | Semver compatibility guarantee | "stable" | not yet |

**Current status: private package prototype / private beta candidate.**

Allowed in current docs:
- "private package prototype"
- "private beta candidate"
- "future public wedge"
- "not yet published"
- "not production-ready"

Forbidden in current docs/packages:
- "public alpha"
- "public beta"
- "stable"
- "production-ready"
- "published to PyPI" (as fact, not as future tense)

## Version Semantics

### Current (Prototype)

```
0.0.1.dev0   ← current generated package context version
```

Rules:
- Prototype pre-releases use `0.0.x.devN` numbering.
- `dev` suffix means "development snapshot — not a release."
- No semver commitment yet.

### Future (Post Public-Alpha Approval)

```
0.1.0a1       ← first public alpha
0.1.0a2       ← subsequent alpha
0.1.0b1       ← first public beta
1.0.0         ← stable release
```

Rules:
- Public alpha approval required before `aN` suffix.
- Public beta approval required before `bN` suffix.
- Stable release gate required before `1.0.0`.
- Breaking changes must be documented before alpha N+1.
- Schema compatibility notes required from public alpha onward.
- Migration notes required from public beta onward.

## Who Can Change

- Version number: only with explicit phase authorization.
- Release channel claim: never without Stage Summit approval.
- Maturity status: only by Verdict or Stage Summit.

## Anti-Overclaim Guards

- `pyproject.toml` version alone does not imply release readiness.
- "0.0.1.dev0" is deliberate — it signals "not a real version."
- Any automated version bump must be explicitly approved.
- No version in package metadata implies "not public release."

---

*Created: 2026-05-01*
*Phase: PV-N12*
*Authority: current_truth / proposal*
