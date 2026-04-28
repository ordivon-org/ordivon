# Repo Governance CLI

Status: **IMPLEMENTED**
Date: 2026-04-28
Phase: 3.3
Tags: `cli`, `repo-governance`, `adapter`, `governance`, `prototype`

## 1. Purpose

The Repo Governance CLI is the first runnable entrypoint for Ordivon's Repo
Governance Pack. It classifies an AI coding agent's intent before execution —
producing a JSON governance decision (execute / escalate / reject + reasons).

The CLI is an **Adapter-layer** component. Its output is evidence, not truth.
It does not execute code, modify files, call shell/MCP/IDE, write databases,
or create ExecutionRequest/ExecutionReceipt records.

## 2. Scope

- Accept structured CLI arguments: task_description, file_paths, estimated_impact, reasoning, test_plan
- Construct a CodingDecisionPayload and DecisionIntake
- Run governance classification through RiskEngine.validate_intake() with CodingDisciplinePolicy
- Output JSON with decision, reasons, pack, underlying_policy, and side-effect guarantees
- Return appropriate exit codes: 0 (execute), 2 (escalate), 3 (reject), 1 (error)

## 3. Non-Goals

The CLI does NOT:
- Execute code or shell commands
- Modify files on disk
- Connect to MCP, IDE, or shell agents
- Run git operations (commit, push, merge)
- Write to any database
- Create ExecutionRequest or ExecutionReceipt ORM records
- Generate CandidateRules or PolicyProposals
- Read real diffs (unless path strings are explicitly provided by user)
- Modify governance/risk_engine, packs/coding policy, API, or ORM schema

## 4. CLI Usage

### Basic invocation

```bash
uv run python scripts/repo_governance_cli.py \
  --task-description "Fix unit test naming" \
  --file-path tests/unit/test_example.py \
  --estimated-impact low \
  --reasoning "Small test-only cleanup" \
  --test-plan "uv run pytest tests/unit/test_example.py" \
  --json
```

### Multiple file paths

```bash
uv run python scripts/repo_governance_cli.py \
  --task-description "Extract shared validation helpers" \
  --file-path shared/validation.py \
  --file-path capabilities/domain/finance_decisions.py \
  --estimated-impact medium \
  --reasoning "Duplicate validation logic." \
  --test-plan "uv run pytest tests/unit/capabilities/ -v" \
  --json
```

### Without test plan (will escalate)

```bash
uv run python scripts/repo_governance_cli.py \
  --task-description "Optimize database query" \
  --file-path domains/strategy/service.py \
  --estimated-impact medium \
  --reasoning "N+1 query detected." \
  --json
```

## 5. Input Arguments

| Argument | Required | Values | Description |
|----------|----------|--------|-------------|
| `--task-description` | Yes | string | What the AI coding agent intends to do |
| `--file-path` | Yes (≥1) | string (repeatable) | File path(s) the agent intends to modify |
| `--estimated-impact` | Yes | low / medium / high | Estimated risk/impact of the change |
| `--reasoning` | Yes | string | Why the agent thinks this change is necessary |
| `--test-plan` | No | string | How the change will be tested |
| `--json` | Optional | flag | Output JSON (default: true) |

## 6. Output JSON Schema

```json
{
  "decision": "execute|escalate|reject",
  "reasons": ["string", ...],
  "pack": "repo_governance",
  "underlying_policy": "coding",
  "source": "repo_governance_cli",
  "side_effects": {
    "file_writes": false,
    "shell": false,
    "mcp": false,
    "ide": false,
    "execution_receipt": false,
    "execution_request": false
  }
}
```

## 7. Decision Semantics

| Decision | Meaning | Trigger Examples |
|----------|---------|-----------------|
| `execute` | Safe to proceed | Valid test/doc fix with test plan |
| `escalate` | Human review required | High impact, missing test_plan |
| `reject` | Blocked — must not proceed | Forbidden file paths (.env, uv.lock, migration runner), missing required fields |

Decision priority: reject > escalate > execute.

Classification is performed by `CodingDisciplinePolicy` through
`RiskEngine.validate_intake()`. The CLI adds no additional policy logic —
it is a pure adapter.

## 8. Exit Code Semantics

| Exit Code | Decision | Rationale |
|-----------|----------|-----------|
| 0 | execute | Safe — CI can proceed |
| 2 | escalate | Needs review — CI may choose to block or warn |
| 3 | reject | Blocked — CI must fail |
| 1 | internal error | CLI itself failed (not a governance decision) |

