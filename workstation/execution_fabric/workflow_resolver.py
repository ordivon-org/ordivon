#!/usr/bin/env python3
"""Execution-free EF6b Workflow -> Resource -> Node -> Provider dry-run resolver."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _ids_unique(items: list[dict[str, Any]], field: str, label: str) -> None:
    values = [item[field] for item in items]
    if len(values) != len(set(values)):
        raise ValueError(f"{label} contains duplicate {field}")


def validate_catalog(catalog: dict[str, Any]) -> None:
    if catalog.get("schemaVersion") != 1:
        raise ValueError("unsupported catalog schemaVersion")
    resources = catalog.get("resources", [])
    nodes = catalog.get("nodes", [])
    providers = catalog.get("providers", [])
    _ids_unique(resources, "resourceId", "resources")
    _ids_unique(nodes, "nodeId", "nodes")
    _ids_unique(providers, "providerId", "providers")
    node_map = {node["nodeId"]: node for node in nodes}
    for resource in resources:
        node_id = resource.get("nodeId")
        if node_id is not None and node_id not in node_map:
            raise ValueError(f"resource references unknown node: {resource['resourceId']}")
    for provider in providers:
        node = node_map.get(provider["nodeId"])
        if node is None:
            raise ValueError(f"provider references unknown node: {provider['providerId']}")
        if provider["providerId"] not in node.get("providers", []):
            raise ValueError(f"provider not advertised by node: {provider['providerId']}")
        if not provider.get("capabilities"):
            raise ValueError(f"provider has no capabilities: {provider['providerId']}")
        targets = provider.get("targetNodeIds", [])
        if len(targets) != len(set(targets)):
            raise ValueError(f"provider has duplicate targetNodeIds: {provider['providerId']}")
        unknown_targets = sorted(set(targets) - set(node_map))
        if unknown_targets:
            raise ValueError(
                f"provider targets unknown nodes: {provider['providerId']} -> {unknown_targets}"
            )


def validate_workflow(plan: dict[str, Any]) -> None:
    if plan.get("schemaVersion") != 1:
        raise ValueError("unsupported workflow schemaVersion")
    if plan.get("executionStarted") is not False:
        raise ValueError("dry-run workflow must not claim executionStarted")
    steps = plan.get("steps", [])
    if not steps:
        raise ValueError("workflow has no steps")
    _ids_unique(steps, "stepId", "steps")
    step_ids = {step["stepId"] for step in steps}
    for step in steps:
        if step.get("effectDispatched") is not False:
            raise ValueError(f"step claims effect dispatch: {step['stepId']}")
        dependencies = step.get("dependsOn", [])
        if step["stepId"] in dependencies:
            raise ValueError(f"step depends on itself: {step['stepId']}")
        missing = sorted(set(dependencies) - step_ids)
        if missing:
            raise ValueError(f"step has unknown dependencies: {step['stepId']} -> {missing}")


def resolve(plan: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    validate_workflow(plan)
    validate_catalog(catalog)

    resources = {item["resourceId"]: item for item in catalog["resources"]}
    providers = list(catalog["providers"])
    bindings = []

    for step in plan["steps"]:
        resource = resources.get(step["resourceId"])
        if resource is None:
            bindings.append(
                {
                    "schemaVersion": 1,
                    "stepId": step["stepId"],
                    "resourceId": step["resourceId"],
                    "requestedCapabilityId": step["requestedCapabilityId"],
                    "disposition": "unresolved",
                    "candidateNodeIds": [],
                    "candidateProviderIds": [],
                    "reasonCode": "reason/workflow-resource-unresolved",
                    "dispatchStarted": False,
                }
            )
            continue

        candidates = [
            provider
            for provider in providers
            if step["requestedCapabilityId"] in provider.get("capabilities", [])
            and (
                resource.get("nodeId") is None
                or provider["nodeId"] == resource.get("nodeId")
                or resource.get("nodeId") in provider.get("targetNodeIds", [])
            )
            and (
                step.get("preferredProviderId") is None
                or provider["providerId"] == step.get("preferredProviderId")
            )
        ]
        candidates.sort(key=lambda provider: provider["providerId"])
        candidate_provider_ids = [provider["providerId"] for provider in candidates]
        candidate_node_ids = sorted({provider["nodeId"] for provider in candidates})

        if len(candidates) == 1:
            disposition = "resolved"
            reason = "reason/workflow-binding-resolved"
            selected_node_id = candidates[0]["nodeId"]
            selected_provider_id = candidates[0]["providerId"]
        elif len(candidates) == 0:
            disposition = "unresolved"
            reason = (
                "reason/preferred-provider-unavailable"
                if step.get("preferredProviderId") is not None
                else "reason/no-capable-provider"
            )
            selected_node_id = None
            selected_provider_id = None
        else:
            disposition = "ambiguous"
            reason = "reason/multiple-capable-providers"
            selected_node_id = None
            selected_provider_id = None

        binding = {
            "schemaVersion": 1,
            "stepId": step["stepId"],
            "resourceId": step["resourceId"],
            "requestedCapabilityId": step["requestedCapabilityId"],
            "disposition": disposition,
            "candidateNodeIds": candidate_node_ids,
            "candidateProviderIds": candidate_provider_ids,
            "reasonCode": reason,
            "dispatchStarted": False,
        }
        if selected_node_id is not None:
            binding["selectedNodeId"] = selected_node_id
        if selected_provider_id is not None:
            binding["selectedProviderId"] = selected_provider_id
        bindings.append(binding)

    return {
        "schemaVersion": 1,
        "workflowId": plan["workflowId"],
        "fullyResolved": all(item["disposition"] == "resolved" for item in bindings),
        "bindings": bindings,
        "dispatchStarted": False,
    }


def unresolved_capabilities(binding_plan: dict[str, Any]) -> list[str]:
    return sorted(
        {
            binding["requestedCapabilityId"]
            for binding in binding_plan["bindings"]
            if binding["disposition"] != "resolved"
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", required=True, type=Path)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-fully-resolved", action="store_true")
    args = parser.parse_args()

    plan = json.loads(args.workflow.read_text(encoding="utf-8"))
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    binding = resolve(plan, catalog)
    payload = json.dumps(binding, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")

    if args.require_fully_resolved and not binding["fullyResolved"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
