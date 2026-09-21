from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT_MACHINE_DOCS = (
    "config/lean_runtime.json",
    "config/quantitative_component_inventory.json",
    "config/external_owner_census.json",
    "config/private_reality_policy.json",
)


def _source_pointers(value):
    text = json.dumps(value)
    return sorted(set(re.findall(r"(?:retired:)?src/ordivon_capital/[A-Za-z0-9_./-]+\.py", text)))


def test_current_machine_readable_source_pointers_exist_or_are_explicitly_retired():
    missing = []
    for rel in CURRENT_MACHINE_DOCS:
        value = json.loads((ROOT / rel).read_text())
        for pointer in _source_pointers(value):
            if pointer.startswith("retired:"):
                continue
            if not (ROOT / pointer).is_file():
                missing.append((rel, pointer))
    assert missing == []


def test_retired_monolith_pointer_is_never_implicit_current_truth():
    offenders = []
    for rel in CURRENT_MACHINE_DOCS:
        value = json.loads((ROOT / rel).read_text())
        for pointer in _source_pointers(value):
            if pointer.startswith("src/ordivon_capital/market/"):
                offenders.append((rel, pointer))
    assert offenders == []
