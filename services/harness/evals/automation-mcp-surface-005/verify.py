#!/usr/bin/env python3
"""Read-only MCP installed-vs-candidate source interface subtraction diagnostic.

The live baseline is supplied as a names-only JSON capture from *tools/list*.
Both Python sources are inspected by AST only; they are never imported or run.
An unchanged static surface is NOT proof of actual MCP inputSchema, downstream
consumer compatibility, runtime readiness, user consent, or release approval.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys


class ContractIndeterminate(ValueError):
    """Evidence cannot establish the candidate's static MCP surface."""


def _checked_name(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 128
        or value != value.strip()
        or any(ch.isspace() for ch in value)
    ):
        raise ContractIndeterminate("invalid or ambiguous MCP tool name")
    return value


def _tool_name_from_decorator(decorator: ast.expr) -> str | None:
    if not (
        isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Attribute)
        and decorator.func.attr == "tool"
        and isinstance(decorator.func.value, ast.Name)
        and decorator.func.value.id == "server"
    ):
        return None
    # Unpacked runtime registration metadata can change permissions, naming
    # and transport schemas without changing static names; no safe AST proof.
    if any(kw.arg is None for kw in decorator.keywords):
        raise ContractIndeterminate("dynamic @server.tool registration options")
    keyword_names = [kw.value for kw in decorator.keywords if kw.arg == "name"]
    if len(keyword_names) != 1 or not isinstance(keyword_names[0], ast.Constant):
        raise ContractIndeterminate("dynamic or missing @server.tool(name=...)")
    return _checked_name(keyword_names[0].value)


def _source_projection(
    code: str,
) -> tuple[frozenset[str], frozenset[str], dict[str, tuple[str, ...]], dict[str, tuple[str, str | None]]]:
    """AST-only declared shapes. Never import, execute or expose defaults/annotations."""
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        raise ContractIndeterminate(f"candidate source cannot be parsed: {error.msg}") from error

    names: list[str] = []
    tool_shapes: dict[str, tuple[str, ...]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                name = _tool_name_from_decorator(decorator)
                if name is not None:
                    names.append(name)
                    tool_shapes[name] = (
                        "async" if isinstance(node, ast.AsyncFunctionDef) else "sync",
                        ast.dump(node.args, include_attributes=False),
                        ast.dump(node.returns, include_attributes=False)
                        if node.returns is not None else "UNANNOTATED_RETURN",
                        repr(sorted(
                            (kw.arg, ast.dump(kw.value, include_attributes=False))
                            for kw in decorator.keywords if kw.arg != "name"
                        )),
                    )
    if not names or len(names) != len(set(names)):
        raise ContractIndeterminate("no static registrations or duplicate MCP tool name")

    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "CampaignSpecInput"]
    if len(classes) != 1:
        raise ContractIndeterminate("CampaignSpecInput declaration is absent or duplicated")
    fields: list[str] = []
    field_shapes: dict[str, tuple[str, str | None]] = {}
    for member in classes[0].body:
        if isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
            fields.append(member.target.id)
            field_shapes[member.target.id] = (
                ast.dump(member.annotation, include_attributes=False),
                ast.dump(member.value, include_attributes=False)
                if member.value is not None else None,
            )
    if not fields or len(fields) != len(set(fields)):
        raise ContractIndeterminate("CampaignSpecInput has no statically named fields")
    return frozenset(names), frozenset(fields), tool_shapes, field_shapes


def inspect_source(code: str) -> tuple[frozenset[str], frozenset[str]]:
    """Retain existing two-set API for source-only tool and field queries."""
    names, fields, _, _ = _source_projection(code)
    return names, fields


def capture_live_names(value: object) -> frozenset[str]:
    """Accept only names from an external official MCP *tools/list* capture."""
    if not isinstance(value, list) or not value:
        raise ContractIndeterminate("live tools/list must be a non-empty JSON array")
    names = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"name"}:
            raise ContractIndeterminate("live snapshot must contain names only, no tool payloads")
        names.append(_checked_name(item["name"]))
    if len(names) != len(set(names)):
        raise ContractIndeterminate("live tools/list contains duplicate names")
    return frozenset(names)


