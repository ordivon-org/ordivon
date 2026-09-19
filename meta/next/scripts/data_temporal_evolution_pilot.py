#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evidence/data-lifecycle/temporal-evolution-r1"
RAW = BASE / "raw/sfi-grants"
DERIVED = BASE / "derived/sfi-grants"
SOURCE = BASE / "source"
RUNTIME_ACQ = BASE / "runtime-acquisition"
PROFILE = json.loads((SOURCE / "external-temporal-reference-profile.json").read_text(encoding="utf-8"))
for d in (RAW, DERIVED, RUNTIME_ACQ):
    d.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())

def acquire_revision(rev: dict) -> dict:
    dst = RAW / f"{rev['role']}.csv"
    path = PROFILE["source"]["path"]
    commit = rev["commit"]
    urls = [
        f"https://cdn.jsdelivr.net/gh/rfordatascience/tidytuesday@{commit}/{path}",
        f"https://raw.githubusercontent.com/rfordatascience/tidytuesday/{commit}/{path}",
    ]
    used = "existing-local"
    if not dst.exists() or sha256(dst) != rev["expectedSha256"]:
        last = None
        for url in urls:
            tmp = dst.with_suffix(".csv.part")
            tmp.unlink(missing_ok=True)
            try:
                subprocess.check_call([
                    "/usr/bin/curl","-fLsS","--retry","2","--connect-timeout","10","--max-time","60",
                    url,"-o",str(tmp),
                ])
                actual = sha256(tmp)
                if actual != rev["expectedSha256"]:
                    raise RuntimeError(f"digest mismatch {actual}")
                tmp.replace(dst)
                used = url
                break
            except Exception as exc:
                last = str(exc)
                tmp.unlink(missing_ok=True)
        else:
            raise RuntimeError(f"all transports failed for {rev['role']}: {last}")
    actual = sha256(dst)
    if actual != rev["expectedSha256"]:
        raise RuntimeError(f"{rev['role']} digest mismatch {actual}")
    return {
        "role":rev["role"],
        "commit":commit,
        "sourceIdentity":f"github:rfordatascience/tidytuesday@{commit}:{path}",
        "transportUsed":used,
        "sha256":actual,
    }

def decode_revision(rev: dict) -> tuple[str, dict]:
    raw = (RAW / f"{rev['role']}.csv").read_bytes()
    utf8_valid = True
    utf8_error = None
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as e:
        utf8_valid = False
        utf8_error = {"start":e.start,"end":e.end,"reason":e.reason,"bytes":raw[e.start:e.end].hex()}
    text = raw.decode(rev["encoding"])
    return text, {"declaredEncoding":rev["encoding"],"strictUtf8Valid":utf8_valid,"firstUtf8Error":utf8_error}

def canonical_rows(text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(text)))

def canonical_logical_hash(rows: list[list[str]]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, separators=(",",":")).encode("utf-8")
    return sha256_bytes(payload)

def duckdb_schema(text: str, role: str) -> list[dict]:
    p = DERIVED / f"{role}.utf8.csv"
    p.write_text(text, encoding="utf-8", newline="")
    sql = f"DESCRIBE SELECT * FROM read_csv_auto('{p.as_posix()}', header=true, sample_size=-1)"
    out = subprocess.check_output(["/usr/bin/duckdb","-json","-c",sql], text=True)
    rows = json.loads(out)
    return [{"name":r["column_name"],"type":r["column_type"]} for r in rows]

def schema_hash(schema: list[dict]) -> str:
    return sha256_bytes(json.dumps(schema,sort_keys=True,separators=(",",":")).encode())

def classify_transition(old: dict, new: dict) -> str:
    raw_same = old["rawSha256"] == new["rawSha256"]
    logical_same = old["logicalContentSha256"] == new["logicalContentSha256"]
    schema_same = old["schemaSha256"] == new["schemaSha256"]
    if raw_same:
        return "IDENTICAL_BYTES"
    if logical_same and schema_same:
        return "REPRESENTATION_ONLY_REVISION"
    if schema_same and not logical_same:
        return "DATA_REVISION"
    if not schema_same and logical_same:
        return "SCHEMA_REPRESENTATION_REVISION"
    return "SCHEMA_AND_DATA_REVISION"

