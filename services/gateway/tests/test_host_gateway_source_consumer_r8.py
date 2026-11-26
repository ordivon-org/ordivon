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


def test_integer_input_direction_preserves_exact_boundary_and_unknown():
    mod = _load()
    host = {
        "work.get": _tool(
            {
                "revision": {"type": "integer", "minimum": 1, "maximum": 9007199254740991},
                "maxBytes": {"type": "integer"},
                "cursor": {"anyOf": [{"type": "null"}, {"type": "integer", "minimum": 0}]},
                "complex": {"type": "integer", "multipleOf": 2},
            },
            [],
        )
    }
    gateway = {
        "work.get": _tool(
            {
                "revision": {"type": "integer", "minimum": 1, "maximum": 9007199254740991},
                "maxBytes": {"type": "integer", "minimum": 16384, "maximum": 4194304},
                "cursor": {"type": "integer", "minimum": 0},
                "complex": {"type": "integer"},
            },
            [],
        )
    }
    report = mod.summarize(host, gateway)
    rows = {row["property"]: row for row in report["sourceIntegerInputComparisons"]}
    assert rows["revision"]["relation"] == "EQUAL"
    assert rows["maxBytes"]["relation"] == "GATEWAY_STRICTER"
    assert rows["maxBytes"]["hostOnlyWitness"] == 16383
    assert rows["cursor"]["relation"] == "GATEWAY_STRICTER"
    assert rows["cursor"]["hostOnlyWitness"] is None
    assert rows["cursor"]["hasHostOnlyWitness"] is True
    assert rows["complex"]["relation"] == "UNKNOWN"
    assert report["installedConsumersQualified"] is None


def test_integer_input_direction_finite_interval_oracle():
    import itertools

    mod = _load()
    spans = [(lo, hi) for lo in range(-2, 3) for hi in range(lo, 3)]
    for (lo, hi), (lo2, hi2), n1, n2 in itertools.product(
        spans, spans, (False, True), (False, True)
    ):

        def schema(a, b, nullable):
            integer = {"type": "integer", "minimum": a, "maximum": b}
            return {"anyOf": [integer, {"type": "null"}]} if nullable else integer

        old = set(range(lo, hi + 1)) | ({None} if n1 else set())
        new = set(range(lo2, hi2 + 1)) | ({None} if n2 else set())
        row = mod.compare_integer_input(schema(lo, hi, n1), schema(lo2, hi2, n2))
        expected = (
            "EQUAL"
            if old == new
            else "GATEWAY_STRICTER"
            if new < old
            else "GATEWAY_WIDER"
            if old < new
            else "INCOMPARABLE"
        )
        assert row["relation"] == expected
        assert row["hasHostOnlyWitness"] == bool(old - new)
        assert row["hasGatewayOnlyWitness"] == bool(new - old)
        if old - new:
            assert row["hostOnlyWitness"] in old - new
        if new - old:
            assert row["gatewayOnlyWitness"] in new - old


def test_integer_input_comparison_does_not_claim_unsupported_schema():
    mod = _load()
    integer = {"type": "integer"}
    for bad in (
        {"type": "integer", "minimum": True},
        {"type": "integer", "minimum": 1.5},
        {"type": "integer", "minimum": 2, "maximum": 1},
        {"type": "integer", "exclusiveMinimum": 1},
        {"type": "integer", "enum": [1, 2]},
        {"anyOf": [integer, {"type": "string"}]},
        {"type": "integer", "default": "1"},
    ):
        assert mod.compare_integer_input(bad, integer)["relation"] == "UNKNOWN"
    assert (
        mod.compare_integer_input(
            {"type": "integer", "default": 0}, {"type": "integer", "default": 1}
        )["defaultRelation"]
        == "DIFFERENT"
    )
