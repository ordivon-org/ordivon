from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import jsonschema


class StandardsInventoryError(RuntimeError):
    """Configuration/schema validation failure for the quantitative component inventory."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise StandardsInventoryError(f"cannot load JSON: {path}") from exc
    if not isinstance(value, dict):
        raise StandardsInventoryError(f"expected object: {path}")
    return value


def validate_inventory(*, inventory_path: Path, schema_path: Path) -> dict[str, Any]:
    inventory = load_json(inventory_path)
    schema = load_json(schema_path)
    try:
        jsonschema.Draft202012Validator(schema).validate(inventory)
    except jsonschema.ValidationError as exc:
        raise StandardsInventoryError(
            f"inventory schema validation failed: {exc.message}"
        ) from exc
    ids = [row["id"] for row in inventory["components"]]
    if len(ids) != len(set(ids)):
        raise StandardsInventoryError("component ids must be unique")
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    args = parser.parse_args()
    inventory = validate_inventory(
        inventory_path=args.inventory,
        schema_path=args.schema,
    )
    print(json.dumps({
        "standing": "PASS",
        "framework": inventory["framework"]["name"],
        "componentCount": len(inventory["components"]),
        "modelCount": sum(
            1 for row in inventory["components"]
            if row["sr26ModelStanding"] == "MODEL"
        ),
        "retiredCount": sum(
            1 for row in inventory["components"]
            if row["status"] == "RETIRED"
        ),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
