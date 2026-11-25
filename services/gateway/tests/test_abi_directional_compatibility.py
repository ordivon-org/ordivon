"""A schema-level witness is not a proof of deployed consumer compatibility."""

from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

SCRIPT = Path(__file__).resolve().parents[1] / "packaging/verify_tool_surface.py"
spec = importlib.util.spec_from_file_location("gateway_abi_directional", SCRIPT)
assert spec and spec.loader
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def tool(schema, side):
    return [
        {
            "name": "probe",
            "inputSchema": schema if side == "input" else {"type": "object"},
            "outputSchema": schema if side == "output" else None,
        }
    ]


def schema(**kwargs):
    return {
        "type": "object",
        "properties": {"existing": {"type": "string"}},
        "required": ["existing"],
        **kwargs,
    }


@pytest.mark.parametrize(
    ("side", "old_extra", "new_extra", "witness"),
    [
        (
            "input",
            {},
            {"additional": {"type": "integer"}},
            {"existing": "ok", "additional": "old-valid"},
        ),
        (
            "output",
            {"additionalProperties": False},
            {"additional": {"type": "integer"}},
            {"existing": "ok", "additional": 1},
        ),
        (
            "input",
            {"maxProperties": 2},
            {"additional": {"type": "integer"}},
            {"existing": "ok", "additional": "old-valid"},
        ),
        (
            "output",
            {"additionalProperties": {"type": "string"}},
            {"additional": {"type": "integer"}},
            {"existing": "ok", "additional": 1},
        ),
    ],
)
def test_shape_changes_have_real_directional_counterexamples(side, old_extra, new_extra, witness):
    old = schema(**old_extra)
    new = deepcopy(old)
    new["properties"].update(new_extra)
    first, second = (old, new) if side == "input" else (new, old)
    # For a closed old output, a candidate retaining additionalProperties=false
    # explicitly accepts the newly declared property.
    assert Draft202012Validator(first).is_valid(witness)
    assert not Draft202012Validator(second).is_valid(witness)
    assert verifier.compare_native_tool_contracts(tool(old, side), tool(new, side))


@pytest.mark.parametrize("side", ["input", "output"])
def test_malformed_schema_cannot_qualify(side):
    old = schema()
    new = deepcopy(old)
    new["properties"]["existing"]["type"] = "unknown-wire-type"
    assert verifier.compare_native_tool_contracts(tool(old, side), tool(new, side))
    # Equal invalid schemas must not pass merely by structural equality.
    assert verifier.compare_native_tool_contracts(tool(new, side), tool(new, side))


def test_new_output_schema_is_not_automatically_compatible():
    assert verifier.compare_native_tool_contracts(tool(None, "output"), tool(schema(), "output"))


def test_closed_input_optional_addition_preserves_old_json_domain():
    old = schema(additionalProperties=False)
    new = deepcopy(old)
    new["properties"]["optional"] = {"type": "integer"}
    assert verifier.compare_native_tool_contracts(tool(old, "input"), tool(new, "input")) == []


def test_open_output_optional_addition_preserves_old_json_domain():
    old = schema()
    new = deepcopy(old)
    new["properties"]["optional"] = {"type": "integer"}
    assert verifier.compare_native_tool_contracts(tool(old, "output"), tool(new, "output")) == []


def test_qualified_directional_rule_against_bounded_json_domain():
    import itertools

    domains = [None, False, 0, 1, "x", [], {}]
    values = [{}]
    for keys in (
        ("existing",),
        ("optional",),
        ("alien",),
        ("existing", "optional"),
        ("existing", "alien"),
        ("optional", "alien"),
        ("existing", "optional", "alien"),
    ):
        values.extend(
            dict(zip(keys, items, strict=True))
            for items in itertools.product(domains, repeat=len(keys))
        )
    accepted = 0
    rejected = 0
    for side, extra, typ, required in itertools.product(
        ("input", "output"),
        (False, True, {"type": "string"}),
        ("integer", "string", "boolean"),
        (False, True),
    ):
        old = schema(additionalProperties=extra)
        new = deepcopy(old)
        new["properties"]["optional"] = {"type": typ}
        if required:
            new["required"].append("optional")
        issues = verifier.compare_native_tool_contracts(tool(old, side), tool(new, side))
        if issues:
            rejected += 1
            continue
        accepted += 1
        source, target = (old, new) if side == "input" else (new, old)
        a, b = Draft202012Validator(source), Draft202012Validator(target)
        assert all(not a.is_valid(v) or b.is_valid(v) for v in values), (side, extra, typ, required)
    assert accepted == 9 and rejected == 27


def test_reference_sensitive_addition_is_not_proven_by_property_sets():
    old = schema(additionalProperties=False)
    old["properties"]["existing"] = {"$ref": "#/$defs/Value"}
    old["$defs"] = {"Value": {"type": "string"}}
    new = deepcopy(old)
    new["properties"]["optional"] = {"type": "integer", "$id": "https://fixture.test/new"}
    assert verifier.compare_native_tool_contracts(tool(old, "input"), tool(new, "input"))


@pytest.mark.parametrize(
    "raw",
    [
        b'[{"name":"x","name":"y","inputSchema":{"type":"object"}}]',
        b'[{"name":"x","inputSchema":{"type":"object","minimum":NaN}}]',
        b'[{"name":"x","inputSchema":{"type":"object","minimum":1e999}}]',
        b'[{"name":"x","inputSchema":{"type":"object","title":"\xff"}}]',
    ],
)
def test_native_compare_cli_rejects_ambiguous_json(tmp_path, raw):
    import json
    import subprocess
    import sys

    left, right = tmp_path / "left.json", tmp_path / "right.json"
    left.write_bytes(raw)
    right.write_text(json.dumps(tool(schema(), "input")), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--compare-native", str(left), str(right)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["compatible"] is False


def test_native_compare_uses_locked_candidate_not_os_interpreter():
    source = (SCRIPT.parent / "install_release.sh").read_text(encoding="utf-8")
    needle = 'if "$RELEASE/.venv/bin/python" "$RELEASE/packaging/verify_tool_surface.py" --compare-native'
    assert needle in source
    assert source.index(needle) < source.index('ln -sfn "releases/$COMMIT"')


def test_non_object_root_is_not_a_qualified_mcp_schema():
    malformed = {"type": "string"}
    for side in ("input", "output"):
        assert verifier.compare_native_tool_contracts(tool(malformed, side), tool(malformed, side))


def test_read_bound_and_escaped_lone_surrogate(tmp_path):
    path = tmp_path / "contract.json"
    path.write_bytes(b" " * (verifier.MAX_CONTRACT_BYTES + 1))
    with pytest.raises(ValueError, match="bounded size"):
        verifier._read_json(path)
    path.write_bytes(b'{"title":"\\ud800"}')
    with pytest.raises(ValueError):
        verifier._read_json(path)
