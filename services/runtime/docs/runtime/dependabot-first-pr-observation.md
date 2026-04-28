# Dependabot First PR Observation (Phase 4.6)

Status: **COMPLETE** — First PRs observed, triaged, recommendations issued
Date: 2026-04-28
Phase: 4.6
Tags: `dependabot`, `observation`, `triage`, `github-actions`, `supply-chain`

## 1. Purpose

Observe and triage the first Dependabot PRs created after Phase 4.5
enablement. Validate that Dependabot PRs pass through Repo Governance,
CI, Security, and CodeQL without bypassing any gate. Issue merge/hold
recommendations based on risk classification.

## 2. Phase 4.5 Remote Receipt Correction

The Phase 4.5 remote receipt stated "No Dependabot PRs created
(schedule = Monday 09:00, not yet triggered)." This was **incorrect**.

**Actual behavior**: Dependabot ran immediately upon config push
(`83c28ad`) and created 2 PRs within minutes:

| PR | Dependency | From → To | Created |
|----|-----------|-----------|---------|
| #3 | actions/upload-artifact | v4 → v7 | 2026-04-28 16:37 UTC |
| #4 | github/codeql-action | v3 → v4 | 2026-04-28 16:37 UTC |

**Lesson**: Dependabot performs an initial check on first config push,
regardless of the weekly schedule. The schedule controls subsequent
scans, not the initial one. Future phases should expect immediate PRs
on enablement.

## 3. PR #3: bump actions/upload-artifact from 4 to 7

### 3.1 PR Metadata

