#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT
AUTH = REPO_ROOT / "catalogs" / "authorities"
RECORDS = AUTH / "records"
OBS = AUTH / "observations"
INDEX = AUTH / "generated" / "authority-index.json"

FORBIDDEN_TASK_FIELDS = {
    "applicability",
    "appliesto",
    "disposition",
    "required",
    "role",
    "rationale",
    "verdict",
    "workflow",
}


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def record_paths() -> list[Path]:
    return sorted(RECORDS.glob("**/*.json"))


def observation_paths(authority_id: str) -> list[Path]:
    return sorted((OBS / authority_id).glob("*.json"))


def records() -> dict[str, tuple[Path, dict]]:
    out: dict[str, tuple[Path, dict]] = {}
    for path in record_paths():
        value = read_json(path)
        authority_id = value.get("id")
        if not isinstance(authority_id, str) or not authority_id:
            raise SystemExit(f"record has no id: {path}")
        if authority_id in out:
            raise SystemExit(
                f"duplicate authority id {authority_id}: {path} and {out[authority_id][0]}"
            )
        out[authority_id] = (path, value)
    return out


def latest_observation(authority_id: str) -> tuple[Path, dict] | None:
    found: list[tuple[str, Path, dict]] = []
    for path in observation_paths(authority_id):
        value = read_json(path)
        if value.get("authorityId") != authority_id:
            raise SystemExit(f"observation authorityId mismatch: {path}")
        date = value.get("observedDate")
        if not isinstance(date, str):
            raise SystemExit(f"observation has no observedDate: {path}")
        found.append((date, path, value))
    if not found:
        return None
    _, path, value = sorted(found, key=lambda x: (x[0], str(x[1])))[-1]
    return path, value


