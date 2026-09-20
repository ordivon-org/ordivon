#!/usr/bin/env python3
"""Standards-first shadow verifier for bounded GeoPackage Point artifacts.

OGC/GeoPackage conformance is delegated to GDAL's GeoPackage validator.
SQLite owns container/integrity/native table observations. OGR owns geospatial
interpretation. This code only binds those external facts to one exact object
contract and checks cross-view consistency.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SCHEMA = ROOT / "artifact-delivery/shadow-contracts/geospatial-vector-contract-v1.schema.json"
GDAL = Path(os.environ.get("ARTIFACT_GDAL_GPKG", "/opt/ordivon/external/python-gdal/3.13.3-2/gdal"))
SQLITE = Path(os.environ.get("ARTIFACT_SQLITE", "/opt/ordivon/external/sqlite/3.53.4-1/sqlite3"))
OGRINFO = Path(os.environ.get("ARTIFACT_OGRINFO", "/usr/bin/ogrinfo"))
OGR2OGR = Path(os.environ.get("ARTIFACT_OGR2OGR", "/usr/bin/ogr2ogr"))
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
EXPECTED_APPLICATION_ID = 1196444487  # 0x47504B47 / GPKG
EXPECTED_USER_VERSION = 10400         # GeoPackage 1.4.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def run(argv: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=timeout)


def artifact_fact(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "name": path.name, "size": path.stat().st_size, "sha256": sha256(path)}


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql_identifier(value: str) -> str:
    if not NAME_RE.fullmatch(value):
        raise ValueError(f"unsafe identifier: {value!r}")
    return '"' + value.replace('"', '""') + '"'


def sqlite_json(path: Path, sql: str) -> tuple[int, Any, str]:
    p = run([str(SQLITE), "-json", str(path), sql])
    value: Any = None
    if p.stdout.strip():
        try:
            value = json.loads(p.stdout)
        except json.JSONDecodeError:
            value = None
    return p.returncode, value, p.stderr


def sqlite_scalar(path: Path, sql: str) -> tuple[int, str, str]:
    p = run([str(SQLITE), str(path), sql])
    return p.returncode, p.stdout.strip(), p.stderr


def validate_contract(contract: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    schema = json.loads(CONTRACT_SCHEMA.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(contract), key=lambda e: list(e.path)):
        failures.append(f"geospatial contract schema invalid: {error.message}")
    if failures:
        return failures
    layer = contract["layer"]
    names = [f["name"] for f in layer["fields"]]
    if len(names) != len(set(names)):
        failures.append("geospatial contract contains duplicate attribute field names")
    if layer["fidColumn"] in names or layer["geometry"]["column"] in names:
        failures.append("fid/geometry columns must not be repeated as attribute fields")
    unknown = [x for x in contract["primaryKey"] if x not in names]
    if unknown:
        failures.append("primaryKey references undeclared attribute field(s): " + ",".join(unknown))
    if "minimumFeatures" in layer and "maximumFeatures" in layer and layer["minimumFeatures"] > layer["maximumFeatures"]:
        failures.append("minimumFeatures exceeds maximumFeatures")
    return failures


def sqlite_type_matches(declared: str, expected: str) -> bool:
    t = declared.upper()
    if expected == "integer": return "INT" in t
    if expected == "string": return any(x in t for x in ("CHAR", "CLOB", "TEXT"))
    if expected == "real": return any(x in t for x in ("REAL", "FLOA", "DOUB"))
    if expected == "boolean": return "BOOL" in t or "INT" in t
    return False


def ogr_type_matches(field: dict[str, Any], expected: str) -> bool:
    t = str(field.get("type") or "")
    subtype = str(field.get("subType") or "")
    if expected == "integer": return t in {"Integer", "Integer64"} and subtype != "Boolean"
    if expected == "string": return t == "String"
    if expected == "real": return t == "Real"
    if expected == "boolean": return (t in {"Integer", "Integer64"} and subtype == "Boolean")
    return False


def verify_geopackage(path: Path, contract_path: Path, evidence_dir: Path | None = None) -> dict[str, Any]:
    if not path.is_file():
        return {"schemaVersion": 1, "kind": "artifact-geospatial-verification", "profileId": "geospatial-geopackage-point-r1", "status": "FAIL", "failures": ["input is not a regular file"]}
    failures: list[str] = []
    try:
        contract = json.loads(contract_path.read_text())
    except Exception as error:
        return {"schemaVersion": 1, "kind": "artifact-geospatial-verification", "profileId": "geospatial-geopackage-point-r1", "status": "FAIL", "artifact": artifact_fact(path), "failures": [f"contract unreadable: {error}"]}
    failures.extend(validate_contract(contract))
    evidence_dir = evidence_dir or Path(tempfile.mkdtemp(prefix="artifact-geospatial-evidence-"))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "artifact-geospatial-verification",
        "profileId": "geospatial-geopackage-point-r1",
        "status": "FAIL",
        "artifact": artifact_fact(path),
        "contract": {"path": str(contract_path.resolve()), "sha256": sha256(contract_path), "canonicalDigest": canonical_digest(contract)},
        "tools": {},
        "failures": failures,
    }
    if failures:
        result["boundary"] = "Invalid object contracts fail before external evidence can be promoted."
        (evidence_dir / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result
    for name, tool in (("gdal", GDAL), ("sqlite", SQLITE), ("ogrinfo", OGRINFO), ("ogr2ogr", OGR2OGR)):
        if not tool.is_file() or not os.access(tool, os.X_OK):
            failures.append(f"required mature external capability unavailable: {name}")
        else:
            result["tools"][name] = {"path": str(tool.resolve()), "sha256": sha256(tool)}
    if failures:
        result["failures"] = failures
        (evidence_dir / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result

    # 1) OGC/GeoPackage conformance via GDAL's full validator.
    val = run([str(GDAL), "driver", "gpkg", "validate", "--full-check", "-v", str(path)])
    (evidence_dir / "gdal-gpkg-validate.txt").write_text(val.stdout + val.stderr)
    validator_pass = val.returncode == 0 and "Validation succeeded" in (val.stdout + val.stderr)
    if not validator_pass:
        failures.append("GDAL GeoPackage full conformance validation failed")

    # 2) Native SQLite container facts.
    rc_integrity, integrity, err_integrity = sqlite_scalar(path, "PRAGMA integrity_check;")
    rc_app, application_id, err_app = sqlite_scalar(path, "PRAGMA application_id;")
    rc_user, user_version, err_user = sqlite_scalar(path, "PRAGMA user_version;")
    sqlite_failures: list[str] = []
    if rc_integrity != 0 or integrity != "ok": sqlite_failures.append("SQLite integrity_check is not ok")
    try: app_id = int(application_id)
    except Exception: app_id = -1
    try: user_ver = int(user_version)
    except Exception: user_ver = -1
    if rc_app != 0 or app_id != EXPECTED_APPLICATION_ID: sqlite_failures.append("GeoPackage application_id is not GPKG")
    if rc_user != 0 or user_ver != EXPECTED_USER_VERSION: sqlite_failures.append("GeoPackage user_version is not 1.4.0 / 10400")
    failures.extend(sqlite_failures)
    sqlite_evidence = {"status": "PASS" if not sqlite_failures else "FAIL", "integrity": integrity, "applicationId": app_id, "userVersion": user_ver, "failures": sqlite_failures}

    layer = contract["layer"]
    lname = layer["name"]
    lstr = sql_literal(lname)
    lid = sql_identifier(lname)
    rc_contents, contents, e1 = sqlite_json(path, "SELECT table_name,data_type,identifier,srs_id,min_x,min_y,max_x,max_y FROM gpkg_contents ORDER BY table_name;")
    rc_geom, geom_rows, e2 = sqlite_json(path, f"SELECT table_name,column_name,geometry_type_name,srs_id,z,m FROM gpkg_geometry_columns WHERE table_name={lstr};")
    rc_table, table_info, e3 = sqlite_json(path, f"PRAGMA table_info({lid});")
    srs_id = int(layer["geometry"]["srs"]["code"])
    rc_srs, srs_rows, e4 = sqlite_json(path, f"SELECT srs_name,srs_id,organization,organization_coordsys_id,definition FROM gpkg_spatial_ref_sys WHERE srs_id={srs_id};")
    rc_count, count_rows, e5 = sqlite_json(path, f"SELECT COUNT(*) AS feature_count FROM {lid};")
    native_bundle = {"contents": contents, "geometryColumns": geom_rows, "tableInfo": table_info, "srs": srs_rows, "count": count_rows}
    (evidence_dir / "sqlite-native-metadata.json").write_text(json.dumps(native_bundle, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    if any(rc != 0 for rc in (rc_contents, rc_geom, rc_table, rc_srs, rc_count)) or not all(isinstance(v, list) for v in (contents, geom_rows, table_info, srs_rows, count_rows)):
        failures.append("native GeoPackage metadata could not be read through SQLite")
        contents = contents if isinstance(contents, list) else []
        geom_rows = geom_rows if isinstance(geom_rows, list) else []
        table_info = table_info if isinstance(table_info, list) else []
        srs_rows = srs_rows if isinstance(srs_rows, list) else []
        count_rows = count_rows if isinstance(count_rows, list) else []

    # 3) Native metadata vs object contract.
    native_failures: list[str] = []
    feature_contents = [r for r in contents if r.get("data_type") == "features"]
    non_feature_contents = [r for r in contents if r.get("data_type") != "features"]
    if len(feature_contents) != 1 or feature_contents[0].get("table_name") != lname:
        native_failures.append("profile requires exactly one feature layer matching contract.layer.name")
    if non_feature_contents:
        native_failures.append("profile excludes tile/attributes-only gpkg_contents entries")
    if len(geom_rows) != 1:
        native_failures.append("contract layer must have exactly one gpkg_geometry_columns row")
    else:
        g = geom_rows[0]; wantg = layer["geometry"]
        if g.get("column_name") != wantg["column"]: native_failures.append("geometry column differs from contract")
        if str(g.get("geometry_type_name") or "").upper() != wantg["type"]: native_failures.append("geometry type differs from contract")
        if int(g.get("srs_id", -999999)) != wantg["srs"]["code"]: native_failures.append("geometry srs_id differs from contract")
        if int(g.get("z", -1)) != 0 or int(g.get("m", -1)) != 0: native_failures.append("R1 requires 2D geometry with z=0,m=0")
    if len(srs_rows) != 1:
        native_failures.append("contract CRS is missing from gpkg_spatial_ref_sys")
    else:
        s = srs_rows[0]; want = layer["geometry"]["srs"]
        if str(s.get("organization") or "").upper() != want["authority"].upper(): native_failures.append("CRS authority differs from contract")
        if int(s.get("organization_coordsys_id", -999999)) != want["code"]: native_failures.append("CRS authority code differs from contract")
    by_name = {r.get("name"): r for r in table_info}
    fid = by_name.get(layer["fidColumn"])
    if not fid or int(fid.get("pk", 0)) != 1 or "INT" not in str(fid.get("type") or "").upper(): native_failures.append("FID column is not the expected INTEGER primary key")
    geom_col = by_name.get(layer["geometry"]["column"])
    if not geom_col: native_failures.append("geometry column absent from native table schema")
    else:
        observed_nullable = int(geom_col.get("notnull", 0)) == 0
        if observed_nullable != layer["geometry"]["nullable"]: native_failures.append("geometry nullability differs from contract")
    for want in layer["fields"]:
        got = by_name.get(want["name"])
        if not got: native_failures.append(f"attribute field missing from native schema: {want['name']}"); continue
        if not sqlite_type_matches(str(got.get("type") or ""), want["type"]): native_failures.append(f"SQLite declared type differs for field {want['name']}")
        observed_nullable = int(got.get("notnull", 0)) == 0
        if observed_nullable != want["nullable"]: native_failures.append(f"SQLite nullability differs for field {want['name']}")
    failures.extend(native_failures)
    native_evidence = {"status": "PASS" if not native_failures else "FAIL", "failures": native_failures, "evidenceSha256": sha256(evidence_dir / "sqlite-native-metadata.json")}

    # 4) OGR geospatial interpretation.
    ogr = run([str(OGRINFO), "-ro", "-so", "-json", str(path), lname])
    (evidence_dir / "ogrinfo.json").write_text(ogr.stdout)
    try: ogr_obj = json.loads(ogr.stdout) if ogr.returncode == 0 else {}
    except json.JSONDecodeError: ogr_obj = {}
    ogr_failures: list[str] = []
    layers = ogr_obj.get("layers") if isinstance(ogr_obj, dict) else None
    olayer = layers[0] if isinstance(layers, list) and len(layers) == 1 else None
    if not isinstance(olayer, dict):
        ogr_failures.append("OGR did not expose exactly one requested layer")
        olayer = {}
    if olayer.get("name") != lname: ogr_failures.append("OGR layer name differs from contract")
    if olayer.get("fidColumnName") != layer["fidColumn"]: ogr_failures.append("OGR FID column differs from contract")
    if int(olayer.get("featureCount", -1)) != (int(count_rows[0]["feature_count"]) if count_rows else -2): ogr_failures.append("OGR and SQLite feature counts differ")
    gfields = olayer.get("geometryFields") or []
    if len(gfields) != 1:
        ogr_failures.append("OGR must expose exactly one geometry field")
    else:
        gf = gfields[0]; wantg = layer["geometry"]
        if gf.get("name") != wantg["column"]: ogr_failures.append("OGR geometry column differs from contract")
        if str(gf.get("type") or "").upper() != wantg["type"]: ogr_failures.append("OGR geometry type differs from contract")
        if bool(gf.get("nullable")) != wantg["nullable"]: ogr_failures.append("OGR geometry nullability differs from contract")
        cid = (((gf.get("coordinateSystem") or {}).get("projjson") or {}).get("id") or {})
        if str(cid.get("authority") or "").upper() != wantg["srs"]["authority"].upper() or int(cid.get("code", -999999)) != wantg["srs"]["code"]:
            ogr_failures.append("OGR CRS authority/code differs from contract")
    ofields = olayer.get("fields") or []
    if [f.get("name") for f in ofields] != [f["name"] for f in layer["fields"]]: ogr_failures.append("OGR attribute field order/name differs from contract")
    if len(ofields) == len(layer["fields"]):
        for got, want in zip(ofields, layer["fields"]):
            if not ogr_type_matches(got, want["type"]): ogr_failures.append(f"OGR logical type differs for field {want['name']}")
            if bool(got.get("nullable")) != want["nullable"]: ogr_failures.append(f"OGR nullability differs for field {want['name']}")
    failures.extend(ogr_failures)
    ogr_evidence = {"status": "PASS" if not ogr_failures else "FAIL", "failures": ogr_failures, "evidenceSha256": sha256(evidence_dir / "ogrinfo.json")}

    # 5) Cross-view attribute agreement and logical key integrity.
    fields = [f["name"] for f in layer["fields"]]
    pk = contract["primaryKey"]
    select_fields = ",".join(sql_identifier(x) for x in fields)
    order = ",".join(sql_identifier(x) for x in pk)
    rc_rows, sqlite_rows, row_err = sqlite_json(path, f"SELECT {select_fields} FROM {lid} ORDER BY {order};")
    if rc_rows != 0 or not isinstance(sqlite_rows, list): sqlite_rows = []; failures.append("SQLite attribute rows could not be read")
    (evidence_dir / "sqlite-attributes.json").write_text(json.dumps(sqlite_rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    geojson = run([str(OGR2OGR), "-f", "GeoJSON", "/vsistdout/", str(path), lname])
    (evidence_dir / "ogr-features.geojson").write_text(geojson.stdout)
    ogr_rows: list[dict[str, Any]] = []
    if geojson.returncode != 0:
        failures.append("OGR feature projection failed")
    else:
        try:
            gj = json.loads(geojson.stdout)
            ogr_rows = [dict(f.get("properties") or {}) for f in gj.get("features", [])]
        except Exception:
            failures.append("OGR feature projection returned invalid GeoJSON")
    cross_failures: list[str] = []
    try:
        sqlite_rows = sorted(sqlite_rows, key=lambda r: tuple(r.get(k) for k in pk))
        ogr_rows = sorted(ogr_rows, key=lambda r: tuple(r.get(k) for k in pk))
        sb, ob = canonical_bytes(sqlite_rows), canonical_bytes(ogr_rows)
        same = sb == ob
        if not same: cross_failures.append("SQLite attributes and OGR GeoJSON properties differ")
        keys = [tuple(r.get(k) for k in pk) for r in sqlite_rows]
        null_key = any(any(v is None for v in key) for key in keys)
        duplicate = len(set(keys)) != len(keys)
        if null_key: cross_failures.append("declared logical primary key contains null")
        if duplicate: cross_failures.append("declared logical primary key is not unique")
        cross = {"status": "PASS" if not cross_failures else "FAIL", "sqliteAttributesSha256": hashlib.sha256(sb).hexdigest(), "ogrPropertiesSha256": hashlib.sha256(ob).hexdigest(), "exactMatch": same, "rowCount": len(sqlite_rows), "failures": cross_failures}
        key_evidence = {"status": "PASS" if not null_key and not duplicate else "FAIL", "columns": pk, "nullObserved": null_key, "duplicateObserved": duplicate}
    except Exception as error:
        cross_failures.append(f"attribute/key canonicalization failed: {error}")
        cross = {"status": "FAIL", "failures": cross_failures}
        key_evidence = {"status": "FAIL"}
    failures.extend(cross_failures)

    count = int(count_rows[0]["feature_count"]) if count_rows else -1
    bound_failures: list[str] = []
    if "minimumFeatures" in layer and count < layer["minimumFeatures"]: bound_failures.append("feature count below contract minimumFeatures")
    if "maximumFeatures" in layer and count > layer["maximumFeatures"]: bound_failures.append("feature count above contract maximumFeatures")
    failures.extend(bound_failures)

    result.update({
        "ogcConformance": {"status": "PASS" if validator_pass else "FAIL", "returnCode": val.returncode, "evidenceSha256": sha256(evidence_dir / "gdal-gpkg-validate.txt")},
        "sqliteContainer": sqlite_evidence,
        "nativeMetadata": native_evidence,
        "geospatialInterpretation": ogr_evidence,
        "attributeCrossView": cross,
        "keyIntegrity": key_evidence,
        "featureBounds": {"status": "PASS" if not bound_failures else "FAIL", "featureCount": count, "minimumFeatures": layer.get("minimumFeatures"), "maximumFeatures": layer.get("maximumFeatures"), "failures": bound_failures},
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "boundary": "PASS is bounded to one OGC GeoPackage 1.4.0 2D Point feature layer under one exact object contract. It establishes container integrity, selected GeoPackage conformance, native metadata/CRS/schema agreement, OGR interpretation, cross-view attributes, logical key integrity and feature bounds. It does not establish positional accuracy, factual truth, CRS fitness, cartographic quality, non-Point topology, tile/raster semantics or spatial-analysis correctness."
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
    value = verify_geopackage(args.input, args.contract, args.evidence_directory)
    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(text)
    else: print(text, end="")
    return 0 if value.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