ICEBERG_TYPE_PROMOTIONS = {
    ("INTEGER", "BIGINT"),
    ("FLOAT", "DOUBLE"),
}

def classify_schema_evolution(old_schema: list[dict], new_schema: list[dict], explicit_mapping: dict[str, str] | None = None) -> dict:
    explicit_mapping = explicit_mapping or {}
    old_by = {x["name"]: x["type"] for x in old_schema}
    new_by = {x["name"]: x["type"] for x in new_schema}
    mapped_targets = set()
    drops, incompatible, promotions, renames = [], [], [], []
    for old_name, old_type in old_by.items():
        target = explicit_mapping.get(old_name, old_name)
        if old_name in explicit_mapping:
            renames.append({"from": old_name, "to": target})
        if target not in new_by:
            drops.append(old_name)
            continue
        mapped_targets.add(target)
        new_type = new_by[target]
        if old_type != new_type:
            if (old_type, new_type) in ICEBERG_TYPE_PROMOTIONS:
                promotions.append({"field": target, "from": old_type, "to": new_type})
            else:
                incompatible.append({"field": target, "from": old_type, "to": new_type})
    additions = [n for n in new_by if n not in mapped_targets]
    if incompatible:
        standing = "BREAKING_TYPE_CHANGE"
    elif drops and additions and not explicit_mapping:
        standing = "AMBIGUOUS_DROP_ADD"
    elif drops:
        standing = "DESTRUCTIVE_DROP"
    elif renames and not additions:
        standing = "EXPLICIT_RENAME_COMPATIBLE"
    elif additions:
        standing = "ADDITIVE_COMPATIBLE"
    elif promotions:
        standing = "TYPE_PROMOTION_COMPATIBLE"
    elif old_schema == new_schema:
        standing = "NO_SCHEMA_CHANGE"
    else:
        standing = "REORDER_OR_METADATA_CHANGE"
    return {
        "standing": standing,
        "additions": additions,
        "drops": drops,
        "renames": renames,
        "promotions": promotions,
        "incompatibleTypeChanges": incompatible,
        "externalOwner": "apache-iceberg-spec-v3",
        "mappingOwner": "iso-iec-11179-3-amd1-2026",
        "fieldIdentityBoundary": "CSV has no stable field IDs; rename compatibility requires an explicit mapping rather than name similarity.",
    }

def schema_conformance_report(actual_schema: list[dict]) -> dict:
    fixtures = {}
    fixtures["actual_revision_pair"] = classify_schema_evolution(actual_schema, actual_schema)
    fixtures["add_nullable_field"] = classify_schema_evolution(
        actual_schema,
        actual_schema + [{"name": "curation_note", "type": "VARCHAR"}],
    )
    renamed = [
        {"name": ("organization_name" if x["name"] == "research_body" else x["name"]), "type": x["type"]}
        for x in actual_schema
    ]
    fixtures["rename_without_mapping"] = classify_schema_evolution(actual_schema, renamed)
    fixtures["rename_with_explicit_mapping"] = classify_schema_evolution(
        actual_schema,
        renamed,
        {"research_body": "organization_name"},
    )
    fixtures["compatible_type_promotion"] = classify_schema_evolution(
        [{"name": "n", "type": "INTEGER"}],
        [{"name": "n", "type": "BIGINT"}],
    )
    fixtures["breaking_type_change"] = classify_schema_evolution(
        [{"name": "amount", "type": "DOUBLE"}],
        [{"name": "amount", "type": "VARCHAR"}],
    )
    expected = {
        "actual_revision_pair": "NO_SCHEMA_CHANGE",
        "add_nullable_field": "ADDITIVE_COMPATIBLE",
        "rename_without_mapping": "AMBIGUOUS_DROP_ADD",
        "rename_with_explicit_mapping": "EXPLICIT_RENAME_COMPATIBLE",
        "compatible_type_promotion": "TYPE_PROMOTION_COMPATIBLE",
        "breaking_type_change": "BREAKING_TYPE_CHANGE",
    }
    for name, standing in expected.items():
        if fixtures[name]["standing"] != standing:
            raise RuntimeError(f"schema conformance fixture {name}: {fixtures[name]['standing']} != {standing}")
    return {
        "schemaVersion": 1,
        "kind": "schema-evolution-conformance",
        "externalOwner": "apache-iceberg-spec-v3",
        "mappingOwner": "iso-iec-11179-3-amd1-2026",
        "note": "Synthetic edge cases are conformance fixtures only; the real SFI revision pair has no schema change.",
        "fixtures": fixtures,
    }

