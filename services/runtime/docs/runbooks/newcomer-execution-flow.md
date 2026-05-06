# Newcomer Execution Flow

Status: **current** | Date: 2026-05-06
Authority: `current_status` | Phase: Newcomer-Friction-Reduction
Tags: `runbook`, `newcomer`, `verify`, `baseline`, `read-only`

## Purpose

This runbook gives new humans and AI collaborators one low-friction path through
Ordivon. It separates the read-only product trust audit from internal governance
baselines and from maintainer-only commands that intentionally update state.

`READY` is always an evidence signal. It never authorizes merge, deployment,
release, trading, policy activation, token refresh, or external action.

## First Read

Read these files before changing code or governance docs:

1. `README.md`
2. `AGENTS.md`
3. `docs/ai/current-phase-boundaries.md`
4. `docs/ai/agent-output-contract.md`
5. `docs/product/ordivon-2026-governance-execution-plan.md`

## Command Ladder

Use the lowest command that answers the question in front of you.

| Need | Command | Writes tracked state? | Use when |
|---|---|---:|---|
| Product trust audit | `uv run python scripts/ordivon_verify.py check .` | No | You need a newcomer-safe trust signal. |
| Product trust audit JSON | `uv run python scripts/ordivon_verify.py check . --json` | No | CI, scripts, or structured report checks. |
| Product trust audit Markdown | `uv run python scripts/ordivon_verify.py check . --markdown` | No | PR comments or human review handoff. |
| Internal read-only baseline | `uv run python scripts/run_baseline.py --read-only` | No | You need internal checker confidence without updating telemetry ledgers. |
| pr-fast hard gates | `uv run python scripts/run_baseline.py --pr-fast` | No | You need the canonical fast hard-gate seal. |
| Full maintainer baseline | `uv run python scripts/run_baseline.py` | Yes | A maintainer intentionally wants telemetry/shadow ledgers refreshed. |

Do not use the full maintainer baseline as a casual newcomer command. It is
valid, but it can update tracked governance state by design.

## Standard Work Flow

Before work:

```bash
uv run python scripts/ordivon_verify.py check .
uv run python scripts/run_baseline.py --read-only
```

During work:

- Run the narrowest relevant unit tests.
- If you add or move files, expect artifact registry checks to matter.
- If you add or edit governance docs, expect document registry and current-truth
  checks to matter.
- If you touch trust reports, receipts, or agent-native evidence, run Alpha or
  agent-native focused tests.

Before handoff:

```bash
uv run python scripts/ordivon_verify.py check .
uv run python scripts/run_baseline.py --read-only
uv run python scripts/check_document_registry.py
python scripts/check_artifact_registry.py
python checkers/current-truth/run.py
git diff --check
```

Add focused tests for the surface you changed. Examples:

```bash
uv run python scripts/run_alpha_casebook.py
uv run --with pytest python -m pytest tests/unit/product/test_ordivon_verify_*.py -q
uv run --with pytest python -m pytest tests/unit/governance/test_egb2_*.py -q
uv run --with pytest python -m pytest tests/unit/governance/test_pgi_*.py -q
```

## External Repo Check

For an external project with `ordivon.verify.json`:

```bash
uv run python scripts/ordivon_verify.py check /path/to/repo --config /path/to/repo/ordivon.verify.json
```

This is still read-only. `DEGRADED` is acceptable when governance files are
intentionally missing, but the report must preserve `missing_evidence`.

## Interpretation Rules

- `READY`: selected evidence checks passed; no action authorization.
- `DEGRADED`: no hard failure, but evidence is incomplete or review is needed.
- `BLOCKED`: hard inconsistency or missing required evidence.
- `NOT_APPLICABLE`: surface did not apply to the selected checker path.

Never convert `DEGRADED` into "good enough" without recording the missing
evidence and review boundary.

## State-Updating Commands

These commands are allowed only when the task explicitly asks for state refresh
or maintainer closure:

```bash
uv run python scripts/run_baseline.py
python checkers/current-truth/run.py --auto-fix
python scripts/run_stage.py <template> --execute
```

If any command writes governance ledgers, include the changed files in the
receipt. State refresh is evidence work, not authorization.