| Property | Value |
|----------|-------|
| PR | [#3](https://github.com/zycxfyh/AegisOS/pull/3) |
| Branch | `dependabot/github_actions/actions/upload-artifact-7` |
| Created | 2026-04-28 16:37:48 UTC |
| State | Open |
| Mergeable | Yes |
| Changed files | `.github/workflows/ci.yml`, `.github/workflows/delivery.yml` |
| Diff | `v4` → `v7` (2 files, +2 -2) |

### 3.2 Version Jump Assessment

| Aspect | Detail |
|--------|--------|
| Old version | `upload-artifact@v4` |
| New version | `upload-artifact@v7` |
| Major versions skipped | 3 (v5, v6, v7) |
| Breaking changes | v7: ESM upgrade, direct file upload support |
| Compatibility score | Low — major version jump with ESM migration |

### 3.3 Release Notes Summary

- **v7.0.0**: Migrated to ESM. Added direct file upload support
  (single files, unzipped). `name` parameter ignored in direct mode.
  Multiple-file globs fail in direct mode.
- **v6.x**: Incremental improvements.
- **v5.x**: Incremental improvements.

### 3.4 Usage in This Repo

`upload-artifact@v4` is used in:
- `ci.yml`: repo-governance evidence artifact upload (retention: 30 days)
- `delivery.yml`: delivery bundle upload

The `name` parameter is explicitly set in both usages. If v7's direct
upload mode is enabled (default behavior may differ), the `name`
parameter could be silently ignored. This is a **high-risk** change
because artifact upload failures are silent — missing artifacts would
not fail CI but would break the evidence chain.

### 3.5 CI Status

| Check | Result |
|-------|--------|
| backend-static | ✅ success |
| verification-fast | ✅ success |
| secret-scan | ✅ success |
| CodeQL (python + js/ts) | ✅ success |
| repo-governance-pr | ✅ success |
| All 19 checks | ✅ success |

### 3.6 Repo Governance

- **Decision**: `execute` (governance passed)
- **Evidence artifact**: Present (`repo-governance-evidence`)
- **Side effects**: None reported

### 3.7 Risk Classification

| Risk | Level | Rationale |
|------|-------|-----------|
| Artifact pipeline | **High** | v7 ESM migration; silent `name` parameter change |
| Evidence chain | **High** | Missing artifacts = broken evidence chain, undetectable in CI green |
| Rollback complexity | Low | Revert to v4 is trivial (single line) |

### 3.8 Recommendation

**HOLD — requires manual artifact verification before merging.**

Before merge:
1. Merge PR #4 first (lower risk, validates merge flow)
2. Verify artifact upload behavior with v7 on a test push
3. Confirm `name` parameter is honored in non-direct mode
4. Verify `repo-governance-evidence` artifact is correctly uploaded
   after merge to main
5. If artifact upload breaks, revert immediately (single-line change)

**Risk mitigant**: If artifacts fail silently with v7, the evidence
chain is broken but CI remains green. A post-merge artifact check is
the minimum verification required.

## 4. PR #4: bump github/codeql-action from 3 to 4

### 4.1 PR Metadata

| Property | Value |
|----------|-------|
| PR | [#4](https://github.com/zycxfyh/AegisOS/pull/4) |
| Branch | `dependabot/github_actions/github/codeql-action-4` |
| Created | 2026-04-28 16:37:53 UTC |
| State | Open |
| Mergeable | Yes |
| Changed files | `.github/workflows/codeql.yml` |
| Diff | `@v3` → `@v4` (1 file, +2 -2) |

### 4.2 Version Jump Assessment

| Aspect | Detail |
|--------|--------|
| Old version | `codeql-action/init@v3` + `codeql-action/analyze@v3` |
| New version | `codeql-action/init@v4` + `codeql-action/analyze@v4` |
| Major version | v3 → v4 (1 major jump) |
| Breaking changes | v4: Python standard library extraction changes, OIDC validation fixes |

### 4.3 Release Notes Summary

- Standard library extraction removed for Python on GHES (not relevant
  — we use GitHub.com cloud runners)
- OIDC validation fix (not relevant — no private registry)
- Git 2.36.0 requirement for incremental analysis with submodules
  (not relevant — no submodules)
- TRAP cache cleanup feature deprecated (not relevant — not used)

### 4.4 CI Status

| Check | Result |
|-------|--------|
| CodeQL (python) | ✅ success |
| CodeQL (javascript-typescript) | ✅ success |
| backend-static | ✅ success |
| verification-fast | ✅ success |
| secret-scan | ✅ success |
| repo-governance-pr | ✅ success |
| All 19 checks | ✅ success |

### 4.5 Repo Governance

- **Decision**: `execute` (governance passed)
- **Evidence artifact**: Present (`repo-governance-evidence`)
- **Side effects**: None reported

### 4.6 Risk Classification

| Risk | Level | Rationale |
|------|-------|-----------|
| CodeQL workflow breakage | **Low** | CI already ran successfully with v4 |
| Alert baseline change | **Low** | Zero-alert baseline unchanged after v4 |
| Rollback complexity | Low | Revert to v3 is trivial (single line) |

### 4.7 Recommendation

**MERGE — low risk, CI-verified, no breaking change impact.**

The v3→v4 jump was already tested by the Dependabot PR's own CI
pipeline. CodeQL jobs ran successfully. Zero alerts maintained.
Breaking changes in v4 are not relevant to this repository's usage
pattern.

### 4.8 Recommended Merge Order

1. **Merge PR #4 first** (low risk, validates Dependabot merge flow)
2. **Hold PR #3** until artifact verification is confirmed
3. After PR #4 merged, verify main branch CI green
4. Then evaluate PR #3 with artifact verification

## 5. Dependabot Behavior Observations

| Observation | Finding |
|-------------|---------|
| Initial scan on config push | ✅ Yes — PRs created immediately |
| Weekly schedule adherence | ⏳ Pending (not yet reached) |
| PR limit (2) respected | ✅ Yes — exactly 2 PRs |
| Labels correctly applied | ✅ `dependencies`, `security/supply-chain` |
| Commit prefix `deps` | ✅ Correct |
| CI triggered on Dependabot PRs | ✅ Full CI pipeline |
| repo-governance-pr behavior | ✅ Passed (execute) for both |
| repo-governance artifact | ✅ Evidence artifacts present |
| No auto-merge attempted | ✅ Confirmed |
| No bypass of any gate | ✅ All gates executed |

## 6. Repo Governance Interaction

Both PRs passed `repo-governance-pr` with `execute` decision.
This means:

1. **Dependabot is recognized as a valid actor**: The governance
   adapter did not escalate or reject the PRs based on bot identity.
2. **Test Plan gap is handled**: Dependabot PRs have no explicit
   Test Plan, but governance adapter accepted the Dependabot PR body
   (release notes + compatibility score) as sufficient evidence.
3. **Evidence artifacts are generated**: Both PRs produced
   `repo-governance-evidence` artifacts, maintaining the evidence chain.

**Risk note**: For major version jumps with breaking changes (PR #3),
the governance adapter's `execute` decision may be too permissive.
Post-merge artifact verification is the compensating control.

## 7. Dependabot Config Tuning Recommendations

| Tuning | Rationale | Phase |
|--------|-----------|-------|
| No changes needed yet | First observation is positive | — |
| Consider `ignore` for risky packages | `upload-artifact` major jumps could be excluded | 4.7 |
| Consider `groups` for minor-only updates | Currently ungrouped (ecosystem default) | 4.7 |
| Keep `open-pull-requests-limit: 2` | Appropriate for current volume | — |

No config changes recommended in this phase.

## 8. Next Phase Recommendation

| Phase | Action | Rationale |
|-------|--------|-----------|
| **Now** | Merge PR #4 (codeql-action v3→v4) | Low risk, CI-verified |
| **Now** | Hold PR #3 (upload-artifact v4→v7) | Artifact verification needed |
| **4.7** | Observe main branch CI after PR #4 merge | Confirm no regression |
| **4.7** | Artifact verification for PR #3 | Validate v7 upload behavior |
| **4.8** | Enable pip + npm ecosystems | After github-actions baseline stable |

## 9. What This Observation Does NOT Do

- ❌ No PR merged
- ❌ No PR commented on
- ❌ No Dependabot config changed
- ❌ No dependency versions changed on main
- ❌ No source code changes
- ❌ No test changes
- ❌ No CI workflow changes
- ❌ No CandidateRule or PolicyProposal
- ❌ No auto-merge enabled
- ❌ No Dependabot PR bypass

## 10. Related Documents

| Document | Relationship |
|----------|-------------|
| `docs/runtime/dependabot-strategy.md` | Strategy doc, Phase 4.5 enablement |
| `docs/architecture/security-platform-baseline.md` | Security gate classification |
| `docs/adr/ADR-008-tooling-adoption-strategy.md` | Build/buy decision |
| `.github/dependabot.yml` | Active Dependabot configuration |
