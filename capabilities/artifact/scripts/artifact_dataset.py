#!/usr/bin/env python3
"""Standards-first shadow verifier for bounded flat Parquet datasets.

Parquet parsing is delegated to mature independent readers (DuckDB and
PyArrow). This code binds a concrete Dataset Contract to their evidence and
checks only cross-reader/profile/contract invariants.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA = ROOT / "artifact-delivery/shadow-contracts/dataset-contract-v1.schema.json"
DUCKDB = Path(os.environ.get("ARTIFACT_DUCKDB", "/opt/ordivon/external/duckdb/1.5.5-1/duckdb"))
PYARROW_PYTHON = Path(os.environ.get("ARTIFACT_PYARROW_PYTHON", "/opt/ordivon/external/pyarrow/25.0.1/python"))
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

TYPE_MAP = {
    "int64": {"arrow": "int64", "duckdb": "BIGINT", "physical": "INT64", "logical": {None, ""}},
    "string": {"arrow": "string", "duckdb": "VARCHAR", "physical": "BYTE_ARRAY", "logical": {"StringType()"}},
    "float64": {"arrow": "double", "duckdb": "DOUBLE", "physical": "DOUBLE", "logical": {None, ""}},
    "boolean": {"arrow": "bool", "duckdb": "BOOLEAN", "physical": "BOOLEAN", "logical": {None, ""}},
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(argv: list[str], *, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=timeout)


def artifact_fact(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "name": path.name, "size": path.stat().st_size, "sha256": sha256(path)}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql_identifier(value: str) -> str:
    if not NAME_RE.fullmatch(value):
        raise ValueError(f"unsafe dataset identifier: {value!r}")
    return '"' + value.replace('"', '""') + '"'


def validate_contract(contract: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    schema = json.loads(CONTRACT_SCHEMA.read_text())
    try:
        jsonschema.Draft202012Validator(schema).validate(contract)
    except jsonschema.ValidationError as error:
        failures.append(f"dataset contract schema invalid: {error.message}")
        return failures
    names = [c["name"] for c in contract["columns"]]
    if len(names) != len(set(names)):
        failures.append("dataset contract contains duplicate column names")
    unknown_pk = [name for name in contract["primaryKey"] if name not in names]
    if unknown_pk:
        failures.append("primary key references undeclared column(s): " + ",".join(unknown_pk))
    by_name = {c["name"]: c for c in contract["columns"]}
    nullable_pk = [name for name in contract["primaryKey"] if name in by_name and by_name[name]["nullable"]]
    if nullable_pk:
        failures.append("primary-key column(s) must be non-nullable in the contract: " + ",".join(nullable_pk))
    if "minimumRows" in contract and "maximumRows" in contract and contract["minimumRows"] > contract["maximumRows"]:
        failures.append("minimumRows exceeds maximumRows")
    return failures


PYARROW_PROBE = r'''
import json, math, sys
import pyarrow as pa
import pyarrow.parquet as pq
p=sys.argv[1]
try:
    pf=pq.ParquetFile(p)
    table=pf.read()
    fields=[]
    for i,field in enumerate(pf.schema_arrow):
        c=pf.schema.column(i)
        fields.append({
            "name": field.name,
            "arrowType": str(field.type),
            "nullable": field.nullable,
            "physicalType": c.physical_type,
            "logicalType": str(c.logical_type) if c.logical_type is not None else None,
            "maxDefinitionLevel": c.max_definition_level,
            "maxRepetitionLevel": c.max_repetition_level,
        })
    rows=table.to_pylist()
    def walk(v):
        if isinstance(v,float) and not math.isfinite(v): raise ValueError("non-finite float value")
        if isinstance(v,dict): return {k:walk(x) for k,x in v.items()}
        if isinstance(v,list): return [walk(x) for x in v]
        return v
    rows=walk(rows)
    print(json.dumps({
        "status":"PASS",
        "pyarrowVersion":pa.__version__,
        "numRows":table.num_rows,
        "numColumns":table.num_columns,
        "fields":fields,
        "rows":rows,
        "metadata":{"numRowGroups":pf.metadata.num_row_groups,"formatVersion":pf.metadata.format_version,"createdBy":pf.metadata.created_by},
    },ensure_ascii=False,sort_keys=True,allow_nan=False))
except Exception as e:
    print(json.dumps({"status":"FAIL","error":type(e).__name__+": "+str(e)},ensure_ascii=False,sort_keys=True))
    raise SystemExit(2)
'''


def duckdb_json(query: str) -> tuple[int, Any, str]:
    p = run([str(DUCKDB), "-json", "-c", query])
    value: Any = None
    if p.stdout.strip():
        try:
            value = json.loads(p.stdout)
        except json.JSONDecodeError:
            value = None
    return p.returncode, value, p.stderr


def verify_parquet(path: Path, contract_path: Path, evidence_dir: Path | None = None) -> dict[str, Any]:
    failures: list[str] = []
    if not path.is_file():
        return {"schemaVersion": 1, "kind": "artifact-dataset-verification", "profileId": "dataset-parquet-flat-r1", "status": "FAIL", "failures": ["input is not a regular file"]}
    if not contract_path.is_file():
        return {"schemaVersion": 1, "kind": "artifact-dataset-verification", "profileId": "dataset-parquet-flat-r1", "status": "FAIL", "artifact": artifact_fact(path), "failures": ["dataset contract is not a regular file"]}
    try:
        contract = json.loads(contract_path.read_text())
    except Exception as error:
        return {"schemaVersion": 1, "kind": "artifact-dataset-verification", "profileId": "dataset-parquet-flat-r1", "status": "FAIL", "artifact": artifact_fact(path), "failures": [f"dataset contract JSON unreadable: {error}"]}
    failures.extend(validate_contract(contract))
    evidence_dir = evidence_dir or Path(tempfile.mkdtemp(prefix="artifact-dataset-evidence-"))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "artifact-dataset-verification",
        "profileId": "dataset-parquet-flat-r1",
        "status": "FAIL",
        "artifact": artifact_fact(path),
        "contract": {"path": str(contract_path.resolve()), "sha256": sha256(contract_path), "canonicalDigest": canonical_digest(contract)},
        "tools": {},
        "failures": failures,
    }
    if failures:
        result["boundary"] = "Contract-invalid inputs fail before reader evidence is promoted."
        (evidence_dir / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result
    for name, tool in (("duckdb", DUCKDB), ("pyarrowPython", PYARROW_PYTHON)):
        if not tool.is_file() or not os.access(tool, os.X_OK):
            failures.append(f"required independent reader unavailable: {name}")
        else:
            result["tools"][name] = {"path": str(tool.resolve()), "sha256": sha256(tool)}
    if failures:
        result["failures"] = failures
        (evidence_dir / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result

    # PyArrow independent reader.
    pa = run([str(PYARROW_PYTHON), "-c", PYARROW_PROBE, str(path)])
    (evidence_dir / "pyarrow.json").write_text(pa.stdout)
    pyarrow: dict[str, Any] | None = None
    if pa.stdout.strip():
        try: pyarrow = json.loads(pa.stdout)
        except json.JSONDecodeError: pass
    if pa.returncode != 0 or not isinstance(pyarrow, dict) or pyarrow.get("status") != "PASS":
        failures.append("PyArrow rejected or could not decode the Parquet artifact")
        pyarrow = pyarrow or {"status": "FAIL", "stderr": pa.stderr[-4000:]}

    # DuckDB native Parquet schema/metadata plus logical rows.
    psql = sql_string(str(path.resolve()))
    rc_schema, duck_schema, err_schema = duckdb_json(f"SELECT * FROM parquet_schema({psql});")
    rc_meta, duck_meta, err_meta = duckdb_json(f"SELECT num_rows,num_row_groups,format_version,created_by FROM parquet_file_metadata({psql});")
    order = ",".join(sql_identifier(x) for x in contract["primaryKey"])
    rc_rows, duck_rows, err_rows = duckdb_json(f"SELECT * FROM read_parquet({psql}) ORDER BY {order};")
    (evidence_dir / "duckdb-schema.json").write_text(json.dumps(duck_schema, indent=2, sort_keys=True) + "\n" if duck_schema is not None else err_schema)
    (evidence_dir / "duckdb-metadata.json").write_text(json.dumps(duck_meta, indent=2, sort_keys=True) + "\n" if duck_meta is not None else err_meta)
    (evidence_dir / "duckdb-rows.json").write_text(json.dumps(duck_rows, indent=2, sort_keys=True, ensure_ascii=False) + "\n" if duck_rows is not None else err_rows)
    if rc_schema != 0 or rc_meta != 0 or rc_rows != 0 or not isinstance(duck_schema, list) or not isinstance(duck_meta, list) or not isinstance(duck_rows, list):
        failures.append("DuckDB rejected or could not decode the Parquet artifact")

    schema_evidence: dict[str, Any] = {"status": "FAIL"}
    row_evidence: dict[str, Any] = {"status": "FAIL"}
    key_evidence: dict[str, Any] = {"status": "FAIL"}
    bounds_evidence: dict[str, Any] = {"status": "FAIL"}

    if pyarrow.get("status") == "PASS" and isinstance(duck_schema, list) and isinstance(duck_meta, list) and isinstance(duck_rows, list):
        expected = contract["columns"]
        pa_fields = pyarrow["fields"]
        duck_fields = [row for row in duck_schema if row.get("type") is not None]
        schema_failures: list[str] = []
        if [x["name"] for x in expected] != [x.get("name") for x in pa_fields]:
            schema_failures.append("PyArrow column order/name differs from contract")
        if [x["name"] for x in expected] != [x.get("name") for x in duck_fields]:
            schema_failures.append("DuckDB parquet_schema column order/name differs from contract")
        if len(expected) == len(pa_fields) == len(duck_fields):
            for want, paf, df in zip(expected, pa_fields, duck_fields):
                mapping = TYPE_MAP[want["type"]]
                repetition = "OPTIONAL" if want["nullable"] else "REQUIRED"
                if paf.get("arrowType") != mapping["arrow"]: schema_failures.append(f"PyArrow type mismatch for {want['name']}")
                if bool(paf.get("nullable")) != want["nullable"]: schema_failures.append(f"PyArrow nullability mismatch for {want['name']}")
                if paf.get("physicalType") != mapping["physical"]: schema_failures.append(f"PyArrow physical type mismatch for {want['name']}")
                if df.get("duckdb_type") != mapping["duckdb"]: schema_failures.append(f"DuckDB logical SQL type mismatch for {want['name']}")
                if df.get("type") != mapping["physical"]: schema_failures.append(f"DuckDB Parquet physical type mismatch for {want['name']}")
                if df.get("repetition_type") != repetition: schema_failures.append(f"DuckDB repetition mismatch for {want['name']}")
                if df.get("logical_type") not in mapping["logical"]: schema_failures.append(f"DuckDB logical annotation mismatch for {want['name']}")
        failures.extend(schema_failures)
        schema_evidence = {
            "status": "PASS" if not schema_failures else "FAIL",
            "contractColumns": expected,
            "pyarrowFields": pa_fields,
            "duckdbParquetFields": duck_fields,
            "failures": schema_failures,
        }

        # Compare logical rows after contract-declared primary-key canonicalization.
        pa_rows = pyarrow["rows"]
        pk = contract["primaryKey"]
        try:
            pa_rows = sorted(pa_rows, key=lambda row: tuple(row[k] for k in pk))
            pa_bytes = canonical_bytes(pa_rows)
            duck_bytes = canonical_bytes(duck_rows)
            same_rows = pa_bytes == duck_bytes
            if not same_rows:
                failures.append("DuckDB and PyArrow logical rows differ after primary-key canonicalization")
            row_evidence = {
                "status": "PASS" if same_rows else "FAIL",
                "rowCount": len(pa_rows),
                "pyarrowRowsSha256": hashlib.sha256(pa_bytes).hexdigest(),
                "duckdbRowsSha256": hashlib.sha256(duck_bytes).hexdigest(),
                "exactCanonicalRowsMatch": same_rows,
            }
            keys = [tuple(row[k] for k in pk) for row in pa_rows]
            null_key = any(any(v is None for v in key) for key in keys)
            duplicate_key = len(set(keys)) != len(keys)
            if null_key: failures.append("declared primary key contains null value")
            if duplicate_key: failures.append("declared primary key is not unique")
            key_evidence = {"status": "PASS" if not null_key and not duplicate_key else "FAIL", "columns": pk, "nullKeyObserved": null_key, "duplicateKeyObserved": duplicate_key}
        except (KeyError, TypeError, ValueError) as error:
            failures.append(f"row canonicalization failed: {error}")

        pa_count = int(pyarrow["numRows"])
        duck_count = int(duck_meta[0]["num_rows"]) if duck_meta else -1
        bounds_failures: list[str] = []
        if pa_count != duck_count: bounds_failures.append("reader row counts differ")
        if "minimumRows" in contract and pa_count < contract["minimumRows"]: bounds_failures.append("row count below contract minimumRows")
        if "maximumRows" in contract and pa_count > contract["maximumRows"]: bounds_failures.append("row count above contract maximumRows")
        failures.extend(bounds_failures)
        bounds_evidence = {"status": "PASS" if not bounds_failures else "FAIL", "pyarrowRowCount": pa_count, "duckdbRowCount": duck_count, "minimumRows": contract.get("minimumRows"), "maximumRows": contract.get("maximumRows"), "failures": bounds_failures}

    result.update({
        "parquetSchema": schema_evidence,
        "readerAgreement": row_evidence,
        "keyIntegrity": key_evidence,
        "rowBounds": bounds_evidence,
        "pyarrow": {k: v for k, v in pyarrow.items() if k != "rows"},
        "duckdb": {"schemaEvidenceSha256": sha256(evidence_dir / "duckdb-schema.json"), "metadataEvidenceSha256": sha256(evidence_dir / "duckdb-metadata.json"), "rowsEvidenceSha256": sha256(evidence_dir / "duckdb-rows.json")},
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "boundary": "PASS is bounded to a flat primitive Parquet dataset under one exact Dataset Contract: native Parquet schema/profile agreement, two independent reader interpretations, primary-key integrity, row bounds and exact canonical logical-row agreement. It does not establish data truth, provenance, statistical quality, domain semantics, units/ontology, schema evolution, nested types, warehouse/catalog transactions or broader database constraints."
    })
    (evidence_dir / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--evidence-directory", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    value = verify_parquet(args.input, args.contract, args.evidence_directory)
    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0 if value.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
