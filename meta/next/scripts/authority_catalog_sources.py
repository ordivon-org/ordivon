"""External authority source identity/currentness and boundary validation.

No search ranking, task-local applicability, or CLI state belongs here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "authorities"
RECORDS = AUTH / "records"
OBS = AUTH / "observations"

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
