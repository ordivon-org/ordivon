#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evidence/data-lifecycle/github-pilot-r1"
RAW = BASE / "raw"
OUT = BASE / "derived"
CONTRACTS = BASE / "contracts"
CATALOG = BASE / "catalog"
LINEAGE = BASE / "lineage"
RUNTIME_LINEAGE = BASE / "runtime-lineage"
RUNTIME_ACQUISITION = BASE / "runtime-acquisition"
ANALYSIS = BASE / "analysis"
SOURCE = BASE / "source"
for d in (OUT, CONTRACTS, CATALOG, LINEAGE, RUNTIME_LINEAGE, RUNTIME_ACQUISITION, ANALYSIS):
    d.mkdir(parents=True, exist_ok=True)

TIDY_SHA = (SOURCE / "tidytuesday-main.sha").read_text().strip()
DUCKDB = "/usr/bin/duckdb"
OL_SCHEMA_URL = "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent"
PRODUCER = "urn:ordivon:data-lifecycle:github-pilot-r1"
SEMANTICS_PATH = BASE / "semantics/external-semantic-profile.json"
SEMANTICS = json.loads(SEMANTICS_PATH.read_text(encoding="utf-8"))

DATASETS = {
    "crossref-member-participation": {
        "raw": RAW / "crossref-member-participation.csv",
        "parquet": OUT / "crossref-member-participation.parquet",
        "source_path": "data/2026/2026-05-19/member_participation_stats_by_country.csv",
        "title": "Crossref member participation statistics by country",
        "data_product": "crossref-metadata-country",
        "source_sha256": "0f220075cedec9443c1a7343771cff7cce1c3892d6e0717f7e6fecbcdb0ad2af",
    },
    "crossref-metadata-coverage": {
        "raw": RAW / "crossref-metadata-coverage.csv",
        "parquet": OUT / "crossref-metadata-coverage.parquet",
        "source_path": "data/2026/2026-05-19/metadata_coverage_stats_by_country.csv",
        "title": "Crossref metadata coverage statistics by country and document type",
        "data_product": "crossref-metadata-country",
        "source_sha256": "2e37a30acc28f47bf724ca1038fbe840ab1be84cd66790ae69aa62a6731f0ad4",
    },
    "se4all-energy": {
        "raw": RAW / "se4all-energy.csv",
        "parquet": OUT / "se4all-energy.parquet",
        "source_path": "data/2026/2026-05-26/energy_cleaned.csv",
        "title": "Sustainable Energy for All country historical indicators",
        "data_product": "se4all-energy-country-year",
        "source_sha256": "87ad1ef2d9713693c17ab57f9e2d995cf427b6c32a088597877301a15f307f0b",
    },
}

def run_json(sql: str):
    out = subprocess.check_output([DUCKDB, "-json", "-c", sql], text=True)
    return json.loads(out)