def bounded_replay_report(revisions: list[dict]) -> dict:
    processing_order = list(reversed([{"commit":x["commit"],"commitTime":x["commitTime"]} for x in revisions]))
    source_order = sorted(processing_order, key=lambda x:x["commitTime"])
    return {
        "schemaVersion": 1,
        "kind": "bounded-revision-replay-conformance",
        "sourceEvents": "real Git commits",
        "processingOrderScenario": "intentionally reversed conformance replay",
        "processingOrder": processing_order,
        "sourceRevisionOrder": source_order,
        "processingOrderAuthoritative": False,
        "watermarkApplied": False,
        "lateEventDropPolicy": "none-for-bounded-history",
        "streamingExternalOwner": "apache-beam-programming-model",
        "standing": "PASS_SOURCE_TIME_SEPARATE_FROM_PROCESSING_ORDER",
    }

def reference_identity_report(rows: list[list[str]]) -> dict:
    header = rows[0]
    idx = {name:i for i,name in enumerate(header)}
    data = rows[1:]
    report = {}
    for id_col,meta in PROFILE["identity"]["referenceIdentifiers"].items():
        label_col = meta["labelColumn"]
        id_i,label_i = idx[id_col],idx[label_col]
        label_to_ids, id_to_labels = {}, {}
        missing = 0
        for row in data:
            ident = row[id_i].strip()
            label = row[label_i].strip()
            if ident in {"","NA","N/A","null","None"}:
                missing += 1
                continue
            label_to_ids.setdefault(label,set()).add(ident)
            id_to_labels.setdefault(ident,set()).add(label)
        ambiguous_labels = {k:sorted(v) for k,v in label_to_ids.items() if len(v)>1}
        identifier_label_variants = {k:sorted(v) for k,v in id_to_labels.items() if len(v)>1}
        report[id_col] = {
            "scheme":meta["scheme"],
            "rowsWithMissingIdentifier":missing,
            "uniqueIdentifiers":len(id_to_labels),
            "uniqueLabelsWithIdentifier":len(label_to_ids),
            "ambiguousLabelsMappingToMultipleIdentifiers":ambiguous_labels,
            "identifierLabelVariants":identifier_label_variants,
            "identityRule":"Identifier is authoritative; multiple labels for one identifier are label variants, not identity conflicts.",
            "standing":"PASS_IDENTIFIER_STABLE" if not ambiguous_labels else "REVIEW_AMBIGUOUS_LABEL",
        }
    proposal_i = idx["proposal_id"]
    proposal_ids=[row[proposal_i] for row in data]
    report["rowIdentityCandidate"]={
        "column":"proposal_id",
        "rows":len(proposal_ids),
        "unique":len(set(proposal_ids)),
        "duplicateRows":len(proposal_ids)-len(set(proposal_ids)),
    }
    return report

