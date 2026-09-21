#!/usr/bin/env python3
"""Experimental projection from Chromium's AX tree to browser action candidates.

This module deliberately does not compute accessible names or ARIA roles. Chromium owns
those semantics through Accessibility.getFullAXTree. The experiment owns only the thin
binding from observed accessibility roles/properties to candidate operations and a local,
ephemeral accessibility-tree context used by decision models.
"""

from __future__ import annotations

from typing import Any, Mapping

import hashlib
import json

CLICK_ROLES = frozenset(
    {
        "button",
        "link",
        "checkbox",
        "radio",
        "switch",
        "tab",
        "menuitem",
        "menuitemradio",
        "gridcell",
    }
)
EDITABLE_ROLES = frozenset({"textbox", "searchbox", "spinbutton"})
CONTEXT_ROLES = frozenset(
    {
        "article",
        "listitem",
        "row",
        "form",
        "dialog",
        "group",
        "navigation",
    }
)


def _ax_value(node: Mapping[str, Any], field: str) -> Any:
    value = node.get(field)
    if isinstance(value, Mapping):
        return value.get("value")
    return None


def _properties(node: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in node.get("properties", []):
        if not isinstance(item, Mapping):
            continue
        name = item.get("name")
        raw = item.get("value")
        if isinstance(name, str) and isinstance(raw, Mapping):
            out[name] = raw.get("value")
    return out


def _descendants(start: str, by_id: Mapping[str, Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    stack = list(reversed(by_id[start].get("childIds") or []))
    while stack:
        node_id = stack.pop()
        node = by_id.get(str(node_id))
        if node is None:
            continue
        rows.append(node)
        children = list(node.get("childIds") or [])
        stack.extend(reversed([str(child) for child in children]))
    return rows


def _context_root(node: Mapping[str, Any], by_id: Mapping[str, Mapping[str, Any]]) -> str:
    current = node
    while True:
        parent_id = current.get("parentId")
        if parent_id is None:
            return str(node["nodeId"])
        parent = by_id.get(str(parent_id))
        if parent is None:
            return str(node["nodeId"])
        if _ax_value(parent, "role") in CONTEXT_ROLES:
            return str(parent["nodeId"])
        current = parent


def _context_text(node: Mapping[str, Any], by_id: Mapping[str, Mapping[str, Any]]) -> str:
    root_id = _context_root(node, by_id)
    nodes = [by_id[root_id], *_descendants(root_id, by_id)]
    seen: set[str] = set()
    parts: list[str] = []
    for item in nodes:
        name = _ax_value(item, "name")
        if not isinstance(name, str):
            continue
        text = name.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        parts.append(text)
    return "\n".join(parts)


def _base_candidate(
    node: Mapping[str, Any],
    by_id: Mapping[str, Mapping[str, Any]],
    operation: str,
) -> dict[str, Any]:
    props = _properties(node)
    candidate = {
        "operation": operation,
        "axNodeId": str(node["nodeId"]),
        "backendDOMNodeId": node.get("backendDOMNodeId"),
        "role": _ax_value(node, "role"),
        "name": _ax_value(node, "name") or "",
        "description": _ax_value(node, "description"),
        "states": props,
        "context": _context_text(node, by_id),
    }
    value = _ax_value(node, "value")
    if value is not None:
        candidate["value"] = value
    return candidate


def project_ax_candidates(tree: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Project one Chromium AX tree into ephemeral operation-specific candidates."""

    raw_nodes = tree.get("nodes")
    if not isinstance(raw_nodes, list):
        raise ValueError("AX tree must contain a nodes list")
    by_id = {
        str(node["nodeId"]): node
        for node in raw_nodes
        if isinstance(node, Mapping) and node.get("nodeId") is not None
    }

    candidates: list[dict[str, Any]] = []
    for node in raw_nodes:
        if not isinstance(node, Mapping) or node.get("nodeId") is None:
            continue
        if node.get("ignored") is True:
            continue
        backend = node.get("backendDOMNodeId")
        if not isinstance(backend, int):
            continue
        role = _ax_value(node, "role")
        props = _properties(node)
        if props.get("disabled") is True:
            continue

        if role in CLICK_ROLES:
            candidates.append(_base_candidate(node, by_id, "CLICK"))
            continue

        if role in EDITABLE_ROLES:
            if props.get("readonly") is not True:
                candidates.append(_base_candidate(node, by_id, "FILL"))
            candidates.append(_base_candidate(node, by_id, "CLICK"))
            continue

        if role == "combobox":
            if props.get("editable"):
                candidates.append(_base_candidate(node, by_id, "FILL"))
                candidates.append(_base_candidate(node, by_id, "CLICK"))
                continue
            for option in _descendants(str(node["nodeId"]), by_id):
                if _ax_value(option, "role") != "option":
                    continue
                option_props = _properties(option)
                if option.get("ignored") is True or option_props.get("disabled") is True:
                    continue
                if option_props.get("selected") is True:
                    continue
                candidate = _base_candidate(node, by_id, "SELECT")
                candidate["optionName"] = _ax_value(option, "name") or ""
                candidates.append(candidate)

    return candidates


def _semantic_payload(candidate: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "operation": candidate.get("operation"),
        "role": candidate.get("role"),
        "name": candidate.get("name"),
        "description": candidate.get("description"),
        "states": candidate.get("states", {}),
        "context": candidate.get("context", ""),
    }
    if "value" in candidate:
        payload["value"] = candidate.get("value")
    if "optionName" in candidate:
        payload["optionName"] = candidate.get("optionName")
    return payload


def _semantic_digest(candidate: Mapping[str, Any]) -> str:
    raw = json.dumps(
        _semantic_payload(candidate),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def make_semantic_witness(candidate: Mapping[str, Any]) -> dict[str, Any]:
    backend = candidate.get("backendDOMNodeId")
    operation = candidate.get("operation")
    if not isinstance(backend, int) or not isinstance(operation, str):
        raise ValueError("candidate lacks stable browser identity")
    return {
        "backendDOMNodeId": backend,
        "operation": operation,
        "optionName": candidate.get("optionName"),
        "semanticDigest": _semantic_digest(candidate),
    }


def check_semantic_witness(
    candidates: list[Mapping[str, Any]],
    witness: Mapping[str, Any],
) -> dict[str, Any]:
    matches = [
        candidate
        for candidate in candidates
        if candidate.get("backendDOMNodeId") == witness.get("backendDOMNodeId")
        and candidate.get("operation") == witness.get("operation")
        and candidate.get("optionName") == witness.get("optionName")
    ]
    if not matches:
        return {"standing": "MISSING", "currentSemanticDigest": None}
    if len(matches) != 1:
        return {"standing": "AMBIGUOUS", "currentSemanticDigest": None}
    current = _semantic_digest(matches[0])
    return {
        "standing": "MATCH" if current == witness.get("semanticDigest") else "SEMANTIC_CHANGED",
        "currentSemanticDigest": current,
    }
