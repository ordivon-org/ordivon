"""
Checker Registry — Hermes Agent skill-system style governance for Ordivon checkers.

Each checker lives in checkers/<name>/ as a self-contained package:
    checkers/receipt-integrity/
    ├── CHECKER.md          ← YAML frontmatter + markdown body (metadata + description)
    ├── run.py              ← entry point: def run() -> CheckerResult
    ├── fixtures/           ← test fixtures (valid/invalid examples)
    └── references/         ← design docs, related architecture notes

The registry tracks:
    .bundled_manifest    — name:hash pairs for bundled checkers (like skills_sync.py)
    .usage.json          — telemetry sidecar (use_count, last_used_at, state, pinned)
    .curator_state       — auto-maintenance scheduler state

Three-source provenance (same as Hermes skills):
    bundled  — shipped with Ordivon, tracked in .bundled_manifest
    external — user-configured external_dirs in config
    custom   — everything else (agent-created or manually added)

Lifecycle states:
    active    → default
    stale     → unused > stale_after_days (default 30)
    archived  → unused > archive_after_days (default 90), moved to .archive/
    pinned    → boolean flag, exempt from all auto-transitions

Key design invariants:
    - Telemetry (.usage.json) is a SIDECAR, not part of CHECKER.md frontmatter.
      CHECKER.md is declaration. .usage.json is state. They don't mix.
    - Atomic writes everywhere — tempfile + os.replace().
    - Best-effort telemetry: a broken sidecar never breaks a checker run.
    - Pinned checkers are off-limits to curator and agent tools.
    - Bundled checkers that user modified are NEVER overwritten on sync.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

logger = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]  # src/ordivon_verify/ → src/ → root
CHECKERS_DIR = ROOT / "checkers"
MANIFEST_FILE = CHECKERS_DIR / ".bundled_manifest"
USAGE_FILE = CHECKERS_DIR / ".usage.json"
ARCHIVE_DIR = CHECKERS_DIR / ".archive"
CURATOR_STATE_FILE = CHECKERS_DIR / ".curator_state"

# ── Lifecycle constants ─────────────────────────────────────────────

STATE_ACTIVE = "active"
STATE_STALE = "stale"
STATE_ARCHIVED = "archived"
_VALID_STATES = {STATE_ACTIVE, STATE_STALE, STATE_ARCHIVED}

DEFAULT_STALE_AFTER_DAYS = 30
DEFAULT_ARCHIVE_AFTER_DAYS = 90

# ── Data types ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class CheckerResult:
    """Structured result from a checker run."""

    status: str  # "pass" | "fail" | "warn"
    exit_code: int
    findings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    output: str = ""


@dataclass
class CheckerEntry:
    """A registered checker — populated from CHECKER.md + run.py."""

    gate_id: str  # unique id: "receipt_integrity"
    display_name: str  # human: "Receipt Integrity"
    layer: str  # "L7B"
    hardness: str  # "hard" | "escalation" | "advisory"
    purpose: str  # what this checker does
    protects_against: str  # what failure mode it catches
    profiles: tuple[str, ...]  # ("pr-fast", "full")
    side_effects: bool = False  # writes files / modifies state
    timeout: int = 120
    entry_fn: Callable[[], CheckerResult] | None = None
    file_path: str = ""  # path to run.py
    checker_dir: str = ""  # path to checker package dir
    bundled_hash: str = ""  # MD5 of bundled content


# ── YAML helper ─────────────────────────────────────────────────────

_yaml_load_fn = None


def _yaml_load(content: str) -> dict:
    global _yaml_load_fn
    if _yaml_load_fn is None:
        import yaml

        loader = getattr(yaml, "CSafeLoader", None) or yaml.SafeLoader

        def _load(value: str):
            return yaml.load(value, Loader=loader) or {}

        _yaml_load_fn = _load
    return _yaml_load_fn(content)


# ── Frontmatter parsing ─────────────────────────────────────────────


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from CHECKER.md content.

    Returns (frontmatter_dict, markdown_body).
    """
    import re

    fm: Dict[str, Any] = {}
    body = content
    if not content.startswith("---"):
        return fm, body
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return fm, body
    yaml_content = content[3 : end_match.start() + 3]
    body = content[end_match.end() + 3 :]
    try:
        parsed = _yaml_load(yaml_content)
        if isinstance(parsed, dict):
            fm = parsed
    except Exception:
        # Fallback: simple key:value + inline list parsing for environments without PyYAML
        for line in yaml_content.strip().split("\n"):
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            # Handle inline lists: [a, b, c]
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            fm[key] = val
    return fm, body


