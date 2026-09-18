#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Any

from anc_canonical import canonical_digest
from ordivon_harness.ordivon.deepseek import DeepSeekSettings, DeepSeekTurnAdapter
from ordivon_harness.ordivon.model import AgentToolDefinition, AgentTurnRequest

HERE = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = HERE / "planning" / "host-e01-fresh-reentry-result-r1.json"

COMMON_SYSTEM = (
    "You are a fresh Host continuity consumer with no prior conversation. "
    "The supplied task inventory is navigation, not domain truth. "
    "Choose exactly one task matching the user's continuation request, then call "
    "task_resume exactly once with that taskId and the exact expectedRevision shown "
    "in the inventory. Do not answer in prose. Do not call any other action. "
    "Exact checkpoint content must be recovered only through task_resume."
)

TASKS: list[dict[str, Any]] = [
    {
        "task_id": "task:host-compact-read-measurement-r1",
        "goal_id": "goal:host-continuity-efficiency",
        "revision": 4,
        "state": "open",
        "checkpoint_digest": "sha256:" + "01" * 32,
        "writer_label": "controller",
        "checkpoint": {
            "schemaVersion": 2,
            "kind": "ordivon.host-working-checkpoint",
            "truthRole": "semantic-working-claim",
            "taskId": "task:host-compact-read-measurement-r1",
            "objective": "Measure whether compact Host inventory preserves fresh-consumer exact re-entry before production admission.",
            "frontier": "Resource and database gates are green; fresh-consumer exact re-entry is the remaining admission gate.",
            "established": ["compact task inventory is materially smaller"],
            "unresolved": ["fresh-consumer selection outcome"],
            "rejected": ["promote compact reads from byte savings alone"],
            "constraints": ["task.resume remains exact hydration boundary"],
            "nextActions": ["run frozen fresh-consumer re-entry A/B"],
            "runtime": None,
            "workStanding": {
                "schemaVersion": 1,
                "truthRole": "checkpoint-authored-work-standing",
                "attention": "ACTIVE",
                "executionAdmission": "ADMITTED_NOW",
                "valueNow": "POSITIVE_VALUE_NOW",
                "progress": "OPEN_FRONTIER",
                "lineage": "SELF_STANDING",
                "relatedTaskIds": [],
                "blockerKinds": [],
                "wake": {"mode": "NONE", "conditions": []},
                "carrier": "RETAIN",
            },
        },
    },
    {
        "task_id": "task:paper-rereview-closure-r1",
        "goal_id": "goal:paper-submission-closure",
        "revision": 7,
        "state": "open",
        "checkpoint_digest": "sha256:" + "02" * 32,
        "writer_label": "review-controller",
        "checkpoint": {
            "schemaVersion": 1,
            "kind": "ordivon.host-working-checkpoint",
            "truthRole": "semantic-working-claim",
            "taskId": "task:paper-rereview-closure-r1",
            "objective": "Close exact peer rereview and repair-to-submission without reopening broad methodology.",
            "frontier": "Frozen science is retained; only concrete rereview defects may trigger repair.",
            "established": ["science freeze complete"],
            "unresolved": ["exact rereview closure"],
            "rejected": ["new exploratory experiments"],
            "constraints": ["no new model fitting"],
            "nextActions": ["perform exact rereview"],
            "runtime": None,
        },
    },
    {
        "task_id": "task:game-causal-lag-loop-r1",
        "goal_id": "goal:game-first-formal-product",
        "revision": 3,
        "state": "open",
        "checkpoint_digest": "sha256:" + "03" * 32,
        "writer_label": "game-controller",
        "checkpoint": {
            "schemaVersion": 1,
            "kind": "ordivon.host-working-checkpoint",
            "truthRole": "semantic-working-claim",
            "taskId": "task:game-causal-lag-loop-r1",
            "objective": "Extend the existing causal-lag mechanic into a small multi-round loop without adding new player verbs.",
            "frontier": "Test whether history creates a non-redundant decision advantage across rounds.",
            "established": ["one-shot mechanic is mechanically green"],
            "unresolved": ["cross-round memory value"],
            "rejected": ["new economy or crafting systems"],
            "constraints": ["reuse existing reward authority"],
            "nextActions": ["run multi-round falsifier"],
            "runtime": None,
        },
    },
    {
        "task_id": "task:artifact-binary-handoff-r1",
        "goal_id": "goal:artifact-delivery-closure",
        "revision": 5,
        "state": "open",
        "checkpoint_digest": "sha256:" + "04" * 32,
        "writer_label": "artifact-controller",
        "checkpoint": {
            "schemaVersion": 1,
            "kind": "ordivon.host-working-checkpoint",
            "truthRole": "semantic-working-claim",
            "taskId": "task:artifact-binary-handoff-r1",
            "objective": "Close the binary artifact egress and cross-conversation handoff bottleneck.",
            "frontier": "Artifact generation works; byte-identity-preserving delivery is the remaining seam.",
            "established": ["native artifact pipeline exists"],
            "unresolved": ["persistent binary handoff"],
            "rejected": ["rebuild artifacts just to move bytes"],
            "constraints": ["preserve byte identity"],
            "nextActions": ["prove one durable egress route"],
            "runtime": None,
        },
    },
    {
        "task_id": "task:runtime-provider-seam-r1",
        "goal_id": "goal:execution-fabric",
        "revision": 2,
        "state": "open",
        "checkpoint_digest": "sha256:" + "05" * 32,
        "writer_label": "runtime-controller",
        "checkpoint": {
            "schemaVersion": 1,
            "kind": "ordivon.host-working-checkpoint",
            "truthRole": "semantic-working-claim",
            "taskId": "task:runtime-provider-seam-r1",
            "objective": "Add the thinnest provider execution seam that reduces Runtime and carrier coupling.",
            "frontier": "Broad execution-fabric expansion is deferred; only a concrete provider boundary is admitted.",
            "established": ["Runtime physical execution authority is separate"],
            "unresolved": ["minimal provider seam"],
            "rejected": ["universal provider ontology"],
            "constraints": ["preserve owner authority"],
            "nextActions": ["test one bounded provider interface"],
            "runtime": None,
        },
    },
    {
        "task_id": "task:security-skill-hardening-r1",
        "goal_id": "goal:security-skill-hardening",
        "revision": 9,
        "state": "open",
        "checkpoint_digest": "sha256:" + "06" * 32,
        "writer_label": "security-controller",
        "checkpoint": {
            "schemaVersion": 1,
            "kind": "ordivon.host-working-checkpoint",
            "truthRole": "semantic-working-claim",
            "taskId": "task:security-skill-hardening-r1",
            "objective": "Harden security skills using controlled test identities and explicit trust boundaries.",
            "frontier": "Wait for controlled test identity before credential-sensitive experiments.",
            "established": ["trust boundary is explicit"],
            "unresolved": ["controlled identity run"],
            "rejected": ["credential extraction"],
            "constraints": ["no bypass of provider verification"],
            "nextActions": ["resume only with controlled identity"],
            "runtime": None,
        },
    },
    {
        "task_id": "task:agent-carrier-fallback-r1",
        "goal_id": "goal:agent-provider-resilience",
        "revision": 6,
        "state": "open",
        "checkpoint_digest": "sha256:" + "07" * 32,
        "writer_label": "agent-controller",
        "checkpoint": {
            "schemaVersion": 1,
            "kind": "ordivon.host-working-checkpoint",
            "truthRole": "semantic-working-claim",
            "taskId": "task:agent-carrier-fallback-r1",
            "objective": "Prove safe carrier fallback under one logical effect identity without duplicate SEND.",
            "frontier": "Only PRE_EFFECT_FAILED attempts may be replaced automatically; ambiguous post-effect state must HOLD.",
            "established": ["pre-effect failure is reroutable"],
            "unresolved": ["cross-carrier duplicate-effect proof"],
            "rejected": ["blind resend after unknown effect"],
            "constraints": ["logical effect identity stays stable"],
            "nextActions": ["run response-loss fallback cases"],
            "runtime": None,
        },
    },
    {
        "task_id": "task:market-readonly-observer-r1",
        "goal_id": "goal:market-capital-readonly",
        "revision": 8,
        "state": "open",
        "checkpoint_digest": "sha256:" + "08" * 32,
        "writer_label": "market-controller",
        "checkpoint": {
            "schemaVersion": 1,
            "kind": "ordivon.host-working-checkpoint",
            "truthRole": "semantic-working-claim",
            "taskId": "task:market-readonly-observer-r1",
            "objective": "Maintain a read-only market research observer without granting live trading authority.",
            "frontier": "Research data paths are admitted; production authorization remains blocked.",
            "established": ["read-only boundary retained"],
            "unresolved": ["observer coverage"],
            "rejected": ["live trade execution"],
            "constraints": ["no production authorization"],
            "nextActions": ["validate read-only data lineage"],
            "runtime": None,
        },
    },
    {
        "task_id": "task:paper-dual-coder-screening-r1",
        "goal_id": "goal:independent-literature-screening",
        "revision": 4,
        "state": "open",
        "checkpoint_digest": "sha256:" + "09" * 32,
        "writer_label": "screening-controller",
        "checkpoint": {
            "schemaVersion": 1,
            "kind": "ordivon.host-working-checkpoint",
            "truthRole": "semantic-working-claim",
            "taskId": "task:paper-dual-coder-screening-r1",
            "objective": "Continue independent dual-coder title and abstract screening without cross-coder contamination.",
            "frontier": "Protocol is frozen; independent coder execution is the scarce next step.",
            "established": ["assignment manifest frozen"],
            "unresolved": ["independent decisions"],
            "rejected": ["controller-side synthetic agreement"],
            "constraints": ["coders remain blinded"],
            "nextActions": ["resume one independent coder"],
            "runtime": None,
        },
    },
    {
        "task_id": "task:agent-plugin-standards-bridge-r1",
        "goal_id": "goal:agent-plugin-standards",
        "revision": 10,
        "state": "open",
        "checkpoint_digest": "sha256:" + "0a" * 32,
        "writer_label": "plugin-controller",
        "checkpoint": {
            "schemaVersion": 1,
            "kind": "ordivon.host-working-checkpoint",
            "truthRole": "semantic-working-claim",
            "taskId": "task:agent-plugin-standards-bridge-r1",
            "objective": "Keep the local skill and plugin bridge aligned with upstream Agent Skills and MCP standards.",
            "frontier": "Compatibility bridge is locally complete; expand only for a demonstrated consumer gap.",
            "established": ["portable skill assets remain independent"],
            "unresolved": ["future consumer incompatibility"],
            "rejected": ["new universal plugin ontology"],
            "constraints": ["upstream standards first"],
            "nextActions": ["wait for concrete consumer gap"],
            "runtime": None,
        },
    },
    {
        "task_id": "task:wsl-safe-restart-preflight-r1",
        "goal_id": "goal:wsl-maintenance-safe-restart",
        "revision": 5,
        "state": "open",
        "checkpoint_digest": "sha256:" + "0b" * 32,
        "writer_label": "workstation-controller",
        "checkpoint": {
            "schemaVersion": 1,
            "kind": "ordivon.host-working-checkpoint",
            "truthRole": "semantic-working-claim",
            "taskId": "task:wsl-safe-restart-preflight-r1",
            "objective": "Prepare a safe WSL compact and restart window without losing current owner state.",
            "frontier": "Maintenance waits for owner freshness and an explicit offline window.",
            "established": ["restart dependencies enumerated"],
            "unresolved": ["maintenance window"],
            "rejected": ["restart while owner state is stale"],
            "constraints": ["revalidate owner state first"],
            "nextActions": ["re-enter when offline window is authorized"],
            "runtime": None,
        },
    },
    {
        "task_id": "task:browser-trust-boundary-measurement-r1",
        "goal_id": "goal:browser-automation-trust-boundary",
        "revision": 11,
        "state": "open",
        "checkpoint_digest": "sha256:" + "0c" * 32,
        "writer_label": "browser-controller",
        "checkpoint": {
            "schemaVersion": 1,
            "kind": "ordivon.host-working-checkpoint",
            "truthRole": "semantic-working-claim",
            "taskId": "task:browser-trust-boundary-measurement-r1",
            "objective": "Measure browser automation trust-boundary failures without bypassing human verification.",
            "frontier": "Differentiate transport readiness from provider trust admission and challenge gating.",
            "established": ["challenge is provider trust state, not Runtime failure"],
            "unresolved": ["safe carrier alternatives"],
            "rejected": ["cookie extraction or challenge evasion"],
            "constraints": ["no verification bypass"],
            "nextActions": ["measure alternative carrier standing"],
            "runtime": None,
        },
    },
]

