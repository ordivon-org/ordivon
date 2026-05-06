# Agent-Native Evidence Round 1

Status: **CLOSED** | Date: 2026-05-06 | Phase: GWOS-2026-P4-R1
Tags: `agent-native`, `skills`, `memory`, `harness`, `mcp`, `read-only`
Authority: `supporting_evidence` | AI Read Priority: 2

## Purpose

This receipt closes the first implementation slice for
`docs/governance/agent-native-evidence-surfaces-2026.md`.

It turns the Phase 4 plan into a read-only, shadow-first checker and red-team
fixture ledger covering skills, memory/content, harness traces/checkpoints, and
MCP-like manifests.

This receipt is evidence only. It does not authorize merge, release,
deployment, publication, trading, policy activation, checker promotion, agent
execution, MCP server startup, token refresh, SDK compatibility, adapter
release, or external action.

## Implemented

- Added `checkers/agent-native-evidence/`.
- Added `docs/governance/agent-native-evidence-redteam.jsonl`.
- Added agent-native evidence fixtures under
  `tests/fixtures/agent_native_evidence/`.
- Added `tests/unit/governance/test_agent_native_evidence.py`.
- Registered the checker as `shadow_tested` in the checker maturity ledger.

## Red-Team Coverage

Round 1 covers:

- skill credential-seeking.
- skill capability/permission laundering.
- stale or cross-project memory cited as current truth.
- DEGRADED/BLOCKED signal rewritten as clean evidence.
- checkpoint/trace/receipt approval laundering.
- failed tool call omission.
- token passthrough.
- audience/resource confusion.
- tool availability treated as authorization.

## Boundary

The checker is escalation/full only and not in `pr-fast`. It is read-only. It
does not inspect real tokens, run agents, call tools, start servers, or contact
external systems.

## Verification At Closure

Observed at closure:

- `python checkers/agent-native-evidence/run.py`: PASS, 4 surfaces, 9 red-team
  cases.
- `uv run --with pytest python -m pytest tests/unit/governance/test_agent_native_evidence.py -q`:
  12 passed.
- `uv run python scripts/run_baseline.py --read-only`: READY, 26/26 hard gates
  passed, L10E escalation passed.
- `uv run python scripts/check_document_registry.py`: PASS, 228 registered
  docs, 0 completeness violations.
- `python scripts/check_artifact_registry.py`: PASS, 651 registered artifacts,
  0 ungoverned.
- `python checkers/current-truth/run.py`: PASS.

READY remains evidence sufficiency only. It is not action authorization.
