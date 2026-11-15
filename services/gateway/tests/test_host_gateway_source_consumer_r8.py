"""Finite source-only MCP consumer surface checks, not a migration approval."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[3] / "tools/repo/check_host_gateway_mcp_consumer_surface.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("host_gateway_source_consumer_r8", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tool(args, required, output=None):
    return {
        "inputSchema": {"type": "object", "properties": args, "required": required},
        "outputSchema": output if output is not None else {"type": "object"},
    }


def test_equal_source_names_and_required_do_not_fake_migration():
    mod = _load()
    host = {
        "work.get": _tool(
            {"workRef": {"type": "string"}},
            ["workRef"],
            {"type": "object", "required": ["workRef", "revision"]},
        ),
        "host.pool.stats": _tool({}, []),
    }
    gateway = {
        "work.get": _tool(
            {"workRef": {"type": "string"}},
            ["workRef"],
            {"type": "object", "additionalProperties": True},
        ),
        "execution.get": _tool({"operationRef": {"type": "string"}}, ["operationRef"]),
    }
    r = mod.summarize(host, gateway)
    assert r["sourceInputNameRequiredParity"] is True
    assert r["hostOnlyTools"] == ["host.pool.stats"]
    assert r["sharedToolCount"] == 1
    assert r["outputSchemaDifferentTools"] == ["work.get"]
    assert r["installedConsumersQualified"] is None
    assert r["securityAuthorized"] is None
    assert r["domainConsumerMigrated"] is None
    assert r["migrationStanding"].startswith("UNKNOWN")


def test_added_required_arg_is_a_real_source_parity_break():
    mod = _load()
    host = {"topic.resume": _tool({"topicRef": {"type": "string"}}, ["topicRef"])}
    gateway = {
        "topic.resume": _tool(
            {
                "topicRef": {"type": "string"},
                "principal": {"type": "string"},
            },
            ["topicRef", "principal"],
        )
    }
    r = mod.summarize(host, gateway)
    assert r["sourceInputNameRequiredParity"] is False
    assert r["inputPropertyOrRequiredDrift"] == ["topic.resume"]


def test_optional_arg_constraints_still_report_schema_difference():
    mod = _load()
    host = {
        "message.search": _tool(
            {"query": {"type": "string"}, "maxBytes": {"type": "integer"}}, ["query"]
        )
    }
    gateway = {
        "message.search": _tool(
            {"query": {"type": "string"}, "maxBytes": {"type": "integer", "minimum": 131072}},
            ["query"],
        )
    }
    r = mod.summarize(host, gateway)
    assert r["sourceInputNameRequiredParity"] is True
    assert r["inputSchemaDifferentTools"] == ["message.search"]
    assert r["migrationStanding"].startswith("UNKNOWN")


def test_empty_or_disjoint_surfaces_are_not_consumer_migration_proof():
    mod = _load()
    r = mod.summarize({"work.get": _tool({}, [])}, {})
    assert r["sharedToolCount"] == 0
    assert r["hostOnlyTools"] == ["work.get"]
    assert r["domainConsumerMigrated"] is None