CI integration note: If strict blocking is desired, treat exit codes 1, 2, and 3
as failures. If advisory-only, exit 0 for execute and escalate, exit 3 for reject.

## 9. Side-Effect Guarantees

All `side_effects` fields are always `false`. The CLI produces only JSON on
stdout. It does not:

- Write any files (not even logs)
- Execute any shell commands beyond its own Python process
- Connect to MCP servers
- Connect to IDE plugins
- Create ExecutionRequest or ExecutionReceipt records
- Write to any database

These guarantees are enforced by design (the CLI has no code paths for any of
these actions) and verified by tests.

## 10. Relationship to Coding Pack

The CLI reuses `packs/coding/policy.py` (CodingDisciplinePolicy) as its
underlying policy provider. It does NOT create a new Pack policy type.
The `underlying_policy` field in the output is `"coding"`.

This is intentional: Repo Governance CLI v1 validates single code change
intents, not full repository workflow intents. A future RepoGovernancePolicy
for workflow-level validation is planned but deferred.

## 11. Relationship to Repo Governance Pack

The Repo Governance Pack (`docs/product/repo-governance-pack.md`) defines the
product strategy. The CLI is the first adapter that connects the governance
core to a real user-facing entrypoint.

```
User CLI input
  → CodingDecisionPayload (packs/coding/models.py)
  → DecisionIntake (domains/decision_intake/models.py)
  → RiskEngine.validate_intake(pack_policy=CodingDisciplinePolicy())
  → GovernanceDecision (execute/escalate/reject)
  → JSON output
```

The Repo Governance Pack also intends to govern workflow-level concerns
(protected branches, CI config, secrets). Those are not yet implemented in
the CLI v1.

## 12. Relationship to Future Adapters

| Adapter | Status | Relationship to CLI |
|---------|--------|--------------------|
| CLI | Phase 3.3 (this doc) | First working adapter |
| GitHub Actions | Future | Same classify-before-execute pattern; reads PR metadata |
| IDE | Future | Same JSON output; IDE renders inline feedback |
| MCP | Future | Same governance pipeline; MCP tool invocation classified |

All adapters share the same invariants:
- Output is evidence, not truth
- Cannot write Core truth directly
- Adapters classify; they do not execute
- Every adapter action produces a Receipt

## 13. Test Evidence

20 unit tests cover:
- Valid test fix → execute
- Doc change with plan → execute
- Missing task_description → reject
- Missing file_paths → reject
- Forbidden .env → reject
- Forbidden uv.lock → reject
- Forbidden migration runner → reject
- High impact → escalate
- Missing test_plan → escalate
- Multi-file medium change with plan → execute
- JSON output has decision, reasons, side_effects
- JSON output has pack and underlying_policy
- CLI does not create ExecutionRequest
- CLI does not create ExecutionReceipt
- CLI does not call shell
- CLI does not call MCP
- CLI does not call IDE
- CLI does not write files

Run: `uv run pytest tests/unit/test_repo_governance_cli.py -v`

Status: 20/20 PASS.

## 14. Eval Corpus Compatibility

The CLI behavior is consistent with `evals/coding_cases.json` (10 cases, C01-C10).
All eval cases produce the same decisions when submitted through the CLI:
- C01/C02/C10 → execute ✓
- C03/C04/C05/C06/C07 → reject ✓
- C08/C09 → escalate ✓

Run: `uv run python evals/run_evals.py`

Status: 24/24 PASS (10 finance + 10 coding + 4 cross-pack).

## 15. Limitations

- Does NOT govern workflow-level concerns (branches, PRs, CI config)
- Does NOT read real git diffs
- Does NOT persist decisions to a database
- Does NOT generate Receipt records
- Does NOT trigger CI or GitHub Actions
- Uses CodingDisciplinePolicy, not a dedicated RepoGovernancePolicy
- No pretty-printing or TUI mode
- No configuration file support
- Exit code mapping (2=escalate) may confuse CI systems expecting 0/1 only

## 16. Next Recommended Wave

**Phase 3.4: GitHub Actions Adapter** — A GitHub Actions action that reads PR
metadata, calls the governance pipeline, and annotates the PR with the decision.
This is the natural next step: prove the CLI pattern can be consumed by CI
before building IDE or MCP adapters.

Alternatively: **Phase 3.5: Eval Corpus Expansion** — Grow from 24 cases to
40+ based on real CLI usage patterns, add adversarial cases, and integrate
the CLI into the eval runner so `run_evals.py` can test the CLI directly.