def sql_quote(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

def describe(path: Path):
    return run_json(f"DESCRIBE SELECT * FROM read_parquet('{sql_quote(path)}')")

def row_count(path: Path) -> int:
    return int(run_json(f"SELECT count(*) AS n FROM read_parquet('{sql_quote(path)}')")[0]["n"])

def duplicate_count(path: Path, keys: list[str]) -> int:
    group = ", ".join(f'"{k}"' for k in keys)
    q = f"""
    SELECT coalesce(sum(n - 1), 0) AS duplicates
    FROM (
      SELECT {group}, count(*) AS n
      FROM read_parquet('{sql_quote(path)}')
      GROUP BY {group}
      HAVING count(*) > 1
    )
    """
    return int(run_json(q)[0]["duplicates"])

def null_key_count(path: Path, keys: list[str]) -> int:
    pred = " OR ".join(f'"{k}" IS NULL' for k in keys)
    return int(run_json(f"SELECT count(*) AS n FROM read_parquet('{sql_quote(path)}') WHERE {pred}")[0]["n"])

def ensure_raw():
    RAW.mkdir(parents=True, exist_ok=True)
    receipts = {}
    for name, d in DATASETS.items():
        canonical = f"https://raw.githubusercontent.com/rfordatascience/tidytuesday/{TIDY_SHA}/{d['source_path']}"
        mirror = f"https://cdn.jsdelivr.net/gh/rfordatascience/tidytuesday@{TIDY_SHA}/{d['source_path']}"
        transports = [mirror, canonical]
        used = "existing-local"
        if not d["raw"].exists() or sha256(d["raw"]) != d["source_sha256"]:
            last_error = None
            for url in transports:
                tmp = d["raw"].with_suffix(d["raw"].suffix + ".part")
                tmp.unlink(missing_ok=True)
                try:
                    subprocess.check_call([
                        "/usr/bin/curl", "-fL", "--retry", "2",
                        "--connect-timeout", "10", "--max-time", "60",
                        url, "-o", str(tmp),
                    ])
                    actual = sha256(tmp)
                    if actual != d["source_sha256"]:
                        raise RuntimeError(f"digest mismatch from {url}: {actual}")
                    tmp.replace(d["raw"])
                    used = url
                    break
                except Exception as exc:
                    last_error = str(exc)
                    tmp.unlink(missing_ok=True)
            else:
                raise RuntimeError(f"{name}: all acquisition transports failed: {last_error}")
        actual = sha256(d["raw"])
        if actual != d["source_sha256"]:
            raise RuntimeError(f"{name}: source digest mismatch: {actual} != {d['source_sha256']}")
        receipts[name] = {
            "sourceIdentity": f"github:rfordatascience/tidytuesday@{TIDY_SHA}:{d['source_path']}",
            "canonicalUrl": canonical,
            "transportUsed": used,
            "sha256": actual,
        }
    policy = {
        "schemaVersion": 1,
        "kind": "digest-verified-acquisition-policy",
        "identityRule": "Git commit + repository path + expected SHA-256 define source identity; transport URL is operational only.",
        "datasets": {},
    }
    for name, d in DATASETS.items():
        policy["datasets"][name] = {
            "sourceIdentity": receipts[name]["sourceIdentity"],
            "canonicalUrl": receipts[name]["canonicalUrl"],
            "allowedTransports": [
                f"https://cdn.jsdelivr.net/gh/rfordatascience/tidytuesday@{TIDY_SHA}/{d['source_path']}",
                receipts[name]["canonicalUrl"],
            ],
            "sha256": receipts[name]["sha256"],
        }
    write_json(SOURCE / "acquisition-policy.json", policy)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    write_json(RUNTIME_ACQUISITION / f"{stamp}.json", {
        "schemaVersion": 1,
        "kind": "digest-verified-acquisition-receipt",
        "policy": str((SOURCE / "acquisition-policy.json").relative_to(ROOT)),
        "datasets": receipts,
    })

def convert_all():
    for name, d in DATASETS.items():
        raw = sql_quote(d["raw"])
        out = sql_quote(d["parquet"])
        if d["parquet"].exists():
            d["parquet"].unlink()
        select_parts = ["*"]
        sem = dataset_semantics(name)
        for source_col, null_meta in sem.get("sourceNullSemantics", {}).items():
            norm = null_meta.get("physicalKeyNormalization")
            if not norm:
                continue
            replacement = str(norm["nullReplacement"]).replace("'", "''")
            derived = norm["derivedColumn"].replace('"', '""')
            source = source_col.replace('"', '""')
            select_parts.append(f"coalesce(\"{source}\", '{replacement}') AS \"{derived}\"")
        select_expr = ", ".join(select_parts)
        sql = f"""
        COPY (
          SELECT {select_expr} FROM read_csv_auto('{raw}', header=true, nullstr='NA', sample_size=-1)
        ) TO '{out}' (FORMAT PARQUET, COMPRESSION ZSTD);
        """
        subprocess.check_call([DUCKDB, "-c", sql])

def logical_type(duck_type: str) -> str:
    t = duck_type.upper()
    if "DATE" in t:
        return "date"
    if any(x in t for x in ("INT", "HUGEINT", "UBIGINT")):
        return "integer"
    if any(x in t for x in ("DOUBLE", "FLOAT", "DECIMAL", "REAL")):
        return "number"
    if "BOOL" in t:
        return "boolean"
    return "string"

def dataset_semantics(name: str) -> dict:
    return SEMANTICS["datasets"][name]

def measure_semantics(name: str, column: str) -> dict | None:
    return dataset_semantics(name).get("measures", {}).get(column)

def make_odcs(name: str, d: dict):
    schema_rows = describe(d["parquet"])
    sem = dataset_semantics(name)
    keys = sem["physicalPrimaryKey"]
    semantic_dimensions = set(sem.get("semanticDimensions", [])) | set(sem.get("descriptiveDimensions", [])) | set(keys)
    props = []
    for row in schema_rows:
        col = row["column_name"]
        prop = {
            "name": col,
            "physicalName": col,
            "logicalType": logical_type(row["column_type"]),
            "physicalType": row["column_type"].lower(),
            "primaryKey": col in keys,
            "primaryKeyPosition": keys.index(col) + 1 if col in keys else -1,
            "required": null_key_count(d["parquet"], [col]) == 0,
            "classification": "public",
            "semanticType": "dimension" if col in semantic_dimensions else ("measure" if logical_type(row["column_type"]) in {"number", "integer"} else "column"),
        }
        ms = measure_semantics(name, col)
        custom_properties = []
        if ms:
            custom_properties.extend([
                {"property": "unitUcum", "value": ms["unitUcum"]},
                {"property": "unitQudt", "value": ms["unitQudt"]},
                {"property": "quantitySemantics", "value": ms["quantitySemantics"]},
            ])
        null_sem = sem.get("sourceNullSemantics", {}).get(col)
        if null_sem:
            custom_properties.extend([
                {"property": "sourceNullMeaning", "value": null_sem["sourceMeaning"]},
                {"property": "observationStatusPolicy", "value": null_sem["observationStatusPolicy"]},
            ])
        for source_col, null_meta in sem.get("sourceNullSemantics", {}).items():
            norm = null_meta.get("physicalKeyNormalization", {})
            if norm.get("derivedColumn") == col:
                custom_properties.extend([
                    {"property": "derivedFromNullableDimension", "value": source_col},
                    {"property": "nullReplacementForPhysicalKey", "value": norm["nullReplacement"]},
                ])
        if custom_properties:
            prop["customProperties"] = custom_properties
        props.append(prop)
    contract = {
        "version": "1.0.0",
        "apiVersion": "v3.2.0",
        "kind": "DataContract",
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"github:{TIDY_SHA}:{d['source_path']}")),
        "name": name,
        "domain": "external-public-data",
        "dataProduct": d["data_product"],
        "status": "active",
        "description": {
            "purpose": "External GitHub dataset used to exercise the Ordivon data lifecycle pilot.",
            "limitations": "Descriptive pilot contract; upstream source semantics and causal interpretation remain outside this contract.",
            "usage": "Reproducible data-lifecycle validation and descriptive analysis."
        },
        "authoritativeDefinitions": [{
            "type": "canonical",
            "url": f"https://github.com/rfordatascience/tidytuesday/blob/{TIDY_SHA}/{d['source_path']}",
            "description": "Exact Git source revision used for acquisition."
        }],
        "schema": [{
            "name": name,
            "physicalName": d["parquet"].name,
            "physicalType": "parquet",
            "description": d["title"],
            "properties": props,
        }],
        "customProperties": [
            {"property": "sourceSha256", "value": sha256(d["raw"])},
            {"property": "derivedParquetSha256", "value": sha256(d["parquet"])},
            {"property": "sourceGitCommit", "value": TIDY_SHA},
            {"property": "semanticProfile", "value": str(SEMANTICS_PATH.relative_to(ROOT))},
            {"property": "statisticalStructureOwner", "value": SEMANTICS["externalOwners"]["statisticalStructure"]},
            {"property": "unitCodeOwner", "value": SEMANTICS["externalOwners"]["unitCodes"]},
            {"property": "qualityMeasureOwner", "value": SEMANTICS["externalOwners"]["qualityMeasures"]},
        ],
    }
    write_json(CONTRACTS / f"{name}.odcs.json", contract)

