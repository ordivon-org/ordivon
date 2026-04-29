# Task Prompt Template

Status: **DOCUMENTED** (Phase 6R)
Date: 2026-04-29
Phase: 6R
Tags: `prompt`, `template`, `compressed`, `task`, `ai-onboarding`

## 1. Purpose

This template is the canonical compressed prompt format for Ordivon tasks.
It replaces 3000-word ultra-detailed prompts with a structured 300-word
phase header. The agent loads the full doctrine from `docs/ai/` and this
prompt provides only what is specific to the current phase.

## 2. Template

```markdown
Read first:
docs/ai/ordivon-root-context.md
docs/ai/architecture-file-map.md
docs/ai/current-phase-boundaries.md
docs/ai/agent-working-rules.md
[any phase-specific docs]

Current phase:
Phase X.Y — Name

Stage identity:
[What this phase is. 1–2 sentences. How it fits in the roadmap.]

Goal:
[The single problem being solved. 2–4 specific deliverables.]

Allowed:
- [Specific change 1]
- [Specific change 2]

Forbidden:
- [Hard boundary 1]
- [Hard boundary 2]

Required content:
[List of specific UI elements, models, tests, or behaviors expected]

Verification:
[Standard seal commands — customize only if needed]
pnpm test
pnpm build
uv run python scripts/run_verification_baseline.py --profile pr-fast
[etc.]

Receipt:
[Receipt format — use standard, customize only if needed]

Commit:
[type]: [description]

Tag:
[phase tag]
```

## 3. Example: Compressed vs Ultra-Detailed

### Before (Ultra-Detailed — DO NOT USE)

```
Phase 4.11 — Dependabot Bot Governance Adapter Patch

Goal: Harden the Dependabot detection in scripts/repo_governance_github_adapter.py.

Steps:
1. Open scripts/repo_governance_github_adapter.py
2. Find the function _is_dependabot_pr() at line 88
3. Remove the check for "deps:" in pr.title
4. Remove the check for "bump " in pr.title
5. Keep only pr.user.login == "dependabot[bot]"
6. Keep event.sender.login == "dependabot[bot]" as secondary check
7. Update the docstring to explain why title is untrusted
8. Open tests/unit/test_repo_governance_github_adapter.py
9. Add test: human deps title should NOT be detected as Dependabot
10. Add test: Dependabot user.login should be detected
11. Add test: unknown user with deps title should NOT be detected
12. Run pytest tests/unit/test_repo_governance_github_adapter.py
13. Run full verification baseline
14. Commit with message "fix: harden Dependabot PR identity detection"
... [continues for 40 more lines]
```

### After (Compressed)

```
Phase 4.11-P — Bot Governance Adapter Identity Hardening

Stage identity: Harden Dependabot detection by removing title-pattern signals.
Only pr.user.login and event.sender.login are trusted for actor identity.

Goal: Remove all title-based detection from _is_dependabot_pr().
Add tests for human-title bypass. See doctrine §3.3, §4.2.

Boundaries: Only modify adapter + tests. No CI, no Dependabot config, no PR merge.

Verification: pytest + full seal. Receipt standard.
```

## 4. What NOT to Include in the Prompt

- File paths the agent can discover by reading the repo
- Line numbers (stale within hours)
- Step-by-step instructions (the agent can infer from context)
- Full governance doctrine (deferred to root-context)
- Actor trust model (deferred to root-context)
- Evidence freshness rules (deferred to root-context)
- Self-check instructions (deferred to agent-working-rules)

## 5. Phase Metadata Pattern

Every phase document (prompt, seal, receipt) should carry:

```markdown
Phase: X.Y
Status: [PLANNED | IN_PROGRESS | COMPLETE | SEALED]
Date: YYYY-MM-DD
Tags: `phase-x-y`, `[domain]`, `[action]`
```

## 6. Receipt Template

```markdown
## Phase X.Y — Receipt

### Files Changed
| File | Lines | Purpose |
|------|-------|---------|

### Confirmed Boundaries
- [ ] No backend changes (or: justified)
- [ ] No policy activation
- [ ] No auto-merge
- [ ] No broker write / live order
- [ ] CandidateRule ≠ Policy labeled where applicable
- [ ] Advisory boundaries labeled where applicable
- [ ] High-risk actions disabled with reasons

### Verification
| Gate | Result |
|------|--------|
| Frontend tests | X/Y PASS |
| Backend tests | X/Y PASS |
| Build | PASS/FAIL |
| Architecture | ✅/❌ |
| Evidence integrity | ✅/❌ |
| Eval corpus | 24/24 PASS |
| Baseline | X/Y gates READY |

### Git
```
[git diff --stat]
```

### Commit
```
[commit hash] [message]
```

### Tag
```
[phase tag]
```
