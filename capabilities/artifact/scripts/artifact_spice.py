#!/usr/bin/env python3
"""Bounded ngspice transient-measure verification for exact SPICE netlist bytes.

ngspice owns circuit parsing and simulation semantics. Artifact binds exact netlist bytes,
exact tool identity, a request-bound minimum data-row floor, and numeric .measure ranges.
It does not infer circuit intent, stability outside the selected analysis, safety, or
physical-hardware behavior.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

NGSPICE = Path("/usr/bin/ngspice")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_fact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": sha256_file(path), "size": path.stat().st_size}


def validate_contract(value: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(value, dict):
        return ["object contract must be a JSON object"]
    if value.get("schemaVersion") != 1 or value.get("kind") != "eda-spice-transient-measure-contract-v1":
        failures.append("object contract identity/version is not eda-spice-transient-measure-contract-v1")
    if not isinstance(value.get("minimumDataRows"), int) or value.get("minimumDataRows", 0) <= 0:
        failures.append("minimumDataRows must be a positive integer")
    measurements = value.get("measurements")
    if not isinstance(measurements, dict) or not measurements:
        failures.append("measurements must be a non-empty object")
    else:
        for name, bounds in measurements.items():
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                failures.append("measurement names must be SPICE-safe identifiers")
                continue
            if not isinstance(bounds, dict) or set(bounds) != {"min", "max"}:
                failures.append(f"measurement {name} must define exactly min/max")
                continue
            try:
                low, high = float(bounds["min"]), float(bounds["max"])
            except (TypeError, ValueError):
                failures.append(f"measurement {name} min/max must be numeric")
                continue
            if low > high:
                failures.append(f"measurement {name} min must be <= max")
    return failures


def parse_measurements(log: str) -> dict[str, float]:
    result: dict[str, float] = {}
    # ngspice batch .measure output: `name =  7.17e-01 at= ...` or `name = 2.64e-01`.
    for match in re.finditer(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)", log):
        result[match.group(1)] = float(match.group(2))
    return result


def verify_spice_transient(subject: Path, contract_path: Path, evidence_directory: Path) -> dict[str, Any]:
    evidence_directory.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    if not subject.is_file():
        return {"status": "FAIL", "failures": ["SPICE subject is not a regular file"]}
    if not contract_path.is_file():
        return {"status": "FAIL", "failures": ["SPICE object contract is not a regular file"]}
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except Exception as error:
        return {"status": "FAIL", "failures": [f"SPICE object contract JSON unreadable: {error}"]}
    failures.extend(validate_contract(contract))
    if not NGSPICE.is_file():
        failures.append("required external tool unavailable: /usr/bin/ngspice")
    if failures:
        return {"status": "FAIL", "failures": failures}

    version_proc = subprocess.run([str(NGSPICE), "--version-small"], text=True, capture_output=True, check=False, timeout=15)
    version_text = next((line.strip() for line in (version_proc.stdout or version_proc.stderr).splitlines() if "ngspice-" in line), "")
    log_path = evidence_directory / "ngspice.log"
    proc = subprocess.run(
        [str(NGSPICE), "-n", "-b", "-o", str(log_path), str(subject)],
        text=True, capture_output=True, check=False, timeout=90,
    )
    log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    if proc.returncode != 0:
        failures.append("ngspice batch simulation failed")
    fatal_patterns = ("Simulation interrupted due to error", "Error on line", "unknown parameter")
    if any(pattern in log for pattern in fatal_patterns):
        failures.append("ngspice log contains a fatal parse/simulation error")
    rows_match = re.search(r"No\. of Data Rows\s*:\s*(\d+)", log)
    rows = int(rows_match.group(1)) if rows_match else None
    if rows is None or rows < int(contract["minimumDataRows"]):
        failures.append("ngspice transient data-row count is below the object contract")

    observed = parse_measurements(log)
    measurement_results: dict[str, Any] = {}
    for name, bounds in contract["measurements"].items():
        value = observed.get(name)
        low, high = float(bounds["min"]), float(bounds["max"])
        passed = value is not None and low <= value <= high
        measurement_results[name] = {"observed": value, "min": low, "max": high, "status": "PASS" if passed else "FAIL"}
        if not passed:
            failures.append(f"ngspice measurement {name} is absent or outside contract bounds")

    return {
        "schemaVersion": 1,
        "kind": "artifact-eda-spice-transient-verification",
        "status": "PASS" if not failures else "FAIL",
        "subject": file_fact(subject),
        "contract": file_fact(contract_path),
        "tool": {"path": str(NGSPICE), "sha256": sha256_file(NGSPICE), "version": version_text},
        "simulation": {"exitCode": proc.returncode, "dataRows": rows, "measurements": measurement_results, "log": file_fact(log_path) if log_path.is_file() else None},
        "failures": failures,
        "boundary": "PASS proves the exact SPICE netlist bytes execute successfully in the exact observed ngspice build for the netlist-selected transient analysis, produce at least the contracted data-row floor, and satisfy only the explicitly named numeric .measure ranges. It does not prove circuit intent, global stability, convergence under other analyses/conditions, device-model fidelity, tolerances, signal/power integrity, safety, regulatory compliance, or physical-hardware behavior."
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--evidence-directory", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    evidence = args.evidence_directory or Path("out/artifact-eda-spice")
    result = verify_spice_transient(args.input.resolve(), args.contract.resolve(), evidence.resolve())
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
