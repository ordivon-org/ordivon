"""Pure metric topology and tolerance checks for bounded STEP solid observations."""

from __future__ import annotations

import math
from typing import Any


def finite_number(value: Any) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def contract_failures(c: Any) -> list[str]:
    if not isinstance(c, dict):
        return ["object contract must be a JSON object"]
    fs = []
    if c.get("schemaVersion") != 1 or c.get("kind") != "cad-step-solid-contract-v1":
        fs.append("object contract identity/version is not cad-step-solid-contract-v1")
    if c.get("units") != "mm":
        fs.append("R1 units must be mm")
    topology = c.get("topology")
    if not isinstance(topology, dict):
        fs.append("contract.topology must be an object")
    else:
        for k in ("solids", "faces", "edges"):
            value = topology.get(k)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                fs.append(f"contract.topology.{k} must be a positive integer")
    bbox = c.get("bboxMm")
    if not isinstance(bbox, dict):
        fs.append("contract.bboxMm must be an object")
    else:
        for k in ("xmin", "ymin", "zmin", "xmax", "ymax", "zmax"):
            value = bbox.get(k)
            if not finite_number(value):
                fs.append(f"contract.bboxMm.{k} must be a finite number")
    for k in ("volumeMm3", "geometryToleranceMm", "volumeToleranceMm3"):
        value = c.get(k)
        if not finite_number(value) or float(value) <= 0:
            fs.append(f"contract.{k} must be a positive finite number")
    return fs


def compare(obs: dict[str, Any], c: dict[str, Any], label: str) -> list[str]:
    issues = []
    if obs.get("valid") is not True:
        issues.append(f"{label} shape is not valid")
    for key in ("solids", "faces", "edges"):
        value = obs.get(key)
        if type(value) is not int or value != c["topology"][key]:
            issues.append(f"{label} topology {key} differs from contract")
    bbox = obs.get("bboxMm")
    bbox = bbox if isinstance(bbox, dict) else {}
    for key in ("xmin", "ymin", "zmin", "xmax", "ymax", "zmax"):
        expected = c["bboxMm"][key]
        value = bbox.get(key)
        if not finite_number(value) or abs(value - expected) > c["geometryToleranceMm"]:
            issues.append(f"{label} bbox {key} differs from contract")
    value = obs.get("volumeMm3")
    if not finite_number(value) or abs(value - c["volumeMm3"]) > c["volumeToleranceMm3"]:
        issues.append(f"{label} volume differs from contract")
    return issues


def compare_readers(left: dict[str, Any], right: dict[str, Any], c: dict[str, Any]) -> list[str]:
    issues = []
    a, b = left.get("bboxMm"), right.get("bboxMm")
    a = a if isinstance(a, dict) else {}
    b = b if isinstance(b, dict) else {}
    for key in ("xmin", "ymin", "zmin", "xmax", "ymax", "zmax"):
        x, y = a.get(key), b.get(key)
        if not finite_number(x) or not finite_number(y) or abs(x - y) > c["geometryToleranceMm"]:
            issues.append(f"cross-reader bbox {key} differs")
    x, y = left.get("volumeMm3"), right.get("volumeMm3")
    if not finite_number(x) or not finite_number(y) or abs(x - y) > c["volumeToleranceMm3"]:
        issues.append("cross-reader volume differs")
    return issues
