"""One pure strict Runtime target-inventory validity law for all consumers.

This validates Owner response consistency, never authorizes execution.
"""

from __future__ import annotations


def valid_runtime_target_inventory(targets: object) -> bool:
    """A positive aggregate must reject duplicate or contradictory targets."""
    if not isinstance(targets, list):
        return False
    names: list[str] = []
    for item in targets:
        if not isinstance(item, dict):
            return False
        name, configured, available = (
            item.get("target"),
            item.get("configured"),
            item.get("available"),
        )
        if (
            not isinstance(name, str)
            or not name.strip()
            or type(configured) is not bool
            or type(available) is not bool
            or (available and not configured)
        ):
            return False
        names.append(name)
    return len(names) == len(set(names))


def valid_runtime_status_envelope(response: object) -> bool:
    """A Runtime v1 status response is an explicit wire contract.

    A target list in an arbitrary JSON object is NOT authenticated evidence
    of the versioned Runtime describe API.
    """
    if (
        not isinstance(response, dict)
        or type(response.get("schemaVersion")) is not int
        or response["schemaVersion"] != 1
    ):
        return False
    node = response.get("node")
    targets = response.get("targets")
    return (
        isinstance(node, dict)
        and isinstance(node.get("nodeId"), str)
        and bool(node["nodeId"].strip())
        and isinstance(targets, list)
        and all(isinstance(target, dict) for target in targets)
    )


def valid_runtime_execution_context_inventory(target: dict, target_name: str | None) -> bool:
    """Canonical Windows inventory is authoritative when present, even when empty.

    Do not infer executable authority from legacy compatibility fields when the
    Owner explicitly reports a canonical inventory. Context values remain
    provider-defined; this validates their representation, not authorization.
    """
    fields = (
        ("windowsContexts", "windowsAuthorities")
        if target_name == "windows_native"
        else ("executionProfiles",)
    )
    if any(field in target and not isinstance(target[field], list) for field in fields):
        return False
    if target_name != "windows_native" or "windowsContexts" not in target:
        return True
    contexts = target["windowsContexts"]
    if any(not isinstance(value, dict) or not value for value in contexts):
        return False
    if any(value in contexts[:index] for index, value in enumerate(contexts)):
        return False
    return bool(contexts) or target.get("available") is not True
