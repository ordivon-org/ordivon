# Ordivon Agent Operating Doctrine

Status: **DOCUMENTED** (Phase 4D)
Date: 2026-04-29
Phase: 4D
Tags: `doctrine`, `agent`, `governance`, `evidence`, `trust`, `prompt-compression`, `self-check`

## 1. Purpose

This document is the long-term operating doctrine for any IDE agent, AI
assistant, or automated system working within the Ordivon project. It
replaces the need for ultra-detailed step-by-step prompts by encoding
the governance philosophy, evidence principles, actor trust model,
adapter boundaries, and policy lifecycle into a reusable reference.

An agent should read this doctrine before executing any Ordivon task.
When in doubt, the agent should run the self-check in §8 before
producing a final receipt.

## 2. Why Step-by-Step Prompting Is Not Enough

Ultra-detailed prompts decompose tasks into rote instructions. This works
for simple operations but fails when:

- **Evidence becomes stale**: A prompt written yesterday may assume check
  results that have since changed. The agent must re-verify, not re-execute
  blind instructions.

- **Actor identity matters**: A "deps:" title does not prove Dependabot
  authorship. The agent must check trusted metadata, not text patterns.

- **Governance adapters evolve**: A prompt may reference a policy that has
  been patched. The agent must check the current adapter behavior, not
  cached assumptions.

- **Context exhausts**: A 3,000-word prompt is not a sustainable interface.
  A 300-word phase header + this doctrine should suffice for most tasks.

The doctrine is designed to be **loaded before task execution** rather
than **embedded inside every prompt**. A compressed phase prompt
(§7) references the doctrine by name and states only what is specific
to that phase.

## 3. Core Doctrine

These are the non-negotiable operating rules. An agent that violates any
of them must report the violation and cannot claim task completion.

### 3.1 Evidence Before Belief

Never assume. Always check. If a CI run is claimed to have passed, verify
the actual check-runs API response. If a test is claimed to cover a path,
read the test file. If a document claims a status, check the git log to
confirm when that status was set.

**Rule**: Before asserting any fact about the project state, the agent
must have recent evidence from a verifiable source (API response, file
read, git log, subprocess output).

**Violation**: "The CI passed" based on what the prompt said, without a
fresh API call.

### 3.2 Fresh Evidence Beats Stale Evidence

Evidence has a freshness property. A check run that completed 3 hours ago
on a pre-patch PR branch is **stale** if the main branch has since been
updated with a relevant fix.

| Freshness | Meaning | Action |
|-----------|---------|--------|
| Current | Evidence from the latest relevant state | Trust |
| Stale | Evidence from a state before a known relevant change | Re-verify or downgrade confidence |
| Regenerated | Stale evidence that has been re-acquired | Trust, with timestamp |
| Human Exception | Evidence from human judgment | Record in receipt, do not override |

**Rule**: When presenting evidence, always note its timestamp and the
state (branch/commit) from which it was obtained. If a known state change
occurred after the evidence was collected, the evidence is stale.

