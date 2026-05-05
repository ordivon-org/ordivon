---
gate_id: dependabot_governance
display_name: Dependabot Governance
layer: L5F
hardness: hard
purpose: Classify Dependabot PRs through CodingDisciplinePolicy gates + shadow evaluation logic — auto-governed dependency updates
protects_against: "Unreviewed dependency merges, CI-broken auto-merges, protected path changes via deps, runtime dependency escalation gaps"
profiles: ['full']
timeout: 30
tags: [coding, governance, dependabot, ci, auto-merge]
---

# Dependabot Governance Checker

## Purpose

The first governance checker that makes operational decisions on real CI data.
Classifies Dependabot PRs through the Coding Pack's discipline policy gates
plus Dependabot-specific shadow evaluation logic:

- **Lockfile-only + CI green → execute** (safe to auto-merge)
- **Runtime dependency + CI red → escalate** (human review required)
- **Protected path touched → reject** (never auto-merge)
- **CI failure → hold** (investigate before merge)

## Input

Accepts a JSON payload describing the PR context:
```json
{
  "actor": "dependabot",
  "changed_files": ["uv.lock", "pyproject.toml"],
  "ci_status": "pass",
  "is_runtime_dep": false,
  "pr_title": "bump requests from 2.31.0 to 2.32.0"
}
```

## Output

A governance decision with receipt:
- `decision`: execute | escalate | reject
- `reasons`: list of classification reasons
- `receipt`: structured evidence record