PROMPTS = {
    "task:host-compact-read-measurement-r1": "Continue the Host work that is deciding whether compact task reads preserve fresh-consumer re-entry before production admission.",
    "task:paper-rereview-closure-r1": "Continue the paper work focused on exact rereview and repair-to-submission closure, not broad methodology expansion.",
    "task:game-causal-lag-loop-r1": "Continue the game work that extends the existing causal-lag mechanic into a multi-round loop without adding new player verbs.",
    "task:artifact-binary-handoff-r1": "Continue the artifact work whose remaining bottleneck is byte-identity-preserving binary handoff across contexts.",
    "task:runtime-provider-seam-r1": "Continue the Runtime work seeking the thinnest provider execution seam rather than a universal execution fabric.",
    "task:security-skill-hardening-r1": "Continue the security-skill hardening work that requires controlled identities and explicit trust boundaries.",
    "task:agent-carrier-fallback-r1": "Continue the Agent carrier work proving safe fallback under one logical effect identity with no duplicate SEND.",
    "task:market-readonly-observer-r1": "Continue the market research observer that must remain read-only and must not gain live trading authority.",
    "task:paper-dual-coder-screening-r1": "Continue the independent dual-coder literature screening work while preserving coder blinding.",
    "task:agent-plugin-standards-bridge-r1": "Continue the Agent Skills and plugin compatibility bridge aligned to upstream standards.",
    "task:wsl-safe-restart-preflight-r1": "Continue the WSL maintenance work preparing a safe restart only after owner freshness and an explicit offline window.",
    "task:browser-trust-boundary-measurement-r1": "Continue the browser automation work measuring trust-boundary and challenge-gating failures without bypassing verification.",
}

