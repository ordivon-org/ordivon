from __future__ import annotations

import copy
import json
import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

import jsonschema

from ordivon_capital.governance.owner_authority import (
    validate_capital_constitution_document,
    validate_delegation_grant_document,
)
from ordivon_capital.risk.risk_capacity_validation import validate_risk_capacity_document

ROOT = Path(__file__).resolve().parents[2]
R3 = ROOT / "planning/r3"
SEED = 20260929
CASES_PER_CONTRACT = 2000


def _paths(value: Any, prefix: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    out = [prefix]
    if isinstance(value, dict):
        for key, child in value.items():
            out.extend(_paths(child, prefix + (key,)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            out.extend(_paths(child, prefix + (index,)))
    return out


def _get(root: Any, path: tuple[Any, ...]) -> Any:
    current = root
    for part in path:
        current = current[part]
    return current


def _set(root: Any, path: tuple[Any, ...], value: Any) -> Any:
    if not path:
        return value
    current = root
    for part in path[:-1]:
        current = current[part]
    current[path[-1]] = value
    return root


def _delete(root: Any, path: tuple[Any, ...]) -> Any:
    if not path:
        return None
    current = root
    for part in path[:-1]:
        current = current[part]
    last = path[-1]
    if isinstance(current, dict):
        current.pop(last, None)
    elif isinstance(current, list) and isinstance(last, int) and 0 <= last < len(current):
        current.pop(last)
    return root


def _mutate(base: dict[str, Any], rng: random.Random, index: int) -> Any:
    value: Any = copy.deepcopy(base)
    paths = _paths(value)
    path = rng.choice(paths)
    current = _get(value, path)
    op = index % 8

    if op == 0:
        return _delete(value, path)
    if op == 1:
        if isinstance(current, dict):
            current["__unexpected__"] = True
            return value
        return _set(value, path, {"__unexpected__": True})
    if op == 2:
        if isinstance(current, list):
            if current:
                current.append(copy.deepcopy(current[0]))
            else:
                current.append("__unexpected__")
            return value
        return _set(value, path, [copy.deepcopy(current), copy.deepcopy(current)])
    if op == 3:
        if isinstance(current, bool):
            return _set(value, path, not current)
        if isinstance(current, (int, float)) and not isinstance(current, bool):
            return _set(value, path, "not-a-number")
        if isinstance(current, str):
            return _set(value, path, "")
        if current is None:
            return _set(value, path, "unexpected")
        return _set(value, path, False)
    if op == 4:
        return _set(value, path, None)
    if op == 5:
        if isinstance(current, str):
            return _set(value, path, current + "__MUTATED__")
        if isinstance(current, list):
            return _set(value, path, [])
        if isinstance(current, dict):
            return _set(value, path, {})
        return _set(value, path, "__MUTATED__")
    if op == 6:
        if isinstance(current, str):
            return _set(value, path, "2026-09-29")
        if isinstance(current, bool):
            return _set(value, path, 1)
        return _set(value, path, "bad value with spaces")
    if isinstance(current, dict):
        keys = list(current)
        if keys:
            current[keys[0]] = copy.deepcopy(current.get(keys[-1]))
        return value
    if isinstance(current, list):
        rng.shuffle(current)
        return value
    if isinstance(current, str):
        return _set(value, path, current.upper())
    return value


def _local_valid(validator: Callable[[Any], Any], doc: Any) -> bool:
    try:
        validator(doc)
    except (TypeError, ValueError, KeyError):
        return False
    return True


def _run_one(
    *,
    label: str,
    schema_path: Path,
    example_path: Path,
    local_validator: Callable[[Any], Any],
    seed_offset: int,
) -> dict[str, Any]:
    schema = json.loads(schema_path.read_text())
    base = json.loads(example_path.read_text())
    format_checker = jsonschema.FormatChecker()
    oracle = jsonschema.Draft202012Validator(schema, format_checker=format_checker)
    if not oracle.is_valid(base):
        raise RuntimeError(f"oracle rejects base example: {label}")
    if not _local_valid(local_validator, base):
        raise RuntimeError(f"local validator rejects base example: {label}")

    rng = random.Random(SEED + seed_offset)
    mismatches: list[dict[str, Any]] = []
    oracle_valid = 0
    local_valid = 0
    for index in range(CASES_PER_CONTRACT):
        case = _mutate(base, rng, index)
        expected = oracle.is_valid(case)
        actual = _local_valid(local_validator, case)
        oracle_valid += int(expected)
        local_valid += int(actual)
        if expected != actual and len(mismatches) < 20:
            mismatches.append(
                {
                    "case": index,
                    "oracleValid": expected,
                    "localValid": actual,
                    "document": case,
                }
            )
    return {
        "label": label,
        "cases": CASES_PER_CONTRACT,
        "oracleValid": oracle_valid,
        "localValid": local_valid,
        "mismatchCount": len(mismatches),
        "mismatches": mismatches,
    }


def main() -> int:
    rows = [
        _run_one(
            label="capital-constitution-v1",
            schema_path=ROOT / "schema/capital-constitution-v1.schema.json",
            example_path=R3 / "examples/constitution-example.json",
            local_validator=validate_capital_constitution_document,
            seed_offset=1,
        ),
        _run_one(
            label="capital-delegation-grant-v1",
            schema_path=ROOT / "schema/capital-delegation-grant-v1.schema.json",
            example_path=R3 / "examples/delegation-example.json",
            local_validator=validate_delegation_grant_document,
            seed_offset=2,
        ),
        _run_one(
            label="capital-risk-capacity-v1",
            schema_path=ROOT / "schema/capital-risk-capacity-v1.schema.json",
            example_path=R3 / "examples/risk-capacity-example.json",
            local_validator=validate_risk_capacity_document,
            seed_offset=3,
        ),
    ]
    total = sum(row["cases"] for row in rows)
    mismatch_count = sum(row["mismatchCount"] for row in rows)
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.r3-resource-governance-validator-differential",
        "seed": SEED,
        "totalCases": total,
        "mismatches": mismatch_count,
        "contracts": rows,
        "standing": "PASS_ZERO_MISMATCH" if mismatch_count == 0 else "FAIL_MISMATCH",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if mismatch_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
