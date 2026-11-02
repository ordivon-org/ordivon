#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

# Accept both direct CLI invocation and import as scripts.authority_catalog.
if __package__:
    from .authority_catalog_search import score_entry
    from .authority_catalog_sources import (
        AUTH,
        FORBIDDEN_TASK_FIELDS,
        OBS,
        RECORDS,
        ROOT,
        forbidden_fields,
        latest_observation,
        observation_paths,
        read_json,
        record_paths,
        records,
        validate_catalog_semantics,
    )
else:
    from authority_catalog_search import score_entry
    from authority_catalog_sources import (
        AUTH,
        FORBIDDEN_TASK_FIELDS,
        OBS,
        RECORDS,
        ROOT,
        forbidden_fields,
        latest_observation,
        observation_paths,
        read_json,
        record_paths,
        records,
        validate_catalog_semantics,
    )

INDEX = AUTH / "generated" / "authority-index.json"

# Retain source-inspection API for existing importers, while keeping its implementation
# within the source boundary. The CLI and index projection live in this module.
__all__ = [
    "AUTH",
    "OBS",
    "RECORDS",
    "ROOT",
    "INDEX",
    "FORBIDDEN_TASK_FIELDS",
    "forbidden_fields",
    "latest_observation",
    "observation_paths",
    "read_json",
    "record_paths",
    "records",
    "validate_catalog_semantics",
    "score_entry",
    "build_index",
    "write_index",
    "load_index",
    "get_record",
    "canonical_bytes",
    "sha256_bytes",
    "parser",
    "main",
]


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def build_index() -> dict:
    catalog = records()
    validate_catalog_semantics(catalog)
    entries = []
    digest_material = []
    for authority_id in sorted(catalog):
        path, record = catalog[authority_id]
        record_digest = sha256_bytes(path.read_bytes())
        latest = latest_observation(authority_id)
        obs_digest = None
        lifecycle = None
        currentness = None
        if latest is not None:
            observation_path, observation = latest
            obs_digest = sha256_bytes(observation_path.read_bytes())
            lifecycle = observation.get("lifecycleStatus")
            currentness = observation.get("observedDate")
        identity = record["identity"]
        discovery = record["discovery"]
        entry = {
            "id": authority_id,
            "title": identity["title"],
            "issuer": identity["issuer"]["name"],
            "authorityKind": identity["authorityKind"],
            "identityMode": identity["identityMode"],
            "versionLabel": identity["versionLabel"],
            "aliases": sorted(discovery["aliases"], key=str.casefold),
            "topics": sorted(discovery["topics"]),
            "domains": sorted(discovery["domains"]),
            "lifecycleStatus": lifecycle,
            "currentnessChecked": currentness,
            "recordDigest": record_digest,
            "observationDigest": obs_digest,
        }
        entries.append(entry)
        digest_material.append(
            {
                "id": authority_id,
                "recordDigest": record_digest,
                "observationDigest": obs_digest,
            }
        )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.external-authority-discovery-index",
        "recordCount": len(entries),
        "recordsDigest": sha256_bytes(canonical_bytes(digest_material)),
        "entries": entries,
        "boundary": "Generated Level-0 discovery projection only. It does not establish task applicability, compliance, certification, authorization or domain acceptance.",
    }


def write_index(index: dict, path: Path = INDEX) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        json.dumps(index, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")
        + b"\n"
    )


def load_index() -> dict:
    """Derive Level-0 discovery from authoritative records and observations.

    The optional CLI build artifact is a cache/projection, never an admitted
    repository source or a prerequisite for list/find.
    """
    return build_index()


def emit(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def cmd_build(_: argparse.Namespace) -> int:
    index = build_index()
    write_index(index)
    emit(
        {
            "standing": "BUILT",
            "path": str(INDEX.relative_to(ROOT.parent.parent)),
            "recordCount": index["recordCount"],
            "recordsDigest": index["recordsDigest"],
        }
    )
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    rows = load_index()["entries"]
    if args.issuer:
        rows = [r for r in rows if args.issuer.casefold() in r["issuer"].casefold()]
    if args.topic:
        rows = [
            r
            for r in rows
            if args.topic.casefold() in [x.casefold() for x in r["topics"]]
        ]
    if args.kind:
        rows = [r for r in rows if r["authorityKind"] == args.kind]
    emit(rows)
    return 0


def cmd_find(args: argparse.Namespace) -> int:
    scored = [(score_entry(row, args.query), row) for row in load_index()["entries"]]
    rows = [
        {"score": score, **row}
        for score, row in sorted(scored, key=lambda x: (-x[0], x[1]["id"]))
        if score > 0
    ][: args.limit]
    emit(rows)
    return 0


def get_record(authority_id: str) -> tuple[Path, dict]:
    catalog = records()
    if authority_id not in catalog:
        raise SystemExit(f"authority not found: {authority_id}")
    return catalog[authority_id]


def cmd_show(args: argparse.Namespace) -> int:
    path, record = get_record(args.id)
    latest = latest_observation(args.id)
    emit(
        {
            "recordPath": str(path.relative_to(ROOT.parent.parent)),
            "record": record,
            "latestObservationPath": str(latest[0].relative_to(ROOT.parent.parent))
            if latest
            else None,
            "latestObservation": latest[1] if latest else None,
            "boundary": "Loaded catalog identity/currentness only. Task-local applicability and claim semantics are intentionally absent.",
        }
    )
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    path, record = get_record(args.id)
    latest = latest_observation(args.id)
    emit(
        {
            "kind": "ordivon.external-authority-refresh-plan",
            "authorityId": args.id,
            "recordPath": str(path.relative_to(ROOT.parent.parent)),
            "officialSource": record["identity"]["officialSource"],
            "latestObservation": latest[1] if latest else None,
            "requiredAction": [
                "Check the official source semantically; HTTP reachability alone is insufficient.",
                "If lifecycle/version/currentness changed, append a new dated observation under catalogs/authorities/observations/<id>/.",
                "Do not rewrite historical observations.",
                "Do not update task-local profiles automatically; reassess applicability/currentness in the affected Work.",
            ],
            "mutated": False,
        }
    )
    return 0


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lightweight external authority catalog"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build_parser = sub.add_parser("build")
    build_parser.set_defaults(fn=cmd_build)

    list_parser = sub.add_parser("list")
    list_parser.add_argument("--issuer")
    list_parser.add_argument("--topic")
    list_parser.add_argument("--kind")
    list_parser.set_defaults(fn=cmd_list)

    find_parser = sub.add_parser("find")
    find_parser.add_argument("query")
    find_parser.add_argument("--limit", type=int, default=10)
    find_parser.set_defaults(fn=cmd_find)

    show_parser = sub.add_parser("show")
    show_parser.add_argument("id")
    show_parser.set_defaults(fn=cmd_show)

    refresh_parser = sub.add_parser("refresh")
    refresh_parser.add_argument("id")
    refresh_parser.set_defaults(fn=cmd_refresh)
    return parser


def main() -> int:
    args = parser().parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
