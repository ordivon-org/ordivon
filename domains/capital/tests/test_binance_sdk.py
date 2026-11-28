from __future__ import annotations

import ast
from pathlib import Path

from ordivon_capital.binance_sdk import dump_sdk_model, unwrap_sdk_oneof

ROOT = Path(__file__).resolve().parents[1]
CAPTURE_MODULES = (
    ROOT / "src/ordivon_capital/markets/binance_usdm_public_capture.py",
    ROOT / "src/ordivon_capital/trading/binance_usdm_private_capture.py",
)


class _Model:
    def __init__(self, value):
        self.value = value

    def model_dump(self):
        return self.value


def test_sdk_model_projection_preserves_existing_list_and_model_semantics():
    assert dump_sdk_model(_Model({"symbol": "SNDKUSDT"})) == {"symbol": "SNDKUSDT"}
    assert dump_sdk_model([_Model({"n": 1}), _Model({"n": 2})]) == [
        {"n": 1},
        {"n": 2},
    ]


def test_sdk_oneof_unwrap_is_explicit_and_noninventing():
    assert unwrap_sdk_oneof(_Model({"actual_instance": [{"symbol": "SNDKUSDT"}]})) == [
        {"symbol": "SNDKUSDT"}
    ]
    unchanged = {"symbol": "SNDKUSDT"}
    assert unwrap_sdk_oneof(unchanged) is unchanged


def test_capture_modules_do_not_reintroduce_generated_sdk_representation_helpers():
    offenders = []
    for path in CAPTURE_MODULES:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {
                "_dump",
                "_oneof",
            }:
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}:{node.name}")
        assert '"actual_instance"' not in source, path
    assert offenders == []
