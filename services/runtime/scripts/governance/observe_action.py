#!/usr/bin/env python3
"""Observe post-action facts for an AOS AIActionDeclaration.

This is an observer, not an interpreter. It records git/filesystem facts and
marks command history as UNKNOWN in v0. It is the only v0 producer of
SYSTEM_OBSERVED AOS action events.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DECLARATIONS_LEDGER = ROOT / "docs/governance/action-declarations.jsonl"
OBSERVED_DIR = ROOT / "docs/governance/observed-actions"
REGISTRY_PATH = ROOT / "docs/governance/document-registry.jsonl"
OBSERVED_SCHEMA_VERSION = "aos-observed-action-v0.3"
OBSERVED_CREATED_BY = "scripts/governance/observe_action.py"
GENESIS_EVENT_HASH = "GENESIS:ObservedAction"


def run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def slug_from_object_id(object_id: str) -> str:
    return object_id.rsplit(":", 1)[-1].replace("/", "-")


def object_hash(obj: dict) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def canonical_event_payload(observation: dict) -> bytes:
    payload = {key: value for key, value in observation.items() if key != "event_hash"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def compute_event_hash(observation: dict) -> str:
    return f"sha256:{hashlib.sha256(canonical_event_payload(observation)).hexdigest()}"


def seal_observation(
    observation: dict,
    *,
    prev_event_hash: str = GENESIS_EVENT_HASH,
    observed_sequence: int = 1,
    source_identity: str = OBSERVED_CREATED_BY,
) -> dict:
    sealed = dict(observation)
    slug = slug_from_object_id(sealed["source_declaration_ref"])
    sealed["event_id"] = f"aos:event:ObservedAction:{slug}.{observed_sequence:06d}"
    sealed["prev_event_hash"] = prev_event_hash
    sealed["source_identity"] = source_identity
    sealed["observed_sequence"] = observed_sequence
    sealed["event_hash"] = compute_event_hash(sealed)
    return sealed


def path_matches(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        clean = pattern.rstrip("/")
        if any(ch in clean for ch in "*?[]"):
            if fnmatch(path, clean):
                return True
        elif path == clean or path.startswith(clean + "/"):
            return True
    return False


def parse_status_paths(status_text: str) -> list[str]:
    paths: list[str] = []
    for line in status_text.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            paths.append(path)
    return sorted(set(paths))


def parse_name_status(diff_text: str) -> tuple[set[str], set[str], set[str]]:
    added: set[str] = set()
    modified: set[str] = set()
    deleted: set[str] = set()
    for line in diff_text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            deleted.add(parts[1])
            added.add(parts[2])
            continue
        if len(parts) < 2:
            continue
        path = parts[1]
        if status.startswith("A"):
            added.add(path)
        elif status.startswith("D"):
            deleted.add(path)
        else:
            modified.add(path)
    return added, modified, deleted


def read_latest_declaration_record(object_id: str) -> dict:
    if not DECLARATIONS_LEDGER.exists():
        return {}
    latest: dict = {}
    for line in DECLARATIONS_LEDGER.read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("object_id") == object_id:
            latest = row
    return latest


def load_registry_entries_for_scope(scope: list[str]) -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    entries: list[dict] = []
    for line in REGISTRY_PATH.read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        path = row.get("path", "")
        if path and path_matches(path, scope):
            entries.append({"doc_id": row.get("doc_id", ""), "path": path})
    return entries


def git_head() -> str:
    rc, out, _ = run(["git", "rev-parse", "HEAD"])
    return out.strip() if rc == 0 else "UNKNOWN"


def build_observation(
    declaration_path: Path,
    base_ref: str | None = None,
    prev_event_hash: str = GENESIS_EVENT_HASH,
    observed_sequence: int = 1,
    source_identity: str = OBSERVED_CREATED_BY,
) -> dict:
    declaration = load_json(declaration_path)
    object_id = declaration["object_id"]
    slug = slug_from_object_id(object_id)
    declaration_digest = object_hash(declaration)
    baseline = read_latest_declaration_record(object_id)
    baseline_paths = set((baseline.get("baseline") or {}).get("dirty_paths") or [])

    git_base_ref = base_ref or (baseline.get("baseline") or {}).get("git_head_ref") or "HEAD"
    unknowns = ["commands_run"]
    sources = ["SYSTEM_OBSERVED:git status --short", "SYSTEM_OBSERVED:filesystem scan"]

    rc, diff_out, diff_err = run(["git", "diff", "--name-status", git_base_ref])
    if rc == 0:
        added, modified, deleted = parse_name_status(diff_out)
        sources.insert(0, "SYSTEM_OBSERVED:git diff --name-status")
    else:
        added, modified, deleted = set(), set(), set()
        unknowns.append(f"git_diff_unavailable:{diff_err.strip()[:120]}")

    rc, untracked_out, _ = run(["git", "ls-files", "--others", "--exclude-standard"])
    if rc == 0:
        added.update(path for path in untracked_out.splitlines() if path.strip())

    changed = added | modified | deleted
    observed_receipts = sorted(p for p in changed if p.startswith("receipts/governance/"))
    observed_registry_entries = load_registry_entries_for_scope(declaration.get("declared_scope", []))
    if "docs/governance/document-registry.jsonl" not in changed:
        observed_registry_entries = []

    now = datetime.now(timezone.utc).isoformat()
    observation = {
        "schema_version": OBSERVED_SCHEMA_VERSION,
        "object_id": f"aos:actions:ObservedAction:{slug}",
        "object_kind": "ObservedAction",
        "origin": "SYSTEM_OBSERVED",
        "created_at": now,
        "created_by": OBSERVED_CREATED_BY,
        "provenance": {
            "input_refs": [object_id, str(declaration_path)],
            "collector": OBSERVED_CREATED_BY,
            "digest": declaration_digest,
            "signature_refs": [],
        },
        "state": "OBSERVED",
        "source_declaration_ref": object_id,
        "observation_sources": sources,
        "git_base_ref": git_base_ref,
        "git_head_ref": git_head(),
        "observed_files_added": sorted(added),
        "observed_files_modified": sorted(modified),
        "observed_files_deleted": sorted(deleted),
        "observed_receipts": observed_receipts,
        "observed_registry_entries": observed_registry_entries,
        "observed_debt_transitions": [],
        "unknown_observations": sorted(set(unknowns)),
        "preexisting_dirty_overlap": sorted(changed & baseline_paths),
        "observed_at": now,
        "declaration_hash": declaration_digest,
    }
    return seal_observation(
        observation,
        prev_event_hash=prev_event_hash,
        observed_sequence=observed_sequence,
        source_identity=source_identity,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Observe post-action facts for an AIActionDeclaration")
    parser.add_argument("--declaration", required=True, help="Path to object.aos.json")
    parser.add_argument(
        "--base-ref", default=None, help="Git ref to diff against; defaults to declaration baseline or HEAD"
    )
    parser.add_argument(
        "--prev-event-hash",
        default=GENESIS_EVENT_HASH,
        help="Previous ObservedAction event_hash. Defaults to the v0 genesis marker.",
    )
    parser.add_argument("--observed-sequence", type=int, default=1, help="1-based sequence number for this observation")
    parser.add_argument(
        "--source-identity",
        default=OBSERVED_CREATED_BY,
        help="System identity that produced this observation",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON observation")
    parser.add_argument(
        "--no-write", action="store_true", help="Do not write docs/governance/observed-actions/<id>.json"
    )
    args = parser.parse_args()

    observation = build_observation(
        Path(args.declaration),
        args.base_ref,
        prev_event_hash=args.prev_event_hash,
        observed_sequence=args.observed_sequence,
        source_identity=args.source_identity,
    )
    if not args.no_write:
        OBSERVED_DIR.mkdir(parents=True, exist_ok=True)
        slug = slug_from_object_id(observation["source_declaration_ref"])
        out_path = OBSERVED_DIR / f"{slug}.json"
        out_path.write_text(json.dumps(observation, indent=2, ensure_ascii=False) + "\n")
        if not args.json:
            print(out_path.relative_to(ROOT))

    if args.json:
        print(json.dumps(observation, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
