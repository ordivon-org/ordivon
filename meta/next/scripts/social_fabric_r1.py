#!/usr/bin/env python3
"""Rebuildable Social Fabric R1 projection over owner-native observations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SNAPSHOT_KIND = "ordivon.social-fabric-owner-cut"
PROJECTION_KIND = "ordivon.social-fabric-current-projection"


class SocialFabricError(ValueError):
    """Fail-closed projection input error."""


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SocialFabricError(f"{label} must be an object")
    return value


def _rows(value: Any, label: str, key: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise SocialFabricError(f"{label} must be a list")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        row = _object(raw, f"{label}[{index}]")
        identity = row.get(key)
        if not isinstance(identity, str) or not identity:
            raise SocialFabricError(f"{label}[{index}].{key} must be non-empty")
        if identity in seen:
            raise SocialFabricError(f"duplicate {label} identity: {identity}")
        seen.add(identity)
        result.append(row)
    return result


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot.get("schemaVersion") != SCHEMA_VERSION:
        raise SocialFabricError("unsupported social snapshot schemaVersion")
    if snapshot.get("kind") != SNAPSHOT_KIND:
        raise SocialFabricError("unsupported social snapshot kind")
    if not isinstance(snapshot.get("observedAt"), str) or not snapshot["observedAt"]:
        raise SocialFabricError("observedAt must be non-empty")

    host = _object(snapshot.get("host"), "host")
    tasks = _rows(host.get("tasks"), "host.tasks", "taskId")
    for task in tasks:
        if task.get("state") not in {"open", "completed", "abandoned"}:
            raise SocialFabricError(f"invalid Task state: {task['taskId']}")
        if not isinstance(task.get("revision"), int) or task["revision"] < 1:
            raise SocialFabricError(f"invalid Task revision: {task['taskId']}")
        digest = task.get("checkpointDigest")
        if not isinstance(digest, str) or not digest.startswith("sha256:"):
            raise SocialFabricError(f"invalid checkpoint digest: {task['taskId']}")
        runtime = task.get("runtime")
        if runtime is not None:
            runtime = _object(runtime, f"{task['taskId']}.runtime")
            if (
                not isinstance(runtime.get("workspaceId"), str)
                or not runtime["workspaceId"]
            ):
                raise SocialFabricError(
                    f"{task['taskId']}.runtime.workspaceId must be non-empty"
                )

    runtime = _object(snapshot.get("runtime"), "runtime")
    _rows(runtime.get("workspaces"), "runtime.workspaces", "workspaceId")
    _rows(
        runtime.get("closedWorkspaces", []),
        "runtime.closedWorkspaces",
        "workspaceId",
    )
    git = _object(snapshot.get("git"), "git")
    if not isinstance(git.get("mainRevision"), str) or not git["mainRevision"]:
        raise SocialFabricError("git.mainRevision must be non-empty")


def _signal(
    signal_type: str,
    source: str,
    subject: str,
    observed_at: str,
    data: dict[str, Any],
    truth_boundary: str,
) -> dict[str, Any]:
    identity = {
        "type": signal_type,
        "source": source,
        "subject": subject,
        "observedAt": observed_at,
        "data": data,
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.social-signal",
        "id": "signal:" + canonical_digest(identity),
        "type": signal_type,
        "source": source,
        "subject": subject,
        "observedAt": observed_at,
        "data": data,
        "truthBoundary": truth_boundary,
    }


def compile_signals(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    observed_at = snapshot["observedAt"]
    result: list[dict[str, Any]] = []
    for task in snapshot["host"]["tasks"]:
        result.append(
            _signal(
                "ordivon.host.task.observed",
                "host",
                task["taskId"],
                observed_at,
                task,
                "Host continuity observation only; foreign references require owner revalidation.",
            )
        )
    for workspace in snapshot["runtime"]["workspaces"]:
        result.append(
            _signal(
                "ordivon.runtime.workspace.observed",
                "runtime",
                workspace["workspaceId"],
                observed_at,
                workspace,
                "Runtime physical/source-state observation only; no domain completion implied.",
            )
        )
    for workspace in snapshot["runtime"].get("closedWorkspaces", []):
        result.append(
            _signal(
                "ordivon.runtime.workspace.closed",
                "runtime",
                workspace["workspaceId"],
                observed_at,
                workspace,
                "Runtime workspace lifecycle observation only.",
            )
        )
    for capability in snapshot.get("gateway", {}).get("capabilities", []):
        if not isinstance(capability, dict) or not isinstance(
            capability.get("capability"), str
        ):
            continue
        result.append(
            _signal(
                "ordivon.gateway.capability.observed",
                "gateway",
                capability["capability"],
                observed_at,
                capability,
                "Gateway routing/availability projection only; natural owner truth remains external.",
            )
        )
    return sorted(result, key=lambda row: (row["source"], row["subject"], row["type"]))


def _finding(
    code: str,
    severity: str,
    subject_refs: list[str],
    evidence_refs: list[str],
    detail: str,
) -> dict[str, Any]:
    body = {
        "code": code,
        "severity": severity,
        "subjectRefs": sorted(subject_refs),
        "evidenceRefs": sorted(evidence_refs),
        "detail": detail,
    }
    return {
        "findingId": "finding:" + canonical_digest(body),
        **body,
        "truthBoundary": (
            "Deterministic finding over this cut; not owner-state mutation, priority, "
            "assignment, execution authority, or domain verdict."
        ),
    }


def compile_projection(snapshot: dict[str, Any]) -> dict[str, Any]:
    validate_snapshot(snapshot)
    signals = compile_signals(snapshot)
    tasks = {row["taskId"]: row for row in snapshot["host"]["tasks"]}
    workspaces = {row["workspaceId"]: row for row in snapshot["runtime"]["workspaces"]}
    closed = {
        row["workspaceId"]: row
        for row in snapshot["runtime"].get("closedWorkspaces", [])
    }
    ancestor_map = snapshot["git"].get("knownAncestorOfMain", {})
    if not isinstance(ancestor_map, dict):
        raise SocialFabricError("git.knownAncestorOfMain must be an object")

    nodes = [
        {
            "id": task_id,
            "nodeKind": "task",
            "owner": "host",
            "state": task["state"],
            "revision": task["revision"],
        }
        for task_id, task in sorted(tasks.items())
    ]
    nodes.extend(
        {
            "id": workspace_id,
            "nodeKind": "workspace",
            "owner": "runtime",
            "dirty": bool(workspace.get("dirty")),
            "currentHeadRevision": workspace.get("currentHeadRevision"),
        }
        for workspace_id, workspace in sorted(workspaces.items())
    )
    nodes.append(
        {
            "id": f"git:{snapshot['git']['mainRevision']}",
            "nodeKind": "git-main",
            "owner": "git",
            "revision": snapshot["git"]["mainRevision"],
        }
    )

    edges: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    referenced_workspaces: set[str] = set()

    for task_id, task in sorted(tasks.items()):
        runtime_ref = task.get("runtime")
        if not isinstance(runtime_ref, dict):
            continue
        workspace_id = runtime_ref["workspaceId"]
        referenced_workspaces.add(workspace_id)
        edges.append(
            {
                "edgeKind": "task-runtime-reference",
                "from": task_id,
                "to": workspace_id,
                "authority": "host-checkpoint-claim",
            }
        )
        workspace = workspaces.get(workspace_id)
        if workspace is None:
            code = (
                "TASK_REFERENCES_CLOSED_WORKSPACE"
                if workspace_id in closed
                else "TASK_WORKSPACE_MISSING_FROM_CUT"
            )
            findings.append(
                _finding(
                    code,
                    "warning",
                    [task_id, workspace_id],
                    [task["checkpointDigest"]],
                    (
                        "Host continuity references a Runtime workspace observed closed."
                        if workspace_id in closed
                        else "Host continuity references a workspace absent from this bounded Runtime cut."
                    ),
                )
            )
            continue

        observed_head = runtime_ref.get("observedHeadRevision")
        current_head = workspace.get("currentHeadRevision")
        if (
            isinstance(observed_head, str)
            and isinstance(current_head, str)
            and observed_head != current_head
        ):
            findings.append(
                _finding(
                    "CHECKPOINT_WORKSPACE_HEAD_DRIFT",
                    "warning",
                    [task_id, workspace_id],
                    [task["checkpointDigest"]],
                    f"Host observed {observed_head}; Runtime now projects {current_head}.",
                )
            )
        if task["state"] == "completed" and bool(workspace.get("dirty")):
            findings.append(
                _finding(
                    "COMPLETED_TASK_DIRTY_WORKSPACE",
                    "warning",
                    [task_id, workspace_id],
                    [task["checkpointDigest"]],
                    "Completed Host Task still references a dirty live Runtime workspace.",
                )
            )
        implementation = task.get("implementationCommitRef")
        if (
            task["state"] == "open"
            and isinstance(implementation, str)
            and ancestor_map.get(implementation) is True
        ):
            findings.append(
                _finding(
                    "MERGED_IMPLEMENTATION_TASK_OPEN",
                    "warning",
                    [task_id, f"git:{implementation}"],
                    [task["checkpointDigest"]],
                    "Explicit implementation commit is on observed main while Task remains open.",
                )
            )

    for workspace_id in sorted(set(workspaces) - referenced_workspaces):
        findings.append(
            _finding(
                "WORKSPACE_WITHOUT_SELECTED_TASK_REFERENCE",
                "info",
                [workspace_id],
                [],
                "No selected Task references this workspace; bounded absence is not global orphan proof.",
            )
        )

    findings.sort(key=lambda row: (row["severity"], row["code"], row["findingId"]))
    graph = {
        "schemaVersion": 1,
        "kind": "ordivon.social-work-graph",
        "observedAt": snapshot["observedAt"],
        "nodes": sorted(nodes, key=lambda row: (row["nodeKind"], row["id"])),
        "edges": sorted(
            edges, key=lambda row: (row["edgeKind"], row["from"], row["to"])
        ),
        "truthBoundary": "Cross-owner reference projection only; natural owners retain truth.",
    }
    fact_set = {
        "schemaVersion": 1,
        "kind": "ordivon.social-fact-set",
        "observedAt": snapshot["observedAt"],
        "signals": signals,
    }
    attention = [row for row in findings if row["severity"] in {"warning", "error"}]
    available = sorted(
        row["capability"]
        for row in snapshot.get("gateway", {}).get("capabilities", [])
        if isinstance(row, dict)
        and isinstance(row.get("capability"), str)
        and row.get("available") is True
    )
    linked = sum(
        isinstance(task.get("runtime"), dict)
        and task["runtime"]["workspaceId"] in workspaces
        for task in tasks.values()
    )
    return {
        "schemaVersion": 1,
        "kind": PROJECTION_KIND,
        "truthRole": "rebuildable-cross-owner-projection",
        "observedAt": snapshot["observedAt"],
        "sourceSnapshotDigest": canonical_digest(snapshot),
        "factSetDigest": canonical_digest(fact_set),
        "workGraphDigest": canonical_digest(graph),
        "findingsDigest": canonical_digest(findings),
        "factSet": fact_set,
        "workGraph": graph,
        "reconciliation": {
            "findings": findings,
            "findingCount": len(findings),
            "warningOrErrorCount": len(attention),
        },
        "attention": attention,
        "commonOperatingPicture": {
            "gitMainRevision": snapshot["git"]["mainRevision"],
            "selectedTaskCount": len(tasks),
            "selectedWorkspaceCount": len(workspaces),
            "linkedTaskCount": linked,
            "closedWorkspaceReferenceCount": sum(
                isinstance(task.get("runtime"), dict)
                and task["runtime"]["workspaceId"] in closed
                for task in tasks.values()
            ),
            "checkpointWorkspaceHeadDriftCount": sum(
                row["code"] == "CHECKPOINT_WORKSPACE_HEAD_DRIFT" for row in findings
            ),
            "availableCapabilities": available,
            "attentionCount": len(attention),
        },
        "nonClaims": [
            "Open does not mean active.",
            "Physical realization does not establish domain completion.",
            "Bounded absence does not prove global absence.",
            "This projection grants no execution, scheduling, assignment, priority, or EffectAuthority.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("view", choices=("current", "attention", "reconcile"))
    parser.add_argument("--snapshot", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.snapshot.read_text(encoding="utf-8"))
    projection = compile_projection(_object(raw, str(args.snapshot)))
    if args.view == "current":
        output: Any = projection
    elif args.view == "attention":
        output = {
            "schemaVersion": 1,
            "kind": "ordivon.social-attention-projection",
            "observedAt": projection["observedAt"],
            "sourceSnapshotDigest": projection["sourceSnapshotDigest"],
            "items": projection["attention"],
        }
    else:
        output = {
            "schemaVersion": 1,
            "kind": "ordivon.social-reconciliation-projection",
            "observedAt": projection["observedAt"],
            "sourceSnapshotDigest": projection["sourceSnapshotDigest"],
            **projection["reconciliation"],
        }
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
