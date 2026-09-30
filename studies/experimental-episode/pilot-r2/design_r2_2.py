from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Any
from anc_canonical import canonical_digest

HERE = Path(__file__).resolve()
BASE = HERE.with_name("design_r2_1.py")


def _load():
    spec = importlib.util.spec_from_file_location(
        "experimental_fabric_r21_design_shared", BASE
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load R2.1 shared design")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _revise(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _revise(v) for k, v in value.items() if k != "scheduleDigest"}
    if isinstance(value, list):
        return [_revise(v) for v in value]
    if isinstance(value, str):
        return value.replace("r2.1", "r2.2")
    return value


def _seal(value: dict[str, Any]) -> dict[str, Any]:
    revised = _revise(value)
    revised["designRevision"] = "r2.2"
    revised["scheduleDigest"] = canonical_digest(revised)
    return revised


def compile_balanced_calibration_schedule(manifest: dict[str, Any]) -> dict[str, Any]:
    return _seal(_load().compile_balanced_calibration_schedule(manifest))


def compile_balanced_inferential_schedule(
    manifest: dict[str, Any], *args, **kwargs
) -> dict[str, Any]:
    return _seal(
        _load().compile_balanced_inferential_schedule(manifest, *args, **kwargs)
    )
