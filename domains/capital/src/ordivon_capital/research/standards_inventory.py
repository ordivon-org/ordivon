from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ordivon_capital.research.quantitative_inventory_validation import (
    QuantitativeInventoryValidationError,
    assert_quantitative_inventory_schema_identity,
    validate_quantitative_component_inventory_document,
)


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
    try:
        assert_quantitative_inventory_schema_identity(schema_path)
        validate_quantitative_component_inventory_document(inventory)
    except (OSError, QuantitativeInventoryValidationError) as exc:
        raise StandardsInventoryError(
            f"inventory schema validation failed: {exc}"
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
        "activeModelCount": sum(
            1 for row in inventory["components"]
            if row["sr26ModelStanding"] == "MODEL" and row["status"] != "RETIRED"
        ),
        "validationRequiredModelCount": sum(
            1 for row in inventory["components"]
            if row["sr26ModelStanding"] == "MODEL" and row["status"] == "VALIDATION_REQUIRED"
        ),
        "retiredModelCount": sum(
            1 for row in inventory["components"]
            if row["sr26ModelStanding"] == "MODEL" and row["status"] == "RETIRED"
        ),
        "nonModelComponentCount": sum(
            1 for row in inventory["components"]
            if row["sr26ModelStanding"] == "NON_MODEL"
        ),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