def compare(live_names: frozenset[str], installed_text: str, candidate_text: str) -> dict[str, object]:
    installed, installed_fields, installed_tools, installed_shapes = _source_projection(installed_text)
    candidate, candidate_fields, candidate_tools, candidate_shapes = _source_projection(candidate_text)
    installed_live_diff = sorted(live_names.symmetric_difference(installed))
    removed = sorted(live_names - candidate)
    added = sorted(candidate - live_names)
    removed_fields = sorted(installed_fields - candidate_fields)
    changed_tools = sorted(
        name for name in installed & candidate
        if installed_tools[name] != candidate_tools[name]
    )
    changed_fields = sorted(
        name for name in installed_fields & candidate_fields
        if installed_shapes[name] != candidate_shapes[name]
    )
    if installed_live_diff:
        status = "INDETERMINATE_INSTALLED_SOURCE_LIVE_MISMATCH"
    elif removed or removed_fields:
        status = "BREAKING_NAME_OR_FIELD_SUBTRACTION_DETECTED"
    elif changed_tools or changed_fields:
        # Source differences are enough to HOLD, not proof the actual MCP
        # inputSchema or natural consumers changed in a breaking way.
        status = "INDETERMINATE_TOOL_OR_FIELD_SHAPE_CHANGED"
    else:
        status = "NO_NAME_OR_FIELD_SUBTRACTION_DETECTED_NOT_RELEASE_APPROVED"
    return {
        "schemaVersion": 1,
        "kind": "ordivon.automation-mcp-surface-subtraction-diagnostic",
        "status": status,
        "liveToolCount": len(live_names),
        "installedSourceToolCount": len(installed),
        "candidateSourceToolCount": len(candidate),
        "installedLiveDisagreement": installed_live_diff,
        "removedLiveToolNames": removed,
        "candidateAddedToolNames": added,
        "removedCampaignSpecFields": removed_fields,
        "changedToolSignatures": changed_tools,
        "changedCampaignFieldShapes": changed_fields,
        "releaseQualified": False,
        "callerUsageProven": False,
        "transportAndSemanticCompatibilityProven": False,
        "truthBoundary": (
            "Only observed live MCP names, static tool parameter/return/decorator shapes and "
            "CampaignSpecInput annotated/default shapes. Static differences mandate "
            "UNKNOWN until official MCP inputSchema/consumers validate them; equality "
            "does not prove schemas or semantics. No candidate import, calls, Provider "
            "SEND, production effect, or consumer usage was measured."
        ),
    }


def _read_text(path: Path, limit: int = 1_048_576) -> str:
    if not path.is_file() or path.stat().st_size > limit:
        raise ContractIndeterminate("source or baseline is missing or oversized")
    return path.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-names-json", required=True, type=Path)
    parser.add_argument("--installed-source", required=True, type=Path)
    parser.add_argument("--candidate-source", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        live = capture_live_names(json.loads(_read_text(args.live_names_json)))
        result = compare(
            live,
            _read_text(args.installed_source),
            _read_text(args.candidate_source),
        )
    except (ContractIndeterminate, OSError, UnicodeError, ValueError) as error:
        print(json.dumps({
            "kind": "ordivon.automation-mcp-surface-subtraction-diagnostic",
            "status": "INDETERMINATE",
            "releaseQualified": False,
            "reason": str(error)[:400],
        }, sort_keys=True))
        return 3
    print(json.dumps(result, sort_keys=True))
    return 2 if result["status"] == "BREAKING_NAME_OR_FIELD_SUBTRACTION_DETECTED" else (
        3 if result["status"].startswith("INDETERMINATE") else 0
    )


if __name__ == "__main__":
    sys.exit(main())