def make_quality():
    q = {"schemaVersion": 1, "kind": "ordivon.data-lifecycle-quality-report", "sourceCommit": TIDY_SHA, "qualityModelOwner": SEMANTICS["externalOwners"]["qualityMeasures"], "fitnessForUse": "descriptive-analytics-pilot", "datasets": {}}
    for name, d in DATASETS.items():
        p = d["parquet"]
        sem = dataset_semantics(name)
        q["datasets"][name] = {
            "rows": row_count(p),
            "columns": len(describe(p)),
            "sourceSha256": sha256(d["raw"]),
            "parquetSha256": sha256(p),
            "duplicatePrimaryKeyRows": duplicate_count(p, sem["physicalPrimaryKey"]),
            "nullPrimaryKeyRows": null_key_count(p, sem["physicalPrimaryKey"]),
            "sourceProvidesObservationStatus": sem.get("missingStatusAvailable", False),
        }
        if sem.get("sourceNullSemantics"):
            q["datasets"][name]["sourceNullSemantics"] = sem["sourceNullSemantics"]

    member = DATASETS["crossref-member-participation"]["parquet"]
    metadata = DATASETS["crossref-metadata-coverage"]["parquet"]
    energy = DATASETS["se4all-energy"]["parquet"]

    member_cols = [r["column_name"] for r in describe(member) if r["column_name"].startswith("deposits_") or r["column_name"] == "acknowledges_funding"]
    member_pred = " OR ".join(f'coalesce("{c}",0) > coalesce(total_members,0)' for c in member_cols)
    q["datasets"]["crossref-member-participation"]["depositCountExceedsTotalMembersRows"] = int(
        run_json(f"SELECT count(*) n FROM read_parquet('{sql_quote(member)}') WHERE {member_pred}")[0]["n"]
    )

    with_cols = [r["column_name"] for r in describe(metadata) if r["column_name"].startswith("with_")]
    with_pred = " OR ".join(f'coalesce("{c}",0) > coalesce(n_dois,0)' for c in with_cols)
    q["datasets"]["crossref-metadata-coverage"]["withMetricExceedsNDoisRows"] = int(
        run_json(f"SELECT count(*) n FROM read_parquet('{sql_quote(metadata)}') WHERE {with_pred}")[0]["n"]
    )

    semantic_checks = {}
    for col, meta in dataset_semantics("se4all-energy").get("measures", {}).items():
        validity = meta.get("validity", {})
        minimum = validity.get("minimum")
        maximum = validity.get("maximum")
        tolerance = validity.get("tolerance", 0)
        clauses = []
        if minimum is not None:
            clauses.append(f'"{col}" < {minimum - tolerance}')
        if maximum is not None:
            clauses.append(f'"{col}" > {maximum + tolerance}')
        violations = 0
        if clauses:
            predicate = " OR ".join(clauses)
            violations = int(run_json(
                f'SELECT count(*) n FROM read_parquet(\'{sql_quote(energy)}\') WHERE "{col}" IS NOT NULL AND ({predicate})'
            )[0]["n"])
        bounds = run_json(
            f'SELECT min("{col}") minv, max("{col}") maxv FROM read_parquet(\'{sql_quote(energy)}\')'
        )[0]
        semantic_checks[col] = {
            "unitUcum": meta["unitUcum"],
            "unitQudt": meta["unitQudt"],
            "quantitySemantics": meta["quantitySemantics"],
            "minimum": minimum,
            "maximum": maximum,
            "tolerance": tolerance,
            "observedMin": bounds["minv"],
            "observedMax": bounds["maxv"],
            "violationRows": violations,
            "basis": validity.get("basis"),
        }
    q["datasets"]["se4all-energy"]["semanticMeasureChecks"] = semantic_checks
    q["datasets"]["se4all-energy"]["semanticMeasureViolationRows"] = sum(x["violationRows"] for x in semantic_checks.values())
    q["datasets"]["se4all-energy"]["missingObservationStatus"] = {
        "sourceProvidesStatus": dataset_semantics("se4all-energy")["missingStatusAvailable"],
        "policy": dataset_semantics("se4all-energy")["observationStatusPolicy"],
        "externalOwner": SEMANTICS["externalOwners"]["observationStatus"],
    }

    q["standing"] = "PASS" if (
        all(d["duplicatePrimaryKeyRows"] == 0 and d["nullPrimaryKeyRows"] == 0 for d in q["datasets"].values())
        and q["datasets"]["se4all-energy"]["semanticMeasureViolationRows"] == 0
    ) else "FAIL"
    write_json(BASE / "quality-report.json", q)
    return q