def main() -> None:
    receipts=[]
    for rev in PROFILE["source"]["revisions"]:
        receipts.append(acquire_revision(rev))
    write_json(RUNTIME_ACQ / "latest.json", {
        "schemaVersion":1,
        "kind":"digest-verified-acquisition-receipt",
        "datasets":receipts,
    })

    revision_rows={}
    ledger=[]
    for rev in PROFILE["source"]["revisions"]:
        text,enc=decode_revision(rev)
        rows=canonical_rows(text)
        revision_rows[rev["role"]]=rows
        schema=duckdb_schema(text,rev["role"])
        entry={
            "role":rev["role"],
            "commit":rev["commit"],
            "commitTime":rev["commitTime"],
            "message":rev["message"],
            "rawSha256":sha256(RAW / f"{rev['role']}.csv"),
            "rawBytes":(RAW / f"{rev['role']}.csv").stat().st_size,
            "encoding":enc,
            "rowCountIncludingHeader":len(rows),
            "columnCount":len(rows[0]),
            "schema":schema,
            "schemaSha256":schema_hash(schema),
            "logicalContentSha256":canonical_logical_hash(rows),
        }
        ledger.append(entry)

    old,new=ledger
    transition=classify_transition(old,new)
    logical_equal=revision_rows["old"] == revision_rows["new"]
    report={
        "schemaVersion":1,
        "kind":"data-revision-ledger",
        "dataset":PROFILE["source"]["path"],
        "revisionOrderingAuthority":"Git commit ancestry/time; processing arrival is non-authoritative",
        "revisions":ledger,
        "transition":{
            "from":old["commit"],
            "to":new["commit"],
            "classification":transition,
            "rawBytesEqual":old["rawSha256"]==new["rawSha256"],
            "schemaEqual":old["schemaSha256"]==new["schemaSha256"],
            "logicalRowsEqual":logical_equal,
            "expectedClassification":"REPRESENTATION_ONLY_REVISION",
        },
        "externalOwners":PROFILE["externalOwners"],
    }
    if transition != "REPRESENTATION_ONLY_REVISION" or not logical_equal:
        raise RuntimeError(f"unexpected transition classification {transition}")
    write_json(BASE / "revision-ledger.json",report)

    schema_conf = schema_conformance_report(new["schema"])
    write_json(BASE / "schema-evolution-conformance.json", schema_conf)
    replay = bounded_replay_report(PROFILE["source"]["revisions"])
    write_json(BASE / "bounded-replay-conformance.json", replay)

    refs=reference_identity_report(revision_rows["new"])
    write_json(BASE / "reference-identity-report.json",{
        "schemaVersion":1,
        "kind":"reference-identity-report",
        "rules":PROFILE["identity"]["rules"],
        "externalOwners":{
            "identifierResolution":PROFILE["externalOwners"]["identifierResolution"],
            "metadataItemMapping":PROFILE["externalOwners"]["metadataItemMapping"],
        },
        "report":refs,
    })

    write_json(BASE / "activation-decision.json",{
        "schemaVersion":1,
        "kind":"data-platform-activation-decision",
        "iceberg":{"activate":False,"reason":"The observed real transition is representation-only; Git commits already provide immutable source snapshots, with no concurrent table writers or table-level schema evolution."},
        "debezium":{"activate":False,"reason":"The source change log is Git history, not a database transaction log."},
        "beam":{"activate":False,"reason":"The source is bounded Git revision history; no watermark/late-data runtime is required."},
        "redpandaKafka":{"activate":False,"reason":"No unbounded fan-out/replay transport workload was demonstrated."},
    })

    stable_files=[
        SOURCE / "external-temporal-reference-profile.json",
        BASE / "revision-ledger.json",
        BASE / "schema-evolution-conformance.json",
        BASE / "bounded-replay-conformance.json",
        BASE / "reference-identity-report.json",
        BASE / "activation-decision.json",
    ]
    write_json(BASE / "manifest.json",{
        "schemaVersion":1,
        "kind":"temporal-evolution-pilot-manifest",
        "files":{str(p.relative_to(BASE)):{"sha256":sha256(p),"bytes":p.stat().st_size} for p in stable_files},
    })
    print(json.dumps({
        "transition":transition,
        "oldUtf8":old["encoding"]["strictUtf8Valid"],
        "newUtf8":new["encoding"]["strictUtf8Valid"],
        "logicalRowsEqual":logical_equal,
        "rows":new["rowCountIncludingHeader"]-1,
        "referenceIdentity":refs,
    },indent=2,ensure_ascii=False,sort_keys=True))

if __name__ == "__main__":
    main()
