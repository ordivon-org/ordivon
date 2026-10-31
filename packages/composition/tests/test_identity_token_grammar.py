"""Composition identity grammars reject trailing data at the schema boundary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

SCHEMAS = Path(__file__).parents[1] / "src" / "ordivon_composition" / "schemas"


def token_contracts() -> list[tuple[str, dict, str]]:
    contracts = []
    for path in sorted(SCHEMAS.glob("*.schema.json")):
        schema = json.loads(path.read_text())
        for name, valid in (("sha256", "sha256:" + "0" * 64), ("identifier", "gate:valid")):
            if name in schema.get("$defs", {}):
                contracts.append((path.name + ":" + name, schema["$defs"][name], valid))
    gate = json.loads((SCHEMAS / "composition-gate-result-v1.schema.json").read_text())
    contracts.extend(
        [
            ("gate:evidence", gate["properties"]["evidenceRefs"]["items"], "evidence:valid"),
            ("gate:digest", gate["properties"]["manifestDigest"], "sha256:" + "0" * 64),
        ]
    )
    interface = json.loads((SCHEMAS / "interface-compatibility-result-v1.schema.json").read_text())
    contracts.append(
        (
            "interface:evidence",
            interface["properties"]["evidenceRef"],
            "interface-compatibility:sha256:" + "0" * 64,
        )
    )
    return contracts


@pytest.mark.parametrize("label,schema,valid", token_contracts())
@pytest.mark.parametrize("suffix", ["", "\n", "\r", "\r\n", "\u2028", "\u2029"])
def test_identity_token_contract_rejects_trailing_line_breaks(
    label: str,
    schema: dict,
    valid: str,
    suffix: str,
) -> None:
    expected = suffix == ""
    assert Draft202012Validator(schema).is_valid(valid + suffix) is expected, label