def make_analysis():
    member = sql_quote(DATASETS["crossref-member-participation"]["parquet"])
    metadata = sql_quote(DATASETS["crossref-metadata-coverage"]["parquet"])
    energy = sql_quote(DATASETS["se4all-energy"]["parquet"])

    crossref_sql = f"""
    COPY (
      WITH latest AS (
        SELECT max(current_up_to) AS d FROM read_parquet('{metadata}')
      ),
      m AS (
        SELECT iso3_code, total_members,
               deposits_ror_id / nullif(total_members,0) AS member_ror_share
        FROM read_parquet('{member}')
        WHERE current_up_to = (SELECT d FROM latest)
      ),
      c AS (
        SELECT iso3_code,
               sum(n_dois) AS n_dois,
               sum(with_ror_id) / nullif(sum(n_dois),0) AS work_ror_share,
               sum(with_orcid) / nullif(sum(n_dois),0) AS work_orcid_share,
               sum(with_abstract) / nullif(sum(n_dois),0) AS work_abstract_share
        FROM read_parquet('{metadata}')
        WHERE current_up_to = (SELECT d FROM latest)
        GROUP BY iso3_code
      )
      SELECT c.iso3_code, m.total_members, c.n_dois,
             m.member_ror_share, c.work_ror_share, c.work_orcid_share, c.work_abstract_share
      FROM c JOIN m USING (iso3_code)
      WHERE c.n_dois >= 1000
      ORDER BY c.work_ror_share DESC, c.n_dois DESC
    ) TO '{sql_quote(ANALYSIS / "crossref-country-metadata-rates.csv")}' (HEADER, DELIMITER ',');
    """
    subprocess.check_call([DUCKDB, "-c", crossref_sql])

    corr = run_json(f"""
      WITH latest AS (SELECT max(current_up_to) d FROM read_parquet('{metadata}')),
      m AS (
        SELECT iso3_code, deposits_ror_id / nullif(total_members,0) member_ror_share
        FROM read_parquet('{member}') WHERE current_up_to=(SELECT d FROM latest)
      ),
      c AS (
        SELECT iso3_code, sum(n_dois) n_dois,
               sum(with_ror_id)/nullif(sum(n_dois),0) work_ror_share
        FROM read_parquet('{metadata}') WHERE current_up_to=(SELECT d FROM latest)
        GROUP BY iso3_code
      )
      SELECT count(*) AS countries, corr(member_ror_share, work_ror_share) AS pearson_r
      FROM c JOIN m USING(iso3_code)
      WHERE n_dois >= 1000 AND member_ror_share IS NOT NULL AND work_ror_share IS NOT NULL
    """)[0]

    energy_sql = f"""
    COPY (
      SELECT yr,
             count(*) AS countries,
             avg(renewable_energy_consumption_tfec_pct) AS country_mean_renewable_tfec_pct,
             avg(access_electricity_total_pop_pct) AS country_mean_electricity_access_pct,
             avg(share_of_renewable_capacity_in_total_capacity_pct) AS country_mean_renewable_capacity_share_pct
      FROM read_parquet('{energy}')
      GROUP BY yr
      ORDER BY yr
    ) TO '{sql_quote(ANALYSIS / "se4all-yearly-country-means.csv")}' (HEADER, DELIMITER ',');
    """
    subprocess.check_call([DUCKDB, "-c", energy_sql])

    energy_latest = run_json(f"""
      WITH x AS (SELECT max(yr) y FROM read_parquet('{energy}'))
      SELECT (SELECT y FROM x) AS latest_year,
             count(*) AS countries,
             avg(renewable_energy_consumption_tfec_pct) AS country_mean_renewable_tfec_pct,
             avg(access_electricity_total_pop_pct) AS country_mean_electricity_access_pct
      FROM read_parquet('{energy}') WHERE yr=(SELECT y FROM x)
    """)[0]

    write_json(ANALYSIS / "analysis-summary.json", {
        "crossref": {
            "eligibleCountryCount": corr["countries"],
            "memberVsWorkRorSharePearsonR": round(float(corr["pearson_r"]), 12),
        },
        "se4all": {
            **energy_latest,
            "country_mean_renewable_tfec_pct": round(float(energy_latest["country_mean_renewable_tfec_pct"]), 12),
            "country_mean_electricity_access_pct": round(float(energy_latest["country_mean_electricity_access_pct"]), 12),
        },
        "interpretationBoundary": "Descriptive outputs only; no causal inference is claimed."
    })

