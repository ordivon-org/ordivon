"""Source vs Rust-only MCP extension declarations are separate kinds of evidence."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

AUDITOR = Path(__file__).resolve().parents[1] / "rust" / "tools" / "audit_mcp_surface.py"
SPEC = importlib.util.spec_from_file_location("host_mcp_source_auditor", AUDITOR)
assert SPEC is not None and SPEC.loader is not None
auditor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(auditor)

TOOL = "work.engagement.advance"


def typed_extension() -> dict:
    return {
        "name": TOOL,
        "inputSchema": {
            "type": "object",
            "properties": {"workRef": {"type": "string"}, "action": {"type": "string"}},
            "required": ["workRef", "action"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "kind": {"const": "ordivon.host-work-engagement"},
                "admission": {"type": "string"},
            },
            "required": ["kind", "admission"],
        },
    }


def test_unreviewed_additive_mcp_tool_must_not_masquerade_as_python_parity() -> None:
    rust = {TOOL: typed_extension()}
    with pytest.raises(RuntimeError, match="explicitly reviewed"):
        auditor.require_explicit_native_extensions([TOOL], [], rust)
    with pytest.raises(RuntimeError, match="explicitly reviewed"):
        auditor.require_explicit_native_extensions([TOOL], ["work.get"], rust)
    with pytest.raises(RuntimeError, match="explicitly reviewed"):
        auditor.require_explicit_native_extensions([TOOL], [TOOL, TOOL], rust)


def test_native_tool_requires_actual_typed_input_and_output_schema() -> None:
    rust = {TOOL: typed_extension()}
    auditor.require_explicit_native_extensions([TOOL], [TOOL], rust)
    for field in ("inputSchema", "outputSchema"):
        invalid = typed_extension()
        del invalid[field]
        with pytest.raises(RuntimeError, match=field):
            auditor.require_explicit_native_extensions([TOOL], [TOOL], {TOOL: invalid})
        invalid = typed_extension()
        invalid[field] = {"type": "object", "additionalProperties": True}
        with pytest.raises(RuntimeError, match=field):
            auditor.require_explicit_native_extensions([TOOL], [TOOL], {TOOL: invalid})
