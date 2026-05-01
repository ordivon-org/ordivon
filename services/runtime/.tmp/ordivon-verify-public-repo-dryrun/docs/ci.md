# Ordivon Verify — CI Example

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-5
Tags: `product`, `verify`, `ci`, `github-actions`, `example`
Authority: `proposal` | AI Read Priority: 3

## Purpose

This document provides example CI integration for Ordivon Verify. These examples are **not active workflows** — they are reference configurations for teams adopting Ordivon Verify in their CI pipeline.

CI running Ordivon Verify checks AI/agent work before merge. It verifies that agent completion claims are consistent with evidence — not that the code itself is correct (that's what tests do).

## Example GitHub Actions Workflow

This is an **example only**. Copy it to your repo and customize.

```yaml
# .github/workflows/ordivon-verify.yml
# Example only — customize for your repo before activating.

name: Ordivon Verify

on:
  pull_request:
    paths:
      - "docs/runtime/**"
      - "docs/product/**"
      - "docs/governance/**"
      - "docs/ai/**"
      - "ordivon.verify.json"

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Run Ordivon Verify
        id: verify
        run: |
          uv run python scripts/ordivon_verify.py all --json > verify-report.json
        continue-on-error: true

      - name: Check exit code
        id: check
        run: |
          STATUS=$(python -c "import json; print(json.load(open('verify-report.json'))['status'])")
          echo "status=$STATUS" >> $GITHUB_OUTPUT
          if [ "$STATUS" = "BLOCKED" ]; then
            echo "BLOCKED — see report below"
            exit 1
          elif [ "$STATUS" = "DEGRADED" ]; then
            echo "DEGRADED — human review required"
            exit 0
          fi

      - name: Post Verify report as PR comment
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('verify-report.json', 'utf8'));
            let body = '## Ordivon Verify Report\n\n';
            body += `**Status**: ${report.status}\n`;
            body += `**Mode**: ${report.mode}\n\n`;
            body += '| Check | Status |\n|-------|--------|\n';
            for (const c of report.checks) {
              const icon = c.status === 'PASS' ? '✅' : c.status === 'WARN' ? '⚠️' : '❌';
              body += `| ${c.id} | ${icon} ${c.status} |\n`;
            }
            if (report.hard_failures.length > 0) {
              body += '\n### Hard Failures\n';
              for (const f of report.hard_failures) {
                body += `- **${f.file || f.id}**: ${f.reason}\n`;
              }
            }
            if (report.warnings.length > 0) {
              body += '\n### Warnings\n';
              for (const w of report.warnings) {
                body += `- ${w.reason}\n`;
              }
            }
            body += `\n> ${report.disclaimer}`;
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body
            });
```

## Exit Code Interpretation

| Exit Code | Status | CI Behavior |
|-----------|--------|-----------|
| 0 | READY | Pass. Do not auto-merge. |
| 1 | BLOCKED | Fail. Block merge. |
| 2 | DEGRADED / NEEDS_REVIEW | Warning. Require human review. |
| 3 | Config error | Fail. Fix configuration. |
| 4 | Runtime error | Fail. Investigate tool issue. |

## PR Policy

| Verify Result | Merge Policy |
|--------------|-------------|
| READY | Allowed, but not auto-merged. Human reviewer still responsible. |
| BLOCKED | **Blocked.** Hard failures must be resolved. |
| DEGRADED | Allowed only with human review approval. |
| Error (3-4) | Blocked. Tool or config issue. |

## Verify Result Is Evidence, Not Authorization

Ordivon Verify reports consistency between claims and evidence. It does not:

- Approve code changes
- Authorize deployment
- Replace code review
- Validate business logic
- Guarantee correctness

The human reviewer makes the decision. Verify provides evidence.