def make_catalog():
    datasets = []
    for name, d in DATASETS.items():
        raw_sha = sha256(d["raw"])
        pq_sha = sha256(d["parquet"])
        pinned = f"https://raw.githubusercontent.com/rfordatascience/tidytuesday/{TIDY_SHA}/{d['source_path']}"
        datasets.append({
            "@id": f"urn:ordivon:dataset:{name}:{raw_sha}",
            "@type": "dcat:Dataset",
            "dct:title": d["title"],
            "dct:identifier": f"sha256:{raw_sha}",
            "dct:source": {"@id": pinned},
            "dct:rights": "TidyTuesday curation requires source data to be publicly available and free for reuse; upstream license terms remain source-specific and are not inferred here.",
            "dcat:distribution": [
                {
                    "@type": "dcat:Distribution",
                    "dct:format": "text/csv",
                    "dcat:downloadURL": {"@id": pinned},
                    "dct:identifier": f"sha256:{raw_sha}",
                },
                {
                    "@type": "dcat:Distribution",
                    "dct:format": "application/vnd.apache.parquet",
                    "dct:identifier": f"sha256:{pq_sha}",
                }
            ]
        })
    catalog = {
        "@context": {
            "dcat": "http://www.w3.org/ns/dcat#",
            "dct": "http://purl.org/dc/terms/"
        },
        "@id": "urn:ordivon:catalog:github-pilot-r1",
        "@type": "dcat:Catalog",
        "dct:title": "Ordivon GitHub Data Lifecycle Pilot R1",
        "dct:identifier": TIDY_SHA,
        "dcat:dataset": datasets,
    }
    write_json(CATALOG / "catalog.dcat.jsonld", catalog)

