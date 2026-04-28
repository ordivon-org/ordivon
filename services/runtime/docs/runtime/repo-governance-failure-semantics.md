# Repo Governance Failure Semantics

Status: **DOCUMENTED**
Date: 2026-04-28
Phase: 3.10
Tags: `repo-governance`, `failure`, `ci`, `semantics`, `evidence`

## 1. Purpose

Define the exact CI behavior for each Repo Governance decision outcome.
Document what each decision means for PR workflow, who needs to act, and
what evidence is produced. This document is the definitive reference for
`repo-governance-pr` job semantics.

## 2. Decision → CI Behavior Table

| Decision | Adapter Exit Code | CI Exit Code | CI Behavior | Artifact | Evidence |
|----------|-------------------|-------------|-------------|----------|----------|
| `execute` | 0 | 0 | ✅ **PASS** | Uploaded | Classified safe |
| `escalate` | 2 | 0 (after warning) | ⚠️ **WARNING** | Uploaded | Human review required |
| `reject` | 3 | 3 | ❌ **FAIL** | Uploaded | Blocked |
| internal error | 1 | 1 | ❌ **FAIL** | May not upload | Adapter failure |

## 3. Execute Semantics

**When**: All governance gates pass.

**Meaning**: The proposed code change does not trigger any rejection or
escalation conditions. The task description is present, file paths are
valid, no forbidden files are touched, a test plan is provided, and the
estimated impact is not high.

**CI behavior**: Job passes (exit 0). No warning emitted.

**Developer action**: None required. The PR can proceed through normal
CI checks (unit tests, integration tests, etc.).

**Evidence**: Governance decision recorded in:
- Workflow log (stdout JSON)
- `repo-governance-report.json` (artifact)
- `repo-governance-report.md` (artifact)

**Example**:
```
✅ Governance: execute — safe to proceed
Decision: execute
Reasons: ["Passed all governance gates."]
```

## 4. Escalate Semantics

**When**: The intake requires human review. Triggers include:
- `estimated_impact='high'`
- Missing `test_plan`
- (Future) changed files exceeding threshold for new contributors

**Meaning**: The change has elevated risk or incomplete information. A
human reviewer should evaluate whether the change is acceptable before
merge. The governance system cannot autonomously approve.

**CI behavior**: Job emits a `::warning::` annotation and passes (exit 0).
The PR can proceed to other CI checks, but the warning is visible in the
PR checks tab and workflow summary.

**Developer action**: A human reviewer must examine the governance reasons
and either:
1. Confirm the change is acceptable and merge
2. Request additional information (test plan, justification)
3. Reject the PR if the change is unsafe

**Why warning, not fail?** Phase 3.6-3.9 is the first CI integration.
Making escalate a hard CI failure would block all high-impact and missing-test-plan
PRs immediately, creating excessive friction. As the governance system matures,
escalate can be promoted to a hard gate (Phase 4.x).

**Evidence**: Governance decision + escalate reasons recorded in:
- Workflow log (stdout JSON + `::warning::` annotation)
- `repo-governance-report.json` (artifact)
- `repo-governance-report.md` (artifact)

**Example**:
```
⚠️  Governance: escalate — human review recommended
::warning::Repo governance: escalate — human review required
Decision: escalate
Reasons: ["estimated_impact='high' — requires human review before code changes."]
```

## 5. Reject Semantics

**When**: The intake is blocked. Triggers include:
- Forbidden file paths: `.env`, `uv.lock`, `pyproject.toml`, `state/db/migrations/runner.py`, `secrets`, `private_key`
- Missing required fields: `task_description`, `file_paths`

**Meaning**: The change touches files or lacks information that governance
rules classify as unacceptable. The PR must not be merged in its current form.

**CI behavior**: Job **fails** (exit 3). The PR is blocked. Other CI jobs
may still run, but the `repo-governance-pr` failure is visible.

