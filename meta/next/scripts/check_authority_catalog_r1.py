#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
CATALOG_TOOL = REPO_ROOT / "tools" / "catalog" / "authority_catalog.py"
SPEC = importlib.util.spec_from_file_location("authority_catalog", CATALOG_TOOL)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load authority catalog tool: {CATALOG_TOOL}")
catalog = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = catalog
SPEC.loader.exec_module(catalog)

RECORD_SCHEMA = ROOT / "schemas/external-authority-record-v1.schema.json"
OBS_SCHEMA = ROOT / "schemas/external-authority-observation-v1.schema.json"
INDEX_SCHEMA = ROOT / "schemas/external-authority-index-v1.schema.json"
DOGFOOD = (
    ROOT / "evidence/acceptance/standard-native-enterprise-r2-dogfood-20260914.json"
)
ENTERPRISE = (
    ROOT / "evidence/acceptance/enterprise-operating-model-r1-dogfood-20260914.json"
)


def fail(message: str) -> None:
    raise SystemExit(message)


def run(*args: str) -> str:
    try:
        return subprocess.check_output(
            args, cwd=ROOT, text=True, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as exc:
        detail = (
            exc.output.strip()
            or f"command failed with exit code {exc.returncode}: {args}"
        )
        raise SystemExit(detail) from exc


def main() -> int:
    records = catalog.records()
    catalog.validate_catalog_semantics(records)
    if len(records) < 30:
        fail(f"seed catalog unexpectedly small: {len(records)}")

    with tempfile.TemporaryDirectory() as d:
        temp = Path(d)
        record_files = [str(path) for path, _ in records.values()]
        observation_files = [
            str(p)
            for authority_id in records
            for p in catalog.observation_paths(authority_id)
        ]
        if record_files:
            run("check-jsonschema", "--schemafile", str(RECORD_SCHEMA), *record_files)
        if observation_files:
            run("check-jsonschema", "--schemafile", str(OBS_SCHEMA), *observation_files)
        built = catalog.build_index()
        temp_index = temp / "authority-index.json"
        temp_index.write_text(
            json.dumps(built, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        run("check-jsonschema", "--schemafile", str(INDEX_SCHEMA), str(temp_index))
        if temp_index.read_bytes() != catalog.INDEX.read_bytes():
            fail("committed generated index differs from deterministic rebuild")

    dogfood = json.loads(DOGFOOD.read_text(encoding="utf-8"))
    required_ids = set()
    deferred_ids = set()
    for case in dogfood["cases"]:
        for row in case["authorityDecisions"]:
            if row["disposition"] == "DEFERRED":
                deferred_ids.add(row["id"])
            else:
                required_ids.add(row["id"])
    enterprise = json.loads(ENTERPRISE.read_text(encoding="utf-8"))
    required_ids.update(row["id"] for row in enterprise["externalManagementGuidance"])
    missing = sorted(required_ids - set(records))
    if missing:
        fail(f"structured non-deferred authority ids missing from catalog: {missing}")

    index = json.loads(catalog.INDEX.read_text(encoding="utf-8"))
    if index["recordCount"] != len(records):
        fail("index recordCount mismatch")
    forbidden_index_keys = {
        "officialSource",
        "access",
        "relations",
        "provenance",
        "role",
        "disposition",
        "rationale",
    }
    for entry in index["entries"]:
        leak = forbidden_index_keys.intersection(entry)
        if leak:
            fail(
                f"Level-0 discovery index leaked Level-1/task fields: {entry['id']} {sorted(leak)}"
            )

    risk = [r for r in index["entries"] if r["id"] == "iso-31000-2018"]
    if len(risk) != 1:
        fail("ISO 31000 seed missing")
    found = [
        (catalog.score_entry(row, "risk management"), row["id"])
        for row in index["entries"]
    ]
    if max(found)[1] != "iso-31000-2018":
        # max tuple tie-break is not the CLI order; test using explicit sort.
        ordered = sorted(found, key=lambda x: (-x[0], x[1]))
        if ordered[0][1] != "iso-31000-2018":
            fail(f"lexical discovery failed for risk management: {ordered[:5]}")

    _, iso = catalog.get_record("iso-31000-2018")
    if catalog.forbidden_fields(iso):
        fail("authority record contains task-local fields")
    refresh = subprocess.check_output(
        [
            sys.executable,
            str(CATALOG_TOOL),
            "refresh",
            "iso-31000-2018",
        ],
        cwd=ROOT,
        text=True,
    )
    refresh_value = json.loads(refresh)
    if refresh_value.get("mutated") is not False:
        fail("refresh must be read-only")

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.external-authority-catalog-r1-acceptance",
        "standing": "PASS_LIGHTWEIGHT_PROGRESSIVE_DISCOVERY",
        "recordCount": len(records),
        "observationCount": sum(
            len(catalog.observation_paths(authority_id)) for authority_id in records
        ),
        "structuredNonDeferredDogfoodIdsResolved": len(required_ids),
        "deferredTaskLocalIdsNotRequiredToResolve": sorted(deferred_ids),
        "discoveryIndex": "catalogs/authorities/generated/authority-index.json",
        "validator": run("check-jsonschema", "--version").strip(),
        "boundary": "Acceptance proves catalog registration/discovery/loading mechanics and migration of already-verified authority metadata. It does not prove catalog completeness, task applicability, standards conformance, certification or semantic currentness beyond recorded observations.",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