def forbidden_fields(value: object, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", key.lower())
            here = f"{prefix}.{key}" if prefix else key
            if normalized in FORBIDDEN_TASK_FIELDS:
                hits.append(here)
            hits.extend(forbidden_fields(child, here))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            hits.extend(forbidden_fields(child, f"{prefix}[{i}]"))
    return hits


def validate_catalog_semantics(catalog: dict[str, tuple[Path, dict]]) -> None:
    ids = set(catalog)
    for authority_id, (path, value) in catalog.items():
        if (
            value.get("kind") != "ordivon.external-authority-record"
            or value.get("schemaVersion") != 1
        ):
            raise SystemExit(f"wrong record kind/schema: {path}")
        identity = value.get("identity", {})
        mode = identity.get("identityMode")
        version = identity.get("versionLabel")
        if mode == "versioned" and not version:
            raise SystemExit(
                f"versioned authority must have versionLabel: {authority_id}"
            )
        if mode == "rolling-source" and version is not None:
            raise SystemExit(
                f"rolling-source authority must use null versionLabel: {authority_id}"
            )
        hits = forbidden_fields(value)
        if hits:
            raise SystemExit(
                f"task-local semantics leaked into authority record {authority_id}: {hits}"
            )
        for relation in ("supersedes", "supersededBy", "related"):
            for target in value.get("relations", {}).get(relation, []):
                if target == authority_id:
                    raise SystemExit(f"self relation {relation}: {authority_id}")
                if target not in ids:
                    raise SystemExit(
                        f"unresolved relation {authority_id} {relation} {target}"
                    )
        previous_date = None
        for obs_path in observation_paths(authority_id):
            obs = read_json(obs_path)
            if obs.get("authorityId") != authority_id:
                raise SystemExit(f"observation mismatch: {obs_path}")
            date = obs.get("observedDate")
            if previous_date is not None and date < previous_date:
                raise SystemExit(f"observation order regression: {obs_path}")
            previous_date = date
            if obs.get("officialSource") != identity.get("officialSource"):
                raise SystemExit(
                    f"observation source differs from record officialSource: {obs_path}"
                )


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
    if not INDEX.is_file():
        raise SystemExit(
            f"generated index missing: {INDEX}; run authority_catalog.py build"
        )
    return read_json(INDEX)


def tokens(text: str) -> list[str]:
    # Discovery treats punctuation and taxonomy separators as token boundaries.
    # Exact identifiers/aliases are scored separately, so semantic lookup benefits
    # from matching `bill-of-materials` with `bill of materials` and similar forms.
    return re.findall(r"[a-z0-9]+", text.casefold())


def normalized_text(text: str) -> str:
    return " ".join(tokens(text))


QUERY_MODIFIERS = {
    "current",
    "latest",
    "official",
    "standard",
    "standards",
    "specification",
    "specifications",
    "spec",
    "framework",
    "version",
    "edition",
    "guideline",
    "guidelines",
    "guidance",
}


def significant_query_tokens(query: str) -> list[str]:
    raw = tokens(query)
    meaningful = [token for token in raw if token not in QUERY_MODIFIERS]
    return meaningful or raw


def score_entry(entry: dict, query: str) -> int:
    q = query.casefold().strip()
    qtokens = significant_query_tokens(query)
    if not qtokens:
        return 0

    identifier = entry["id"].casefold()
    title = entry["title"].casefold()
    aliases = [x.casefold() for x in entry["aliases"]]
    topics = [x.casefold() for x in entry["topics"]]
    domains = [x.casefold() for x in entry["domains"]]
    issuer = entry["issuer"].casefold()

    qnorm = normalized_text(query)
    title_norm = normalized_text(title)
    alias_norms = [normalized_text(x) for x in aliases]
    field_tokens = {
        "identifier": set(tokens(identifier)),
        "title": set(tokens(title)),
        "aliases": set(t for value in aliases for t in tokens(value)),
        "topics": set(t for value in topics for t in tokens(value)),
        "domains": set(t for value in domains for t in tokens(value)),
        "issuer": set(tokens(issuer)),
    }
    all_tokens = set().union(*field_tokens.values())
    matched = {token for token in qtokens if token in all_tokens}
    coverage = len(matched) / len(set(qtokens))

    # Discovery fails closed for multi-token semantic queries: every meaningful
    # query token must be represented by the candidate. Generic query modifiers
    # such as `latest` or `standard` are ignored for this gate. This prevents
    # unknown named entities from receiving plausible-looking partial matches.
    if len(set(qtokens)) > 1 and coverage < 1.0:
        return 0

    score = 0
    if q == identifier:
        score += 1000
    if qnorm in alias_norms:
        score += 700
    if qnorm and qnorm in title_norm:
        score += 350
    if qnorm and any(qnorm in value for value in alias_norms):
        score += 250

    for token in qtokens:
        if token in field_tokens["identifier"]:
            score += 90
        if token in field_tokens["title"]:
            score += 55
        if token in field_tokens["aliases"]:
            score += 45
        if token in field_tokens["topics"]:
            score += 60
        if token in field_tokens["domains"]:
            score += 25
        if token in field_tokens["issuer"]:
            score += 15
        if token not in all_tokens:
            score -= 80

    if coverage == 1.0 and len(set(qtokens)) > 1:
        score += 200
    return max(score, 0)


def emit(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def cmd_build(_: argparse.Namespace) -> int:
    index = build_index()
    write_index(index)
    emit(
        {
            "standing": "BUILT",
            "path": str(INDEX.relative_to(ROOT)),
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
            "recordPath": str(path.relative_to(ROOT)),
            "record": record,
            "latestObservationPath": str(latest[0].relative_to(ROOT))
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
            "recordPath": str(path.relative_to(ROOT)),
            "officialSource": record["identity"]["officialSource"],
            "latestObservation": latest[1] if latest else None,
            "requiredAction": [
                "Check the official source semantically; HTTP reachability alone is insufficient.",
                "If lifecycle/version/currentness changed, append a new dated observation under authorities/observations/<id>/.",
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