**Developer action**: The developer must:
1. Read the rejection reasons
2. Fix the issue (e.g., remove forbidden files from the PR, add missing fields)
3. Push a new commit
4. The governance check re-runs automatically

**Why block?** Forbidden file paths represent real security and stability
risks (secrets exposure, lockfile conflicts, migration runner manipulation).
Reject is intentionally a hard gate from the first CI integration.

**Evidence**: Governance decision + rejection reasons recorded in:
- Workflow log (stdout JSON)
- `repo-governance-report.json` (artifact)
- `repo-governance-report.md` (artifact)
- GitHub Actions failure annotation

**Example**:
```
❌ Governance: reject — blocked
Decision: reject
Reasons: ["Forbidden file path: '.env' matches protected pattern '.env'."]
```

## 6. Internal Error Semantics

**When**: The adapter or report renderer encounters an unexpected error.

**Meaning**: The governance system itself failed. This is not a governance
decision — it's a system error.

**CI behavior**: Job **fails** (exit 1). The PR is blocked pending investigation.

**Developer action**: The developer should:
1. Check the workflow log for error details
2. Report the issue if it persists
3. Wait for a fix or workaround

**Evidence**: Error message in workflow log. Artifacts may not be generated.

## 7. Artifact Semantics

**When**: Every repo-governance-pr run (always, via `if: always()`).

**Artifact name**: `repo-governance-evidence`

**Contents**:
```
repo-governance-report.json  — machine-readable evidence
repo-governance-report.md    — human-readable evidence
```

**Retention**: 30 days (configurable per project policy).

**Purpose**: Each PR has an auditable governance decision record. Even if
the PR is closed or the workflow log expires, the artifact preserves the
governance evidence.

**Not a Receipt**: The artifact is evidence, not an ExecutionReceipt.
It does not imply execution happened. It does not write to any database.

## 8. Known GitHub Runner Constraints

| Constraint | Impact | Mitigation |
|-----------|--------|-----------|
| `pull_request` event payload | PR title, body, labels available; base/head sha available | Used for changed file diff |
| Shallow checkout | `git diff base..head` needs full history | `fetch-depth: 0` in checkout step |
| Fork PR permissions | `pull-requests: read` may be restricted | Read-only permissions minimize risk |
| Artifact upload on failure | `if: always()` ensures artifact generation even on reject | Artifact always available for audit |
| `::warning::` annotation | Visible in PR checks tab, not in PR timeline | Escalation is visible without commenting |
| Path characters in artifact | Colons/special chars in filenames rejected | Simple filenames: `repo-governance-report.*` |

## 9. Why PR Comments Are Not Enabled Yet

PR comments require `pull-requests: write` permission and a GitHub token.
Enabling PR comments would:

1. Break the read-only invariant (adapter output becomes active PR content)
2. Require write permissions (scope creep)
3. Create governance content in PR timeline (harder to audit as evidence)

PR comments are a future capability (Phase 4.x). Before enabling:
- The governance system must have a proven track record of correct classification
- The evidence artifact system must be stable
- The escalation path must have clear human review workflows

The current `::warning::` annotation + artifact upload provides sufficient
visibility without write permissions.

## 10. Future Path to Checks API

The GitHub Checks API provides richer failure reporting than exit codes:
- Per-file annotations
- Summary with markdown
- Actionable suggestions

Future phases (4.x) may integrate Checks API for:
- **Reject**: annotation on forbidden file paths with specific reasons
- **Escalate**: summary with review checklist
- **Execute**: green check with governance score

This requires `checks: write` permission and is deferred until the
basic CI integration is validated.

## 11. Related Documents

| Document | Relationship |
|----------|-------------|
| `docs/runtime/verification-ci-gate-plan.md` | Defines which gates run when |
| `docs/runtime/repo-governance-cli.md` | CLI usage and semantics |
| `tests/contracts/repo_governance_output.schema.json` | JSON output contract |
| `docs/architecture/verification-platform.md` | Gate classification system |
| `docs/architecture/ordivon-platform-map.md` | Adapter Platform position |
