#!/usr/bin/env python3
"""Bounded KiCad PCB verification using KiCad-native DRC and manufacturing export.

This verifier deliberately does not infer electrical intent, schematic parity, signal
integrity, manufacturability, safety, or board fitness. It proves only the exact PCB
bytes against one request-bound mechanical contract through the installed KiCad CLI.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

KICAD = Path("/usr/bin/kicad-cli")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_fact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256_file(path), "size": path.stat().st_size}


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False, timeout=90)


def number_with_unit(value: Any, unit: str) -> float | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\s*([-+]?[0-9]+(?:\.[0-9]+)?)\s*" + re.escape(unit) + r"\s*", value)
    return float(match.group(1)) if match else None


def contract_failures(contract: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(contract, dict):
        return ["object contract must be a JSON object"]
    if contract.get("schemaVersion") != 1 or contract.get("kind") != "eda-kicad-pcb-contract-v1":
        failures.append("object contract identity/version is not eda-kicad-pcb-contract-v1")
    board = contract.get("board")
    if not isinstance(board, dict):
        failures.append("contract.board must be an object")
    else:
        for key in ("hasOutline", "widthMm", "heightMm", "throughHolePads", "minDrillDiameterMm"):
            if key not in board:
                failures.append(f"contract.board.{key} is required")
    outputs = contract.get("manufacturingOutputs")
    if not isinstance(outputs, dict):
        failures.append("contract.manufacturingOutputs must be an object")
    else:
        layers = outputs.get("gerberLayers")
        if not isinstance(layers, list) or not layers or not all(isinstance(x, str) and x for x in layers):
            failures.append("contract.manufacturingOutputs.gerberLayers must be a non-empty string list")
        if outputs.get("excellon") is not True:
            failures.append("R1 requires Excellon drill export")
    drc = contract.get("drc")
    if not isinstance(drc, dict) or drc.get("severity") != "error" or drc.get("requireZeroViolations") is not True:
        failures.append("R1 requires zero KiCad error-severity DRC violations")
    return failures


def verify_kicad_pcb(subject: Path, contract_path: Path, evidence_directory: Path) -> dict[str, Any]:
    evidence_directory.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    observations: list[str] = []
    if not subject.is_file():
        return {"status": "FAIL", "failures": ["PCB subject is not a regular file"]}
    if not contract_path.is_file():
        return {"status": "FAIL", "failures": ["PCB object contract is not a regular file"]}
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except Exception as error:
        return {"status": "FAIL", "failures": [f"PCB object contract JSON unreadable: {error}"]}
    failures.extend(contract_failures(contract))
    if not KICAD.is_file():
        failures.append("required external tool unavailable: /usr/bin/kicad-cli")
    if failures:
        return {"status": "FAIL", "failures": failures}

    version = run([str(KICAD), "version"])
    version_text = (version.stdout or version.stderr).strip().splitlines()[0] if (version.stdout or version.stderr).strip() else ""

    drc_path = evidence_directory / "drc.json"
    drc_proc = run([
        str(KICAD), "pcb", "drc", "--format", "json", "--severity-error",
        "--exit-code-violations", "--output", str(drc_path), str(subject),
    ])
    drc: dict[str, Any] = {}
    if drc_path.is_file():
        try:
            drc = json.loads(drc_path.read_text(encoding="utf-8"))
        except Exception as error:
            failures.append(f"KiCad DRC JSON unreadable: {error}")
    else:
        failures.append("KiCad DRC did not produce JSON evidence")
    violations = drc.get("violations") if isinstance(drc, dict) else None
    if drc_proc.returncode != 0 or not isinstance(violations, list) or violations:
        failures.append("KiCad DRC reported error-level violations")

    stats_path = evidence_directory / "stats.json"
    stats_proc = run([str(KICAD), "pcb", "export", "stats", "--format", "json", "-o", str(stats_path), str(subject)])
    stats: dict[str, Any] = {}
    if stats_proc.returncode != 0 or not stats_path.is_file():
        failures.append("KiCad board statistics export failed")
    else:
        try:
            stats = json.loads(stats_path.read_text(encoding="utf-8"))
        except Exception as error:
            failures.append(f"KiCad board statistics JSON unreadable: {error}")

    board_contract = contract["board"]
    board_stats = stats.get("board", {}) if isinstance(stats, dict) else {}
    pads = stats.get("pads", {}) if isinstance(stats, dict) else {}
    if bool(board_stats.get("has_outline")) != bool(board_contract["hasOutline"]):
        failures.append("board outline standing differs from object contract")
    comparisons = [
        ("board width", number_with_unit(board_stats.get("width"), "mm"), float(board_contract["widthMm"]), 0.0002),
        ("board height", number_with_unit(board_stats.get("height"), "mm"), float(board_contract["heightMm"]), 0.0002),
        ("minimum drill diameter", number_with_unit(board_stats.get("min_drill_diameter"), "mm"), float(board_contract["minDrillDiameterMm"]), 0.0002),
    ]
    for name, observed, expected, tolerance in comparisons:
        if observed is None or abs(observed - expected) > tolerance:
            failures.append(f"{name} differs from object contract")
    if int(pads.get("through_hole", -1)) != int(board_contract["throughHolePads"]):
        failures.append("through-hole pad count differs from object contract")

    manufacture = evidence_directory / "manufacturing"
    gerber_dir = manufacture / "gerber"
    drill_dir = manufacture / "drill"
    gerber_dir.mkdir(parents=True, exist_ok=True)
    drill_dir.mkdir(parents=True, exist_ok=True)
    layers = list(contract["manufacturingOutputs"]["gerberLayers"])
    gerber_proc = run([str(KICAD), "pcb", "export", "gerbers", "-o", str(gerber_dir), "--layers", ",".join(layers), str(subject)])
    if gerber_proc.returncode != 0:
        failures.append("KiCad Gerber export failed")
    drill_report = drill_dir / "drill-report.rpt"
    drill_proc = run([
        str(KICAD), "pcb", "export", "drill", "-o", str(drill_dir), "--format", "excellon",
        "--excellon-units", "mm", "--generate-report", "--report-path", str(drill_report), str(subject),
    ])
    if drill_proc.returncode != 0:
        failures.append("KiCad Excellon drill export failed")

    gerber_files = sorted(path for path in gerber_dir.iterdir() if path.is_file() and path.stat().st_size > 0)
    drill_files = sorted(path for path in drill_dir.iterdir() if path.is_file() and path.stat().st_size > 0)
    if len(gerber_files) < len(layers) + 1:  # selected layers plus Gerber job metadata
        failures.append("Gerber export did not materialize the expected layer set plus job metadata")
    if not any(path.suffix.lower() == ".drl" for path in drill_files):
        failures.append("Excellon drill export did not materialize a .drl file")
    if not drill_report.is_file() or drill_report.stat().st_size == 0:
        failures.append("drill report was not materialized")

    if isinstance(drc, dict) and drc.get("ignored_checks"):
        observations.append("KiCad reports ignored/default-disabled checks separately; R1 acceptance binds only error-severity DRC plus the explicit object contract.")

    return {
        "schemaVersion": 1,
        "kind": "artifact-eda-kicad-pcb-verification",
        "status": "PASS" if not failures else "FAIL",
        "subject": file_fact(subject),
        "contract": file_fact(contract_path),
        "tool": {"path": str(KICAD), "sha256": sha256_file(KICAD), "version": version_text},
        "drc": {"exitCode": drc_proc.returncode, "report": file_fact(drc_path) if drc_path.is_file() else None, "violationCount": len(violations) if isinstance(violations, list) else None},
        "stats": {"report": file_fact(stats_path) if stats_path.is_file() else None, "board": board_stats, "pads": pads},
        "manufacturing": {"gerber": [file_fact(x) for x in gerber_files], "drill": [file_fact(x) for x in drill_files]},
        "observations": observations,
        "failures": failures,
        "boundary": "PASS proves the exact KiCad PCB bytes have zero error-severity KiCad DRC violations, match the request-bound mechanical board contract, and produce non-empty selected Gerber plus Excellon outputs under the exact observed KiCad CLI. It does not prove schematic parity, electrical function, signal/power integrity, manufacturing yield, component correctness, safety, regulatory compliance, or caller-domain fitness."
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--evidence-directory", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    evidence = args.evidence_directory or Path("out/artifact-eda-kicad-pcb")
    result = verify_kicad_pcb(args.input.resolve(), args.contract.resolve(), evidence.resolve())
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
