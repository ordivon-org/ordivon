# Agent-Native Evidence Import Report Round 1

Status: **CLOSED** | Date: 2026-05-06 | Phase: GWOS-2026-P4-F
Tags: `agent-native`, `import-report`, `skills`, `memory`, `harness`, `mcp`
Authority: `supporting_evidence` | AI Read Priority: 2

## Purpose

This report closes the Phase 4F import-report slice for
`docs/governance/agent-native-evidence-surfaces-2026.md`.

The goal is to make the four agent-native evidence surfaces readable as one
import boundary:

```text
Skill / Memory / Harness / MCP evidence -> read-only hygiene checks
                                      -> red-team fixture result
                                      -> evidence boundary report
```

This report is evidence only. It does not authorize merge, release,
deployment, publication, token refresh, MCP server startup, SDK/API adapter
work, agent execution, tool invocation, checker promotion, policy activation,
trading, or external action.

## Import Surfaces

| Surface | Imported object | Valid fixture | Red-team fixtures | Boundary |
|---|---:|---:|---:|---|
| Skill Safety | `SKILL.md` | 2 | 4 | capability is not permission |
| Memory / Content | memory JSON record | 1 | 5 | memory is not current truth without source/freshness |
| Harness Evidence | trace/checkpoint/review/receipt JSON bundle | 1 | 5 | trace/checkpoint/receipt is not approval |
| MCP Boundary | MCP-like manifest JSON | 1 | 4 | tool availability/token/audience are not authorization |

Observed fixture suite total: **23** structured fixtures.

## Checker Integration

`checkers/agent-native-evidence/run.py` now validates the fixture suite in its
main execution path:

- positive fixtures must produce no finding.
- red-team fixtures must produce at least one finding.
- fixture counts are emitted in checker stats and human output.

This matters because Phase 4 evidence should not live only in unit tests. The
baseline escalation checker now proves the read-only import examples remain
separated from unsafe interpretations.

## Unsafe Interpretations Blocked

Round 1 blocks these interpretation failures:

- Skill capability treated as permission.
- Skill asks for credentials, tokens, secrets, passwords, or API keys.
- Dangerous Skill tool declarations without read-only and non-authorization
  boundaries.
- Memory missing source receipt.
- Stale memory cited as current truth.
- Cross-project memory imported silently.
- `DEGRADED` or `BLOCKED` evidence rewritten as clean/current fact.
- CandidateRule imported as Policy.
- Checkpoint, trace, or execution receipt claims approval.
- Failed tool-call evidence omitted from trace/checkpoint bundles.
- Human review node mismatch.
- Trace presence treated as truth.
- Token passthrough or real token read/refresh claims.
- Tool availability treated as action authorization.
- Resource/audience equivalence.
- Missing confused-deputy risk notes.

## Non-Imported Runtime Capabilities

Phase 4F explicitly does not import or create:

- real agent traces from external runtimes.
- live LangGraph checkpoints.
- OpenAI trace ingestion.
- Claude Skill execution.
- MCP server connections.
- MCP tool calls.
- token reads, token refreshes, credential discovery, or token validation.
- SDK/API/public platform compatibility.

Those may become future evidence targets only after casebook evidence and
read-only fixtures justify them. They are not implemented by this report.

## Boundary Statement

Agent-native evidence import is evidence hygiene only:

```text
trace present != truth
checkpoint present != approval
skill capability != permission
tool available != authorization
memory present != current truth
manifest present != safe integration
```

Any future adapter, SDK, API, MCP server, or public wedge must pass through a
separate casebook, red-team fixture, OEP, owner review, and receipt path before
it can be discussed as implementation work.

## Verification At Closure

Observed at closure:

- `python checkers/agent-native-evidence/run.py`: PASS, 4 surfaces, 9 red-team
  language cases, 23 structured fixtures, 1 repo skill file.
- `uv run --with pytest python -m pytest tests/unit/governance/test_agent_native_evidence.py -q`:
  40 passed.
- `python scripts/check_artifact_registry.py`: PASS, 674 registered artifacts,
  0 ungoverned.
- `uv run python scripts/check_document_registry.py`: PASS, 229 registered
  docs, 0 completeness violations.

READY/PASS remains evidence sufficiency only. It is not action authorization.