def compact(task: dict[str, Any]) -> dict[str, Any]:
    return {key: task[key] for key in (
        "task_id", "goal_id", "revision", "state", "checkpoint_digest", "writer_label"
    )}

def inventory_for(case_index: int, treatment: str) -> list[dict[str, Any]]:
    # Deterministic per-case rotation prevents one fixed list position from becoming a cue.
    offset = (case_index * 5) % len(TASKS)
    ordered = TASKS[offset:] + TASKS[:offset]
    if treatment == "A":
        return ordered
    if treatment == "B":
        return [compact(task) for task in ordered]
    raise ValueError(treatment)

def tool_def() -> AgentToolDefinition:
    ids = [task["task_id"] for task in TASKS]
    return AgentToolDefinition(
        name="task_resume",
        description=(
            "Recover one exact Host semantic checkpoint. Inventory rows are navigation only; "
            "supply the exact taskId and expectedRevision from the selected current row."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "taskId": {"type": "string", "enum": ids},
                "expectedRevision": {"type": "integer", "minimum": 1},
            },
            "required": ["taskId", "expectedRevision"],
            "additionalProperties": False,
        },
    )

def compile_trial(case_index: int, treatment: str) -> AgentTurnRequest:
    target = TASKS[case_index]
    inventory = {
        "schemaVersion": 3 if treatment == "A" else 4,
        "kind": "ordivon.host-task-list",
        "itemView": "full" if treatment == "A" else "basic",
        "tasks": inventory_for(case_index, treatment),
        "hasMore": False,
        "nextCursor": None,
        "truthBoundary": (
            "continuity inventory only; not work priority, owner standing, or domain truth"
        ),
    }
    messages = [
        {"role": "system", "content": COMMON_SYSTEM},
        {
            "role": "system",
            "content": (
                "Current bounded Host task inventory follows. "
                + json.dumps(inventory, sort_keys=True, separators=(",", ":"))
            ),
        },
        {"role": "user", "content": PROMPTS[target["task_id"]]},
    ]
    tool = tool_def()
    return AgentTurnRequest(
        harness_run_id=f"harness-run:host-e01:{case_index+1:02d}:{treatment}",
        turn_id=f"turn:host-e01:{case_index+1:02d}:{treatment}:1",
        sequence=1,
        assignment_id=f"assignment:host-e01:{case_index+1:02d}:{treatment}",
        context_digest=canonical_digest(messages),
        tool_catalog_digest=canonical_digest([tool.to_dict()]),
        messages=tuple(messages),
        tools=(tool,),
        remaining_budget={
            "modelCalls": 1,
            "modelRetries": 0,
            "toolCalls": 1,
            "wallTimeMs": 90_000,
            "observationOnlyTurns": 1,
            "noProgressTurns": 1,
        },
    )