**Example from Phase 4.11**: Dependabot PR #5 had a `repo-governance-pr:
failure` check result. This was **stale** because the identity hardening
patch had been merged to main after the PR branch was created. The stale
failure did not indicate a current problem — it indicated that the PR
branch's adapter code was obsolete. The correct action was to note the
staleness, verify the fix on main, and proceed with the analysis — not
to re-trigger the check and treat the re-run failure as new evidence.

### 3.3 Actor Identity Must Come from Trusted Metadata

When a PR is created, its title, body, labels, and branch name are **user-
supplied text**. They can be set by anyone. They are not identity.

| Source | Trust Level | Use |
|--------|-------------|-----|
| `pr.user.login` | Trusted | Primary identity |
| `event.sender.login` | Trusted | Secondary identity |
| `pr.title` | Untrusted | Content only, never identity |
| `pr.body` | Untrusted | Content only, never identity |
| `pr.labels` | Untrusted | Hints only, never identity |
| Branch name | Untrusted | Content only, never identity |

**Rule**: Never use title, body, labels, or branch name to determine
whether a PR comes from a trusted bot actor. Only GitHub actor metadata
(user.login, sender.login) is trusted for identity.

**Violation**: Treating a PR with title "deps: bump react" as a Dependabot
PR when the PR author is `human-maintainer`.

**Example from Phase 4.11 Patch**: The original `_is_dependabot_pr()`
used title patterns (`deps:`, `bump `) as a detection signal. This was
insecure — any human could write a "deps:" title. The patch removed all
title-based detection, keeping only `pr.user.login` and `event.sender.login`.

### 3.4 Adapter Output Is Evidence, Not Truth

The Repo Governance adapter, the RiskEngine, the CodingDisciplinePolicy —
these produce **classifications**. Classifications are evidence, not
ground truth. A `reject` decision means the policy engine rejected the
intake under its current rules. It does not mean the PR is objectively
dangerous.

**Rule**: Adapter output should be recorded and respected, but always
with awareness that:
- The adapter may have bugs
- The policy may be misconfigured
- The adapter may be running stale code
- The decision is a classification, not a fact about the code

**Example**: When `repo-governance-pr` failed on all Dependabot PRs,
the correct response was not "Dependabot PRs are dangerous." It was
"The adapter does not handle bot PRs correctly. Fix the adapter."

### 3.5 External Actor Handling Is Not Bypass

When an external actor (Dependabot, CodeQL, Gitleaks) produces output:
- The output is **evidence**
- The output does **not** automatically trigger governance decisions
- The output must flow through the same governance classification path
- If the classification path doesn't handle the actor correctly, fix
  the adapter — don't bypass governance

**Rule**: External actors get **adapted governance**, not **bypassed
governance**. The adapter can inject synthetic fields (like a test_plan
for Dependabot PRs), but it cannot skip the RiskEngine entirely.

**Violation**: Adding `if is_dependabot: return "execute"` at the top
of the adapter, skipping all checks. The correct approach is to inject
a synthetic test_plan and still run forbidden-file checks.

### 3.6 CandidateRule Is Not Policy

A CandidateRule is an **advisory observation**:
- It identifies a pattern
- It runs in dry-run mode
- It collects data
- It does NOT block CI or reject PRs

A Policy is a **blocking rule**:
- It has been observed over ≥2 weeks
- It has caught ≥3 real problems
- It has documented bypass conditions
- It has stakeholder sign-off

**Rule**: Never promote a CandidateRule to Policy without meeting all
four criteria. Never write a new blocking check as Policy directly —
start as CandidateRule.

### 3.7 Governance Must Reduce Net Risk, Not Maximize Process

The purpose of governance is to **reduce the probability of bad outcomes**,
not to **maximize the number of checks performed**. A check that fires on
every PR and is always ignored is worse than no check — it trains
developers to ignore governance.

**Rule**: Before adding any governance gate, ask:
- What specific risk does this gate prevent?
- What is the false positive rate?
- Who will act on the escalation?
- If the answer to any of these is unclear, start as CandidateRule
  (advisory, no block).

### 3.8 No Human Exception Without Receipt

If a human reviewer overrides a governance decision (merges a PR that
governance rejected, skips a required check, bypasses a policy), the
override must be recorded:

- Why the override was granted
- Who granted it
- When
- What evidence was considered
- What risk was accepted

**Rule**: Human exception is legitimate but must leave a trace. An
unexplained override is a governance violation.

**Violation**: Merging PR #7 (react) without documenting the frontend
compatibility analysis and the accepted risk.

## 4. Actor Trust Model

Every PR, commit, or workflow trigger has an **actor**. The actor's
identity determines what governance treatment applies.

### 4.1 Human PR

| Property | Value |
|----------|-------|
| Identity | Verified by `pr.user.login` |
| Test Plan | Required. Missing → escalate |
| Forbidden Files | Reject (.env, uv.lock, pyproject.toml, etc.) |
| Governance Path | Full RiskEngine → CodingDisciplinePolicy |
| Auto-merge | Never |

### 4.2 Dependabot PR

| Property | Value |
|----------|-------|
| Identity | Verified by `pr.user.login == "dependabot[bot]"` |
| Test Plan | Synthetic (injected by adapter) |
| Expected Files | pyproject.toml, uv.lock, package.json, pnpm-lock.yaml |
| Forbidden Files | Still rejected (.env, source code outside expected set) |
| Governance Path | Adapted — synthetic test_plan + file filtering |
| Auto-merge | Never |

### 4.3 Future AI Agent PR

| Property | Value |
|----------|-------|
| Identity | Must be verified by trusted metadata (not title/body) |
| Test Plan | Required. May be synthetic if agent provides changelog |
| Forbidden Files | Full enforcement |
| Governance Path | Full RiskEngine — no special treatment unless adapter extended |
| Auto-merge | Never (requires 3+ months of clean history first) |

### 4.4 GitHub Workflow (push, schedule)

| Property | Value |
|----------|-------|
| Identity | `github-actions[bot]` |
| Governance | No intake needed — internal CI actor |
| Evidence | Check run results, workflow logs |

### 4.5 External Security Tools (CodeQL, Gitleaks, Bandit)

| Property | Value |
|----------|-------|
| Identity | Tool-specific |
| Output | Evidence — SARIF, logs, alerts |
| Governance | Does not auto-block. Findings inform human triage |
| Policy | CandidateRule until proven over ≥2 weeks |

## 5. Evidence Freshness Rules

Evidence has a lifecycle. The agent must track freshness and not present
stale evidence as current.

### 5.1 Current Evidence

Evidence obtained from the latest state of the system:
- A check run from the current commit on the relevant branch
- A file read from the current working tree
- An API response from the last 60 seconds

**Action**: Trust. Present with timestamp.

### 5.2 Stale Evidence

Evidence from a state before a known relevant change:
- A check run from a PR branch that predates a main-branch fix
- A file read from a commit that has since been superseded
- An API response from >10 minutes ago during active development

**Action**: Do not present as current. If used, explicitly mark as stale
and explain why it's still relevant. Prefer to re-verify.

### 5.3 Regenerated Evidence

Stale evidence that has been re-acquired:
- A check run that was re-triggered and completed
- A file that was re-read after a known change

**Action**: Trust. Present with new timestamp.

### 5.4 Human Exception Evidence

Evidence from human judgment:
- "I reviewed the changelog and it looks safe"
- "The frontend build failure is known and acceptable"

**Action**: Record in receipt. Do not override. Do not treat as automated
verification. A human exception is valid but must be traceable (§3.8).

## 6. Prompt Compression Rules

A compressed phase prompt should contain only what is **specific to this
phase**. Everything else should be in the doctrine.

### 6.1 Required Elements

Every phase prompt must state:

1. **Stage identity**: What phase this is and what it's called
2. **Purpose**: The single problem being solved
3. **Boundaries**: Allow-list (what can change) and deny-list (hard stops)
4. **Verification**: What seal checks to run
5. **Receipt format**: What the final output must contain

### 6.2 Elements Deferred to Doctrine

The following should NOT be repeated in every prompt:

- The full governance philosophy
- The actor trust model
- Evidence freshness rules
- The CandidateRule → Policy lifecycle
- The adapter boundary rules
- The agent self-check

Instead, the prompt says: "Agent should self-check per Ordivon Agent
Operating Doctrine §8 before producing receipt."

### 6.3 Implementation Inference

The compressed prompt states **what to achieve**, not **how to implement**.
The agent infers implementation details from:
- The project structure (read files before writing)
- The existing code patterns (match the style)
- The governance rules (don't bypass RiskEngine)
- The evidence rules (verify, don't assume)

**Example — before compression**:
```
Modify scripts/repo_governance_github_adapter.py:
1. Add function _is_dependabot_pr() at line 88
2. Check pr.user.login for "dependabot"
3. Check event.sender.login for "dependabot"
4. Do not check title
5. Return True if found
... [50 more lines]
```

**Example — after compression**:
```
Harden Dependabot PR identity: remove title-only signals from
_is_dependabot_pr(). Only trust pr.user.login and event.sender.login.
Update tests. Run full seal. See doctrine §3.3, §4.2.
```

## 7. Examples

These examples are drawn from actual Ordivon phases (4.5–4.11). They
illustrate the doctrine in practice.

### 7.1 Stale repo-governance Failure After Adapter Patch

**Situation**: Phase 4.11 deployed an identity hardening patch to main.
Dependabot PRs #5, #6, #8 still showed `repo-governance-pr: failure`.

**Agent action**: The agent attempted to re-trigger the checks. The
re-runs still failed because the PR branches had stale adapter code.

**Doctrine applied**:
- The failure was **stale evidence** (§3.2): the PR branches predated
  the fix.
- All **substantive CI was current and green**: the real tests passed.
- The agent correctly identified the staleness and did not treat the
  re-run failure as a new problem.
- Merge recommendation was based on current substantive evidence, with
  the stale go-pr failure explicitly noted.

**Lesson**: When a governance check fails but all substantive CI passes
and the governance adapter was recently patched, check whether the
failure is stale before blocking merge.

### 7.2 Dependabot Title Cannot Prove Identity

**Situation**: A PR with title "deps: bump react" was created by a human
maintainer. The original adapter treated it as Dependabot and injected
a synthetic test_plan.

**Doctrine applied**:
- Title is **untrusted metadata** (§3.3). Any human can write "deps:".
- The adapter was patched to only trust `pr.user.login`.
- After the patch, a human "deps:" PR correctly escalates (no synthetic
  test_plan).

**Lesson**: Never use user-supplied text fields for identity. Only
GitHub actor metadata is trusted.

### 7.3 CodeQL Finding Is Evidence, Not Policy

**Situation**: CodeQL reported a security alert on a PR. The CI workflow
uploaded a SARIF file.

**Doctrine applied**:
- The finding is **evidence** (§3.4, §4.5). It is not an automatic block.
- CodeQL workflow health is a hard gate (init/analyze/upload must succeed).
- CodeQL finding severity is advisory — requires human triage.
- The finding does not bypass governance. It informs the governance
  classification.

**Lesson**: Security scanners produce evidence. Governance produces
decisions. Don't confuse the two layers.

### 7.4 Artifact Exists but Is Not ExecutionReceipt

**Situation**: repo-governance-pr produced a JSON output file. An agent
treated this as an ExecutionReceipt.

**Doctrine applied**:
- The JSON output is an **adapter artifact** (§3.4). It is evidence of
  the classification, not an ExecutionReceipt in the Ordivon evidence
  platform.
- An ExecutionReceipt requires an ExecutionRequest, a DB write, and a
  traceable ID. The adapter does none of these.
- The artifact is useful but its scope is limited to CI evidence.

**Lesson**: Don't confuse CI artifacts with platform evidence records.
They serve different purposes and have different trust levels.

## 8. Agent Self-Check Before Final Receipt

Before producing a final receipt for any Ordivon task, the agent must
answer these six questions truthfully:

### 1. Did I rely on stale evidence?

- Did I cite a check result from before a known fix was deployed?
- Did I assume a file's content without re-reading it?
- Did I trust a CI status from >10 minutes ago during active work?

**If yes**: Re-acquire the evidence or mark it as stale in the receipt.

### 2. Did I trust untrusted text?

- Did I use a PR title, body, label, or branch name to determine identity?
- Did I assume a file path from a prompt without verifying it exists?
- Did I treat a human-authored description as ground truth?

**If yes**: Replace with trusted metadata or verified observation.

### 3. Did I bypass governance?

- Did I skip a RiskEngine check because "it's just a small change"?
- Did I merge or recommend merging without repo-governance-pr passing?
- Did I treat a Dependabot PR differently without adapter-level justification?

**If yes**: The receipt is invalid. Re-run with correct governance path.

### 4. Did I confuse evidence with truth?

- Did I treat a policy engine's "reject" as proof of danger?
- Did I treat a scanner's finding as an automatic block?
- Did I treat an adapter artifact as an ExecutionReceipt?

**If yes**: Re-frame as evidence + classification, not objective truth.

### 5. Did I create policy from experience?

- Did I add a blocking check because "this seems like a good idea"?
- Did I promote a pattern to Policy without 2+ weeks of observation?
- Did I skip the CandidateRule phase?

**If yes**: Revert to CandidateRule (advisory) and document the pattern.

### 6. Did I over-split the work?

- Did I break one logical change into 5 phases for process reasons?
- Did I create a new phase for something that could have been a patch?
- Did I require a separate receipt for a single-line fix?

**If yes**: Collapse into fewer phases. The doctrine exists to reduce
phase count, not increase it.

---

If the answer to all six questions is **no**, the receipt is valid.
If any answer is **yes**, the receipt must explain the exception.
