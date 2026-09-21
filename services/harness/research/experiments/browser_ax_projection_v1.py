#!/usr/bin/env python3
"""Experimental projection from Chromium's AX tree to browser action candidates.

Chromium owns accessible roles/names/states through Accessibility.getFullAXTree.
The experiment owns only:
- a thin binding from browser-observed semantics to supported effects;
- a minimal DOM metadata safety gate for HTML affordances AX alone cannot distinguish;
- local, ephemeral AX context for decision evidence;
- a decision-bound semantic witness.

DOM metadata is browser-owned input such as DOM.describeNode results. It is not
persisted as a new Ordivon DOM ontology and is never used to recompute accessible names.
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
UNSAFE_INPUT_TYPES = frozenset({"file", "hidden", "password"})


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


def _dom_descriptor(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    nested = value.get("node")
    if isinstance(nested, Mapping):
        return nested
    return value


def _dom_attributes(value: Mapping[str, Any] | None) -> dict[str, str]:
    descriptor = _dom_descriptor(value)
    raw = descriptor.get("attributes")
    if not isinstance(raw, list):
        return {}
    out: dict[str, str] = {}
    for index in range(0, len(raw) - 1, 2):
        key, val = raw[index], raw[index + 1]
        if isinstance(key, str) and isinstance(val, str):
            out[key.lower()] = val
    return out


def _dom_node_name(value: Mapping[str, Any] | None) -> str:
    descriptor = _dom_descriptor(value)
    raw = descriptor.get("nodeName")
    return raw.upper() if isinstance(raw, str) else ""


def dom_metadata_from_document(value: Mapping[str, Any]) -> dict[int, Mapping[str, Any]]:
    """Flatten one DOM.getDocument response/root into backend-node metadata."""

    root = value.get("root") if isinstance(value.get("root"), Mapping) else value
    if not isinstance(root, Mapping):
        raise ValueError("DOM document must contain a root node")

    out: dict[int, Mapping[str, Any]] = {}
    stack: list[Mapping[str, Any]] = [root]
    while stack:
        node = stack.pop()
        backend = node.get("backendNodeId")
        if isinstance(backend, int):
            out[backend] = node

        content_document = node.get("contentDocument")
        if isinstance(content_document, Mapping):
            stack.append(content_document)

        for key in ("children", "shadowRoots"):
            children = node.get(key)
            if isinstance(children, list):
                stack.extend(child for child in reversed(children) if isinstance(child, Mapping))
    return out


def _dom_metadata_for(
    dom_metadata: Mapping[int | str, Mapping[str, Any]],
    backend: int,
) -> Mapping[str, Any]:
    value = dom_metadata.get(backend)
    if value is None:
        value = dom_metadata.get(str(backend))
    return value if isinstance(value, Mapping) else {}


def _unsafe_input(value: Mapping[str, Any] | None) -> bool:
    if _dom_node_name(value) != "INPUT":
        return False
    input_type = _dom_attributes(value).get("type", "text").strip().lower()
    return input_type in UNSAFE_INPUT_TYPES


def _contenteditable(value: Mapping[str, Any] | None) -> bool:
    attrs = _dom_attributes(value)
    raw = attrs.get("contenteditable")
    return raw is not None and raw.strip().lower() not in {"false", "inherit"}


def _summary(value: Mapping[str, Any] | None) -> bool:
    return _dom_node_name(value) == "SUMMARY"


def _has_actionable_descendant(
    node: Mapping[str, Any],
    by_id: Mapping[str, Mapping[str, Any]],
) -> bool:
    for child in _descendants(str(node["nodeId"]), by_id):
        if child.get("ignored") is True:
            continue
        props = _properties(child)
        if props.get("disabled") is True:
            continue
        role = _ax_value(child, "role")
        if role in CLICK_ROLES or role in EDITABLE_ROLES or role == "combobox":
            return True
    return False


def _base_candidate(
    node: Mapping[str, Any],
    by_id: Mapping[str, Mapping[str, Any]],
    operation: str,
    *,
    frame_id: str | None,
) -> dict[str, Any]:
    props = _properties(node)
    name = _ax_value(node, "name")
    description = _ax_value(node, "description")
    candidate = {
        "operation": operation,
        "axNodeId": str(node["nodeId"]),
        "backendDOMNodeId": node.get("backendDOMNodeId"),
        "role": _ax_value(node, "role"),
        "name": name.strip() if isinstance(name, str) else "",
        "description": description.strip() if isinstance(description, str) else description,
        "states": props,
        "context": _context_text(node, by_id),
    }
    if frame_id is not None:
        candidate["frameId"] = frame_id
    value = _ax_value(node, "value")
    if value is not None:
        candidate["value"] = value
    return candidate


def project_ax_candidates(
    tree: Mapping[str, Any],
    *,
    dom_metadata: Mapping[int | str, Mapping[str, Any]] | None = None,
    frame_id: str | None = None,
    require_dom_metadata: bool = False,
) -> list[dict[str, Any]]:
    """Project one Chromium AX tree into ephemeral operation-specific candidates.

    dom_metadata is optional browser-owned metadata keyed by backendDOMNodeId. AX alone
    cannot safely distinguish some HTML controls, notably password/file inputs, so a
    production candidate projector must provide DOM metadata and set require_dom_metadata
    before granting effects.
    """

    raw_nodes = tree.get("nodes")
    if not isinstance(raw_nodes, list):
        raise ValueError("AX tree must contain a nodes list")
    by_id = {
        str(node["nodeId"]): node
        for node in raw_nodes
        if isinstance(node, Mapping) and node.get("nodeId") is not None
    }
    dom_metadata = dom_metadata or {}

    candidates: list[dict[str, Any]] = []
    for node in raw_nodes:
        if not isinstance(node, Mapping) or node.get("nodeId") is None:
            continue
        if node.get("ignored") is True:
            continue
        backend = node.get("backendDOMNodeId")
        if not isinstance(backend, int):
            continue
        props = _properties(node)
        if props.get("disabled") is True:
            continue

        dom = _dom_metadata_for(dom_metadata, backend)
        if require_dom_metadata and not dom:
            continue
        if _unsafe_input(dom):
            continue

        role = _ax_value(node, "role")

        if _contenteditable(dom):
            if props.get("readonly") is not True:
                candidates.append(_base_candidate(node, by_id, "FILL", frame_id=frame_id))
            candidates.append(_base_candidate(node, by_id, "CLICK", frame_id=frame_id))
            continue

        if _summary(dom):
            candidates.append(_base_candidate(node, by_id, "CLICK", frame_id=frame_id))
            continue

        if role in CLICK_ROLES:
            if role == "gridcell" and _has_actionable_descendant(node, by_id):
                continue
            candidates.append(_base_candidate(node, by_id, "CLICK", frame_id=frame_id))
            continue

        if role in EDITABLE_ROLES:
            if props.get("readonly") is not True:
                candidates.append(_base_candidate(node, by_id, "FILL", frame_id=frame_id))
            candidates.append(_base_candidate(node, by_id, "CLICK", frame_id=frame_id))
            continue

        if role == "combobox":
            if props.get("editable"):
                candidates.append(_base_candidate(node, by_id, "FILL", frame_id=frame_id))
                candidates.append(_base_candidate(node, by_id, "CLICK", frame_id=frame_id))
                continue
            for option in _descendants(str(node["nodeId"]), by_id):
                if _ax_value(option, "role") != "option":
                    continue
                option_props = _properties(option)
                if option.get("ignored") is True or option_props.get("disabled") is True:
                    continue
                if option_props.get("selected") is True:
                    continue
                candidate = _base_candidate(node, by_id, "SELECT", frame_id=frame_id)
                option_name = _ax_value(option, "name")
                candidate["optionName"] = (
                    option_name.strip() if isinstance(option_name, str) else ""
                )
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
        "frameId": candidate.get("frameId"),
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
        and candidate.get("frameId") == witness.get("frameId")
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
