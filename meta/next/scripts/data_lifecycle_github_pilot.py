#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import uuid
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evidence/data-lifecycle/github-pilot-r1"
RAW = BASE / "raw"
OUT = BASE / "derived"
CONTRACTS = BASE / "contracts"
CATALOG = BASE / "catalog"
LINEAGE = BASE / "lineage"
ANALYSIS = BASE / "analysis"
SOURCE = BASE / "source"
for d in (OUT, CONTRACTS, CATALOG, LINEAGE, ANALYSIS):
    d.mkdir(parents=True, exist_ok=True)

TIDY_SHA = (SOURCE / "tidytuesday-main.sha").read_text().strip()
DUCKDB = "/usr/bin/duckdb"
OL_SCHEMA_URL = "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunEvent"
PRODUCER = "urn:ordivon:data-lifecycle:github-pilot-r1"

DATASETS = {
    "crossref-member-participation": {
        "raw": RAW / "crossref-member-participation.csv",
        "parquet": OUT / "crossref-member-participation.parquet",
        "source_path": "data/2026/2026-05-19/member_participation_stats_by_country.csv",
        "title": "Crossref member participation statistics by country",
        "keys": ["current_up_to", "iso3_code"],
        "data_product": "crossref-metadata-country",
        "source_sha256": "0f220075cedec9443c1a7343771cff7cce1c3892d6e0717f7e6fecbcdb0ad2af",
    },
    "crossref-metadata-coverage": {
        "raw": RAW / "crossref-metadata-coverage.csv",
        "parquet": OUT / "crossref-metadata-coverage.parquet",
        "source_path": "data/2026/2026-05-19/metadata_coverage_stats_by_country.csv",
        "title": "Crossref metadata coverage statistics by country and document type",
        "keys": ["current_up_to", "iso3_code", "document_type", "document_subtype_key"],
        "data_product": "crossref-metadata-country",
        "source_sha256": "2e37a30acc28f47bf724ca1038fbe840ab1be84cd66790ae69aa62a6731f0ad4",
    },
    "se4all-energy": {
        "raw": RAW / "se4all-energy.csv",
        "parquet": OUT / "se4all-energy.parquet",
        "source_path": "data/2026/2026-05-26/energy_cleaned.csv",
        "title": "Sustainable Energy for All country historical indicators",
        "keys": ["country_code", "yr"],
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
    for name, d in DATASETS.items():
        pinned = f"https://raw.githubusercontent.com/rfordatascience/tidytuesday/{TIDY_SHA}/{d['source_path']}"
        if not d["raw"].exists():
            tmp = d["raw"].with_suffix(d["raw"].suffix + ".part")
            urllib.request.urlretrieve(pinned, tmp)
            tmp.replace(d["raw"])
        actual = sha256(d["raw"])
        if actual != d["source_sha256"]:
            raise RuntimeError(f"{name}: source digest mismatch: {actual} != {d['source_sha256']}")

def convert_all():
    for name, d in DATASETS.items():
        raw = sql_quote(d["raw"])
        out = sql_quote(d["parquet"])
        if d["parquet"].exists():
            d["parquet"].unlink()
        select_expr = "*"
        if name == "crossref-metadata-coverage":
            select_expr = "*, coalesce(document_subtype, '') AS document_subtype_key"
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

def make_odcs(name: str, d: dict):
    schema_rows = describe(d["parquet"])
    keys = d["keys"]
    props = []
    for row in schema_rows:
        col = row["column_name"]
        props.append({
            "name": col,
            "physicalName": col,
            "logicalType": logical_type(row["column_type"]),
            "physicalType": row["column_type"].lower(),
            "primaryKey": col in keys,
            "primaryKeyPosition": keys.index(col) + 1 if col in keys else -1,
            "required": null_key_count(d["parquet"], [col]) == 0,
            "classification": "public",
        })
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
        ],
    }
    write_json(CONTRACTS / f"{name}.odcs.json", contract)

def make_quality():
    q = {"schemaVersion": 1, "kind": "ordivon.data-lifecycle-quality-report", "sourceCommit": TIDY_SHA, "datasets": {}}
    for name, d in DATASETS.items():
        p = d["parquet"]
        q["datasets"][name] = {
            "rows": row_count(p),
            "columns": len(describe(p)),
            "sourceSha256": sha256(d["raw"]),
            "parquetSha256": sha256(p),
            "duplicatePrimaryKeyRows": duplicate_count(p, d["keys"]),
            "nullPrimaryKeyRows": null_key_count(p, d["keys"]),
        }

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

    bounded_pct_cols = [
        r["column_name"] for r in describe(energy)
        if (
            r["column_name"].startswith("access_")
            or r["column_name"].endswith("_consumption_tfec_pct")
            or r["column_name"] in {
                "perc_renewable_of_total_electricity_output",
                "share_of_renewable_capacity_in_total_capacity_pct",
                "final_to_primary_energy_ratio_pct",
            }
        )
    ]
    pct_pred = " OR ".join(
        f'("{c}" IS NOT NULL AND ("{c}" < 0 OR "{c}" > 100.1))' for c in bounded_pct_cols
    )
    q["datasets"]["se4all-energy"]["boundedPercentageOutsideToleranceRows"] = int(
        run_json(f"SELECT count(*) n FROM read_parquet('{sql_quote(energy)}') WHERE {pct_pred}")[0]["n"]
    )
    q["datasets"]["se4all-energy"]["observedRangeWarnings"] = {
        "access_non_solid_fuel_urban_pop_pct_max": run_json(
            f"SELECT max(access_non_solid_fuel_urban_pop_pct) v FROM read_parquet('{sql_quote(energy)}')"
        )[0]["v"],
        "transmission_and_distribution_losses_pct_max": run_json(
            f"SELECT max(transmission_and_distribution_losses_pct) v FROM read_parquet('{sql_quote(energy)}')"
        )[0]["v"],
        "note": "Transmission/distribution losses are not constrained by the generic 0-100 percentage rule; bounded proportion-like fields use a 0.1 percentage-point tolerance for source rounding."
    }

    q["standing"] = "PASS" if all(
        d["duplicatePrimaryKeyRows"] == 0 and d["nullPrimaryKeyRows"] == 0 for d in q["datasets"].values()
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
        "crossref": {"eligibleCountryCount": corr["countries"], "memberVsWorkRorSharePearsonR": corr["pearson_r"]},
        "se4all": energy_latest,
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
    for job, names in groups.items():
        ins = [ds_ref(n, DATASETS[n], False) for n in names]
        outs = [ds_ref(n, DATASETS[n], True) for n in names]
        events = [
            lineage_event(job, "START", ins, []),
            lineage_event(job, "COMPLETE", ins, outs),
        ]
        write_json(LINEAGE / f"{job}.openlineage.json", events)

def make_manifest(q):
    files = {}
    for p in sorted(BASE.rglob("*")):
        if p.is_file() and p.name != "manifest.json":
            files[str(p.relative_to(BASE))] = {"bytes": p.stat().st_size, "sha256": sha256(p)}
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