def validate() -> dict[str, Any]:
    assert len(TASKS) == 12
    assert len(PROMPTS) == 12
    ids = [task["task_id"] for task in TASKS]
    assert len(ids) == len(set(ids))
    rows = []
    for i, target in enumerate(TASKS):
        a = compile_trial(i, "A")
        b = compile_trial(i, "B")
        assert a.tools[0].to_dict() == b.tools[0].to_dict()
        assert PROMPTS[target["task_id"]]
        rows.append({
            "caseId": f"E01-{i+1:02d}",
            "targetTaskId": target["task_id"],
            "targetRevision": target["revision"],
            "aMessageBytes": len(json.dumps(a.messages, sort_keys=True).encode()),
            "bMessageBytes": len(json.dumps(b.messages, sort_keys=True).encode()),
        })
    return {"status": "passed", "caseCount": 12, "plannedCalls": 24, "cases": rows}

def usage_value(usage: dict[str, Any], *keys: str) -> int:
    for key in keys:
        value = usage.get(key)
        if isinstance(value, int):
            return value
    return 0

def run_live(output: Path) -> dict[str, Any]:
    validation = validate()
    settings = DeepSeekSettings.from_secret_file(timeout_seconds=60.0, max_output_tokens=128)
    trials: list[dict[str, Any]] = []
    order: list[tuple[int, str]] = []
    for i in range(len(TASKS)):
        order.extend([(i, "A"), (i, "B")] if i % 2 == 0 else [(i, "B"), (i, "A")])
    for ordinal, (case_index, treatment) in enumerate(order, 1):
        target = TASKS[case_index]
        request = compile_trial(case_index, treatment)
        adapter = DeepSeekTurnAdapter(settings)
        _, _, _, body = adapter._prepare_request(request)
        row: dict[str, Any] = {
            "ordinal": ordinal,
            "caseId": f"E01-{case_index+1:02d}",
            "treatment": treatment,
            "targetTaskId": target["task_id"],
            "targetRevision": target["revision"],
            "providerRequestBytes": len(body),
            "requestTokenUpperBound": adapter.request_token_upper_bound(request),
            "providerRequestDigest": adapter.provider_request_digest(request),
        }
        started = time.monotonic()
        try:
            result = adapter.invoke(request)
            row["latencyMs"] = round((time.monotonic() - started) * 1000, 3)
            row["status"] = "completed"
            row["usage"] = result.usage
            row["toolCallCount"] = len(result.tool_calls)
            first = result.tool_calls[0] if result.tool_calls else None
            row["toolName"] = None if first is None else first.name
            row["arguments"] = None if first is None else first.arguments
            row["argumentError"] = None if first is None else first.argument_error
            selected_task = None if first is None else first.arguments.get("taskId")
            selected_revision = None if first is None else first.arguments.get("expectedRevision")
            row["taskIdCorrect"] = selected_task == target["task_id"]
            row["revisionCorrect"] = selected_revision == target["revision"]
            row["exactResumeSelection"] = (
                len(result.tool_calls) == 1
                and first is not None
                and first.name == "task_resume"
                and first.argument_error is None
                and row["taskIdCorrect"]
                and row["revisionCorrect"]
            )
        except Exception as error:
            row["latencyMs"] = round((time.monotonic() - started) * 1000, 3)
            row["status"] = "provider_error"
            row["errorType"] = type(error).__name__
            row["error"] = str(error)[:1000]
        trials.append(row)
        partial = {
            "schemaVersion": 1,
            "kind": "ordivon.host-e01-fresh-reentry-result",
            "truthRole": "measurement-result-not-production-authority",
            "status": "in_progress",
            "providerModel": settings.model,
            "validation": validation,
            "trials": trials,
        }
        output.write_text(json.dumps(partial, indent=2, sort_keys=True) + "\n")
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.host-e01-fresh-reentry-result",
        "truthRole": "measurement-result-not-production-authority",
        "status": "completed",
        "providerModel": settings.model,
        "validation": validation,
        "trials": trials,
    }
    result["summary"] = summarize(result)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result