def lineage_event(job_name: str, event_type: str, inputs: list[dict], outputs: list[dict]):
    run_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{TIDY_SHA}:{job_name}"))
    return {
        "eventType": event_type,
        "eventTime": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "run": {"runId": run_id},
        "job": {"namespace": "urn:ordivon:data-lifecycle:github-pilot-r1", "name": job_name},
        "inputs": inputs,
        "outputs": outputs,
        "producer": PRODUCER,
        "schemaURL": OL_SCHEMA_URL,
    }

def ds_ref(name: str, d: dict, derived=False):
    if derived:
        digest = sha256(d["parquet"])
        return {"namespace": "urn:ordivon:data-lifecycle:github-pilot-r1", "name": f"{d['parquet'].name}@sha256:{digest}"}
    return {
        "namespace": f"https://github.com/rfordatascience/tidytuesday/tree/{TIDY_SHA}",
        "name": d["source_path"],
    }

def make_lineage():
    groups = {
        "crossref-transform": ["crossref-member-participation", "crossref-metadata-coverage"],
        "se4all-transform": ["se4all-energy"],
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    run_dir = RUNTIME_LINEAGE / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    for job, names in groups.items():
        ins = [ds_ref(n, DATASETS[n], False) for n in names]
        outs = [ds_ref(n, DATASETS[n], True) for n in names]
        events = [
            lineage_event(job, "START", ins, []),
            lineage_event(job, "COMPLETE", ins, outs),
        ]
        write_json(run_dir / f"{job}.openlineage.json", events)

def make_manifest(q):
    files = {}
    for p in sorted(BASE.rglob("*")):
        if not p.is_file() or p.name == "manifest.json":
            continue
        rel = p.relative_to(BASE)
        if rel.parts and rel.parts[0] in {"runtime-lineage", "runtime-acquisition"}:
            continue
        files[str(rel)] = {"bytes": p.stat().st_size, "sha256": sha256(p)}
    write_json(BASE / "manifest.json", {
        "schemaVersion": 1,
        "kind": "ordivon.data-lifecycle-github-pilot",
        "sourceRepository": "https://github.com/rfordatascience/tidytuesday",
        "sourceCommit": TIDY_SHA,
        "qualityStanding": q["standing"],
        "files": files,
    })

def main():
    ensure_raw()
    convert_all()
    for name, d in DATASETS.items():
        make_odcs(name, d)
    q = make_quality()
    make_analysis()
    make_catalog()
    make_lineage()
    make_manifest(q)
    print(json.dumps({
        "standing": q["standing"],
        "sourceCommit": TIDY_SHA,
        "datasets": {k: q["datasets"][k] for k in sorted(q["datasets"])},
    }, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