# ── Hash utilities ──────────────────────────────────────────────────


def _coerce_int(value: Any, default: int) -> int:
    """Coerce a value (possibly string from YAML fallback) to int."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _dir_hash(directory: Path) -> str:
    """MD5 of all file contents in a directory for change detection."""
    hasher = hashlib.md5()
    try:
        for fpath in sorted(directory.rglob("*")):
            if fpath.is_file() and ".usage" not in str(fpath) and ".bundled" not in str(fpath):
                rel = fpath.relative_to(directory)
                hasher.update(str(rel).encode("utf-8"))
                hasher.update(fpath.read_bytes())
    except (OSError, IOError):
        pass
    return hasher.hexdigest()


# ── Atomic I/O ──────────────────────────────────────────────────────


def _atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON atomically via tempfile + os.replace."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix="." + path.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except Exception as e:
        logger.debug("Failed to write %s: %s", path, e, exc_info=True)


# ═══════════════════════════════════════════════════════════════════════
# Bundled Manifest — tracks bundled checker origin hashes
# ═══════════════════════════════════════════════════════════════════════


def _read_bundled_manifest() -> Dict[str, str]:
    """Read .bundled_manifest as {name: hash}."""
    if not MANIFEST_FILE.exists():
        return {}
    try:
        result = {}
        for line in MANIFEST_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                name, _, hash_val = line.partition(":")
                result[name.strip()] = hash_val.strip()
            else:
                result[line] = ""  # v1 migration
        return result
    except (OSError, IOError):
        return {}


def _write_bundled_manifest(entries: Dict[str, str]) -> None:
    """Write .bundled_manifest atomically."""
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = "\n".join(f"{name}:{hash_val}" for name, hash_val in sorted(entries.items())) + "\n"
    try:
        fd, tmp_path = tempfile.mkstemp(dir=str(MANIFEST_FILE.parent), prefix=".bundled_manifest.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, MANIFEST_FILE)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except Exception as e:
        logger.debug("Failed to write bundled manifest: %s", e)


# ═══════════════════════════════════════════════════════════════════════
# Usage Telemetry (.usage.json sidecar)
# ═══════════════════════════════════════════════════════════════════════


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_usage_record() -> Dict[str, Any]:
    return {
        "use_count": 0,
        "last_used_at": None,
        "last_pass_at": None,
        "last_fail_at": None,
        "state": STATE_ACTIVE,
        "pinned": False,
        "archived_at": None,
        "created_at": _now_iso(),
    }


def _load_usage() -> Dict[str, Dict[str, Any]]:
    if not USAGE_FILE.exists():
        return {}
    try:
        data = json.loads(USAGE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        logger.debug("Failed to read %s: %s", USAGE_FILE, e)
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): v for k, v in data.items() if isinstance(v, dict)}


def _save_usage(data: Dict[str, Dict[str, Any]]) -> None:
    _atomic_write_json(USAGE_FILE, data)


def get_usage_record(gate_id: str) -> Dict[str, Any]:
    """Return usage record for a checker, creating fresh one if missing."""
    data = _load_usage()
    rec = data.get(gate_id)
    if not isinstance(rec, dict):
        return _empty_usage_record()
    base = _empty_usage_record()
    for k, v in base.items():
        rec.setdefault(k, v)
    return rec


def _mutate_usage(gate_id: str, mutator) -> None:
    """Load, apply mutator(record), save. Best-effort — errors are logged."""
    if not gate_id:
        return
    try:
        data = _load_usage()
        rec = data.get(gate_id)
        if not isinstance(rec, dict):
            rec = _empty_usage_record()
        mutator(rec)
        data[gate_id] = rec
        _save_usage(data)
    except Exception as e:
        logger.debug("_mutate_usage(%s) failed: %s", gate_id, e, exc_info=True)


def bump_checker_use(gate_id: str) -> None:
    def _apply(rec):
        rec["use_count"] = int(rec.get("use_count") or 0) + 1
        rec["last_used_at"] = _now_iso()

    _mutate_usage(gate_id, _apply)


def bump_checker_result(gate_id: str, passed: bool) -> None:
    def _apply(rec):
        if passed:
            rec["last_pass_at"] = _now_iso()
        else:
            rec["last_fail_at"] = _now_iso()

    _mutate_usage(gate_id, _apply)


def set_checker_state(gate_id: str, state: str) -> None:
    if state not in _VALID_STATES:
        return

    def _apply(rec):
        rec["state"] = state
        if state == STATE_ARCHIVED:
            rec["archived_at"] = _now_iso()
        else:
            rec["archived_at"] = None

    _mutate_usage(gate_id, _apply)


def set_checker_pinned(gate_id: str, pinned: bool) -> None:
    def _apply(rec):
        rec["pinned"] = bool(pinned)

    _mutate_usage(gate_id, _apply)


def is_checker_pinned(gate_id: str) -> bool:
    rec = get_usage_record(gate_id)
    return bool(rec.get("pinned"))


# ═══════════════════════════════════════════════════════════════════════
# Discovery — find all checkers across bundled + external dirs
# ═══════════════════════════════════════════════════════════════════════

EXCLUDED_DIRS = frozenset({".git", ".github", ".archive", "__pycache__"})


def get_all_checker_dirs() -> List[Path]:
    """Return all checker directories: bundled first, then external."""
    dirs = [CHECKERS_DIR]
    # External dirs from config
    try:
        from ordivon_verify.config import load_config

        config = load_config()
        external = config.get("checkers", {}).get("external_dirs", [])
        if isinstance(external, str):
            external = [external]
        for entry in external:
            p = Path(os.path.expanduser(os.path.expandvars(str(entry))))
            if p.is_dir() and p != CHECKERS_DIR:
                dirs.append(p)
    except Exception:
        pass
    return dirs


def _is_bundled(checker_dir: Path) -> bool:
    """Return True if checker_dir is under the bundled CHECKERS_DIR."""
    try:
        checker_dir.resolve().relative_to(CHECKERS_DIR.resolve())
        return True
    except ValueError:
        return False


def discover_checkers() -> Dict[str, CheckerEntry]:
    """Walk all checker dirs and return {gate_id: CheckerEntry}.

    Only includes directories that have both CHECKER.md and run.py.
    """
    entries: Dict[str, CheckerEntry] = {}
    bundled_manifest = _read_bundled_manifest()

    for checker_root in get_all_checker_dirs():
        if not checker_root.exists():
            continue
        for checker_md in sorted(checker_root.rglob("CHECKER.md")):
            checker_dir = checker_md.parent
            # Skip excluded dirs
            parts = set(checker_dir.relative_to(checker_root).parts)
            if parts & EXCLUDED_DIRS:
                continue

            try:
                raw = checker_md.read_text(encoding="utf-8")
                frontmatter, _ = parse_frontmatter(raw)
            except Exception:
                continue

            gate_id = frontmatter.get("gate_id") or checker_dir.name
            if not gate_id or gate_id in entries:
                continue

            run_py = checker_dir / "run.py"
            entry_fn = None
            if run_py.exists():
                # Validate run.py syntax without executing
                try:
                    compile(run_py.read_text(), str(run_py), "exec")
                except (SyntaxError, OSError):
                    continue
                # Don't exec here — delayed until run time

            profiles = frontmatter.get("profiles", ["pr-fast", "full"])
            if isinstance(profiles, str):
                profiles = [profiles]

            entry = CheckerEntry(
                gate_id=gate_id,
                display_name=frontmatter.get("display_name", gate_id),
                layer=frontmatter.get("layer", "L?"),
                hardness=frontmatter.get("hardness", "hard"),
                purpose=frontmatter.get("purpose", ""),
                protects_against=frontmatter.get("protects_against", ""),
                profiles=tuple(profiles),
                side_effects=frontmatter.get("side_effects", False),
                timeout=_coerce_int(frontmatter.get("timeout"), 120),
                entry_fn=entry_fn,  # populated at run time
                file_path=str(run_py) if run_py.exists() else "",
                checker_dir=str(checker_dir),
                bundled_hash=(bundled_manifest.get(gate_id, "") if _is_bundled(checker_dir) else ""),
            )
            entries[gate_id] = entry

    return entries


# ═══════════════════════════════════════════════════════════════════════
# Sync — seed and update bundled checkers
# ═══════════════════════════════════════════════════════════════════════


def sync_bundled_checkers(quiet: bool = False) -> dict:
    """Sync bundled checkers using the manifest (same logic as skills_sync.py).

    - NEW: checker not in manifest → add to manifest with hash
    - EXISTING & unchanged by user → update if bundled changed
    - EXISTING & user-modified → skip, don't overwrite
    - DELETED by user → respected, not re-added
    """
    manifest = _read_bundled_manifest()
    active_entries = discover_checkers()

    copied = []
    updated = []
    user_modified = []
    skipped = 0

    for gate_id, entry in active_entries.items():
        if not entry.checker_dir:
            continue
        checker_dir = Path(entry.checker_dir)
        if not _is_bundled(checker_dir):
            continue

        bundled_hash = _dir_hash(checker_dir)

        if gate_id not in manifest:
            manifest[gate_id] = bundled_hash
            copied.append(gate_id)
            if not quiet:
                print(f"  + {gate_id}")
        else:
            origin_hash = manifest.get(gate_id, "")
            if not origin_hash:
                manifest[gate_id] = bundled_hash
                skipped += 1
            elif bundled_hash != origin_hash:
                manifest[gate_id] = bundled_hash
                updated.append(gate_id)
                if not quiet:
                    print(f"  ↑ {gate_id} (updated)")
            else:
                skipped += 1

    # Clean stale manifest entries
    active_names = set(active_entries.keys())
    cleaned = sorted(set(manifest.keys()) - active_names)
    for name in cleaned:
        del manifest[name]

    _write_bundled_manifest(manifest)

    return {
        "copied": copied,
        "updated": updated,
        "skipped": skipped,
        "user_modified": user_modified,
        "cleaned": cleaned,
        "total_bundled": len([e for e in active_entries.values() if _is_bundled(Path(e.checker_dir))]),
    }


# ═══════════════════════════════════════════════════════════════════════
# Manifest generation — auto-generate verification-gate-manifest.json
# ═══════════════════════════════════════════════════════════════════════


def generate_manifest() -> dict:
    """Generate a verification-gate-manifest.json from registered checkers."""
    entries = discover_checkers()
    gates = []
    for entry in sorted(entries.values(), key=lambda e: e.layer):
        gates.append({
            "gate_id": entry.gate_id,
            "display_name": entry.display_name,
            "layer": entry.layer,
            "hardness": entry.hardness,
            "command": f"python -m ordivon_verify run {entry.gate_id}",
            "expected_result_type": "exit_code_0" if entry.hardness == "hard" else "checker_output",
            "may_be_removed_only_by": "Stage Summit with documented reason",
            "purpose": entry.purpose,
            "protects_against": entry.protects_against,
        })
    hard_count = sum(1 for e in entries.values() if e.hardness == "hard")
    escalation_count = sum(1 for e in entries.values() if e.hardness == "escalation")
    return {
        "manifest_id": "auto-generated-v1",
        "profile": "auto",
        "version": "1.0",
        "status": "current",
        "authority": "derived_from_registry",
        "gate_count": len(gates),
        "hard_count": hard_count,
        "escalation_count": escalation_count,
        "gates": gates,
        "_note": "Auto-generated from checkers/ directory. Do not edit manually.",
    }


# ═══════════════════════════════════════════════════════════════════════
# Archival — archive/restore checker packages
# ═══════════════════════════════════════════════════════════════════════


def archive_checker(gate_id: str) -> Tuple[bool, str]:
    """Move a checker directory to .archive/. Returns (ok, message)."""
    entries = discover_checkers()
    entry = entries.get(gate_id)
    if not entry or not entry.checker_dir:
        return False, f"Checker '{gate_id}' not found."

    checker_dir = Path(entry.checker_dir)
    if not _is_bundled(checker_dir):
        return False, "Cannot archive bundled checker."

    if is_checker_pinned(gate_id):
        return False, f"Checker '{gate_id}' is pinned — unpin first."

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    dest = ARCHIVE_DIR / checker_dir.name
    if dest.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        dest = ARCHIVE_DIR / f"{checker_dir.name}-{ts}"

    try:
        checker_dir.rename(dest)
    except OSError:
        import shutil

        try:
            shutil.move(str(checker_dir), str(dest))
        except Exception as e:
            return False, f"Failed to archive: {e}"

    set_checker_state(gate_id, STATE_ARCHIVED)
    return True, f"Archived to {dest}"


# ═══════════════════════════════════════════════════════════════════════
# Curator — auto-maintenance (stale/archive detection)
# ═══════════════════════════════════════════════════════════════════════


def _load_curator_state() -> Dict[str, Any]:
    if not CURATOR_STATE_FILE.exists():
        return {"last_run_at": None, "run_count": 0, "paused": False}
    try:
        data = json.loads(CURATOR_STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("run_count", 0)
            return data
    except Exception:
        pass
    return {"last_run_at": None, "run_count": 0, "paused": False}


def _save_curator_state(state: Dict[str, Any]) -> None:
    _atomic_write_json(CURATOR_STATE_FILE, state)


def run_curator(
    stale_after_days: int = DEFAULT_STALE_AFTER_DAYS,
    archive_after_days: int = DEFAULT_ARCHIVE_AFTER_DAYS,
) -> Dict[str, Any]:
    """Run one curator cycle: transition stale/archive based on last_used_at.

    Returns summary dict with actions taken.
    """
    state = _load_curator_state()
    if state.get("paused"):
        return {"action": "skipped", "reason": "curator paused"}

    now = datetime.now(timezone.utc)
    actions = {"staled": [], "archived": [], "pinned_skipped": []}

    entries = discover_checkers()
    for gate_id, entry in entries.items():
        rec = get_usage_record(gate_id)
        if rec.get("pinned"):
            continue
        if rec.get("state") == STATE_ARCHIVED:
            continue

        last_used = rec.get("last_used_at")
        if not last_used:
            continue

        try:
            last_dt = datetime.fromisoformat(last_used)
        except (ValueError, TypeError):
            continue

        days_since = (now - last_dt).days

        if days_since > archive_after_days:
            ok, msg = archive_checker(gate_id)
            if ok:
                actions["archived"].append(gate_id)
        elif days_since > stale_after_days:
            set_checker_state(gate_id, STATE_STALE)
            actions["staled"].append(gate_id)

    state["last_run_at"] = _now_iso()
    state["run_count"] = state.get("run_count", 0) + 1
    _save_curator_state(state)

    return actions


# ═══════════════════════════════════════════════════════════════════════
# Document Curator — detect stale documents in document-registry.jsonl
# ═══════════════════════════════════════════════════════════════════════


def run_document_curator() -> Dict[str, Any]:
    """Scan document-registry.jsonl for stale documents.

    Returns summary with stale doc IDs and recommended actions.
    This is the DG Pack equivalent of the checker curator —
    governed objects (documents) get lifecycle management.
    """
    import json as _json
    from datetime import date as _date

    registry_path = ROOT / "docs" / "governance" / "document-registry.jsonl"
    if not registry_path.exists():
        return {"error": "document-registry.jsonl not found", "stale": [], "critical_stale": []}

    entries = []
    with open(registry_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(_json.loads(line))
            except _json.JSONDecodeError:
                pass

    today = _date.today()
    result = {"stale": [], "critical_stale": [], "total": len(entries), "fresh": 0, "no_window": 0}

    for e in entries:
        did = e.get("doc_id", "?")
        last_verified = e.get("last_verified", "")
        stale_after = e.get("stale_after_days")
        authority = e.get("authority", "")

        if not last_verified:
            result["no_window"] += 1
            continue

        try:
            lv_date = _date.fromisoformat(last_verified)
        except (ValueError, TypeError):
            continue

        window = stale_after if isinstance(stale_after, int) else 14
        age = (today - lv_date).days

        if age > window * 2:
            item = {
                "doc_id": did,
                "path": e.get("path", ""),
                "age_days": age,
                "window_days": window,
                "authority": authority,
            }
            if authority in ("source_of_truth", "current_status"):
                result["critical_stale"].append(item)
            else:
                result["stale"].append(item)
        else:
            result["fresh"] += 1

    return result