def summarize(result: dict[str, Any]) -> dict[str, Any]:
    treatments: dict[str, Any] = {}
    total_completed = 0
    for treatment in ("A", "B"):
        rows = [row for row in result["trials"] if row["treatment"] == treatment]
        completed = [row for row in rows if row["status"] == "completed"]
        total_completed += len(completed)
        exact = sum(bool(row.get("exactResumeSelection")) for row in completed)
        task_ok = sum(bool(row.get("taskIdCorrect")) for row in completed)
        rev_ok = sum(bool(row.get("revisionCorrect")) for row in completed if row.get("taskIdCorrect"))
        correct_task = sum(bool(row.get("taskIdCorrect")) for row in completed)
        one_tool = sum(row.get("toolCallCount") == 1 for row in completed)
        def mean(field: str) -> float | None:
            return None if not completed else round(statistics.mean(row[field] for row in completed), 3)
        prompt_tokens = [
            usage_value(row.get("usage", {}), "prompt_tokens", "inputTokens")
            for row in completed
        ]
        treatments[treatment] = {
            "planned": len(rows),
            "completed": len(completed),
            "providerErrors": len(rows) - len(completed),
            "exactResumeSelections": exact,
            "exactResumeSelectionRate": None if not completed else round(exact / len(completed), 6),
            "taskIdAccuracy": None if not completed else round(task_ok / len(completed), 6),
            "revisionAccuracyConditionalOnCorrectTask": (
                None if correct_task == 0 else round(rev_ok / correct_task, 6)
            ),
            "zeroOrMultipleToolCallCount": len(completed) - one_tool,
            "meanProviderRequestBytes": mean("providerRequestBytes"),
            "meanRequestTokenUpperBound": mean("requestTokenUpperBound"),
            "meanPromptTokens": None if not prompt_tokens else round(statistics.mean(prompt_tokens), 3),
            "meanLatencyMs": mean("latencyMs"),
        }
    a, b = treatments["A"], treatments["B"]
    enough = total_completed >= 22 and b["completed"] >= 11
    b_rate = b["exactResumeSelectionRate"]
    a_rate = a["exactResumeSelectionRate"]
    semantic_ok = (
        enough
        and b_rate is not None
        and a_rate is not None
        and b_rate >= (11 / 12)
        and b_rate >= a_rate - (1 / 12)
        and b["zeroOrMultipleToolCallCount"] == 0
    )
    resource_ok = (
        b["meanProviderRequestBytes"] is not None
        and a["meanProviderRequestBytes"] is not None
        and b["meanProviderRequestBytes"] < a["meanProviderRequestBytes"]
        and b["meanRequestTokenUpperBound"] is not None
        and a["meanRequestTokenUpperBound"] is not None
        and b["meanRequestTokenUpperBound"] < a["meanRequestTokenUpperBound"]
    )
    if not enough:
        classification = "INCOMPLETE_PROVIDER"
    elif semantic_ok and resource_ok:
        classification = "PASS"
    else:
        classification = "FAIL_OR_INSUFFICIENT"
    return {
        "classification": classification,
        "completedCalls": total_completed,
        "treatments": treatments,
        "thresholds": {
            "overallCompletedMin": 22,
            "bCompletedMin": 11,
            "bExactResumeRateMin": round(11 / 12, 6),
            "bMayTrailAByAtMost": round(1 / 12, 6),
            "bZeroOrMultipleToolCallsMustEqual": 0,
            "bRequestBytesMustBeLower": True,
            "bTokenUpperBoundMustBeLower": True,
        },
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.validate_only:
        print(json.dumps(validate(), indent=2, sort_keys=True))
        return 0
    result = run_live(args.output)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
