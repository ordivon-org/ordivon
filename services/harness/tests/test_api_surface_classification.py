from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _public_exports() -> set[str]:
    tree = ast.parse((ROOT / "src/ordivon_harness/api.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        ):
            return {
                item.value
                for item in node.value.elts
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            }
    raise AssertionError("ordivon_harness.api has no __all__")


def test_api_classification_covers_each_stable_export_exactly_once() -> None:
    classification = json.loads(
        (ROOT / "docs/api-surfaces-r1.json").read_text(encoding="utf-8")
    )
    categories = (
        classification["application"],
        classification["integration"],
        classification["lowLevelCompatibility"],
    )
    flattened = [name for category in categories for name in category]

    assert len(flattened) == len(set(flattened))
    assert set(flattened) == _public_exports()
    assert classification["truthRole"] == "compatibility-classification-only"
    assert classification["authorityBoundary"] == (
        "classification-only-no-export-removal-no-new-authority"
    )
