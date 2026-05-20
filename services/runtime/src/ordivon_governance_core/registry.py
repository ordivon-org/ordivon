"""Registry utilities — interact with the document registry. PG-backed when available, JSONL fallback."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional

from .jsonl import read_jsonl, find_by_key, count_entries

# Canonical registry path (JSONL fallback)
DEFAULT_REGISTRY = Path(__file__).resolve().parents[2] / "docs/governance/document-registry.jsonl"
DOC_TYPES_PATH = Path(__file__).resolve().parents[2] / "docs/governance/schemas/document-types.json"

VALID_AUTHORITIES = (
    "source_of_truth",
    "current_status",
    "supporting_evidence",
    "historical_record",
    "proposal",
    "example",
    "archive",
    "bootstrap",
)


def load_valid_doc_types() -> set[str]:
    """Load valid document types from the canonical governance schema."""
    data = json.loads(DOC_TYPES_PATH.read_text())
    return set(data["valid_doc_types"])


# PG session factory — imported lazily
_pg_session = None


def _get_pg_session():
    global _pg_session
    if _pg_session is not None:
        return _pg_session
    try:
        from state.db.session import SessionLocal

        _pg_session = SessionLocal()
        return _pg_session
    except Exception:
        return None


def _use_pg() -> bool:
    return os.environ.get("ORDIVON_REGISTRY_BACKEND", "") == "pg" or _get_pg_session() is not None


def load_registry(path: Optional[Path] = None) -> dict[str, dict]:
    """Load registry into path→entry map. Uses PG when available."""
    if _use_pg():
        try:
            from state.db.governance_schema import DocumentRegistry

            session = _get_pg_session()
            registry = {}
            for row in session.query(DocumentRegistry).all():
                d = {c.name: getattr(row, c.name) for c in row.__table__.columns}
                d.pop("id", None)
                if d.get("path"):
                    registry[d["path"]] = d
            return registry
        except Exception:
            pass

    registry = {}
    p = path or DEFAULT_REGISTRY
    for entry in read_jsonl(p):
        entry_path = entry.get("path", "")
        if entry_path:
            registry[entry_path] = entry
    return registry


def load_registry_by_id(path: Optional[Path] = None) -> dict[str, dict]:
    """Load registry into doc_id→entry map."""
    if _use_pg():
        try:
            from state.db.governance_schema import DocumentRegistry

            session = _get_pg_session()
            registry = {}
            for row in session.query(DocumentRegistry).all():
                d = {c.name: getattr(row, c.name) for c in row.__table__.columns}
                d.pop("id", None)
                if d.get("doc_id"):
                    registry[d["doc_id"]] = d
            return registry
        except Exception:
            pass

    registry = {}
    p = path or DEFAULT_REGISTRY
    for entry in read_jsonl(p):
        doc_id = entry.get("doc_id", "")
        if doc_id:
            registry[doc_id] = entry
    return registry


def find_entry(path: str) -> Optional[dict]:
    """Find a registry entry by path."""
    if _use_pg():
        try:
            from state.db.governance_schema import DocumentRegistry

            session = _get_pg_session()
            row = session.query(DocumentRegistry).filter(DocumentRegistry.path == path).first()
            if row:
                d = {c.name: getattr(row, c.name) for c in row.__table__.columns}
                d.pop("id", None)
                return d
        except Exception:
            pass
    return find_by_key(DEFAULT_REGISTRY, "path", path)


def find_entry_by_id(doc_id: str) -> Optional[dict]:
    """Find a registry entry by doc_id."""
    if _use_pg():
        try:
            from state.db.governance_schema import DocumentRegistry

            session = _get_pg_session()
            row = session.query(DocumentRegistry).filter(DocumentRegistry.doc_id == doc_id).first()
            if row:
                d = {c.name: getattr(row, c.name) for c in row.__table__.columns}
                d.pop("id", None)
                return d
        except Exception:
            pass
    return find_by_key(DEFAULT_REGISTRY, "doc_id", doc_id)


def register_entry(entry: dict) -> bool:
    """Register a new document in PG or JSONL fallback."""
    if _use_pg():
        try:
            from state.db.governance_schema import DocumentRegistry

            session = _get_pg_session()
            existing = session.query(DocumentRegistry).filter(DocumentRegistry.doc_id == entry.get("doc_id")).first()
            if existing:
                return False  # duplicate
            row = DocumentRegistry(**{
                k: v for k, v in entry.items() if k in [c.name for c in DocumentRegistry.__table__.columns]
            })
            session.add(row)
            session.commit()
            return True
        except Exception:
            pass

    # JSONL fallback
    from .jsonl import append_jsonl_safe

    return append_jsonl_safe(DEFAULT_REGISTRY, entry, dedup_by="doc_id").get("status") == "appended"


def entry_count() -> int:
    if _use_pg():
        try:
            from state.db.governance_schema import DocumentRegistry

            session = _get_pg_session()
            return session.query(DocumentRegistry).count()
        except Exception:
            pass
    return count_entries(DEFAULT_REGISTRY)


def path_exists_in_registry(path: str) -> bool:
    return find_entry(path) is not None


def doc_id_exists(doc_id: str) -> bool:
    return find_entry_by_id(doc_id) is not None


def validate_entry_basic(entry: dict) -> list[str]:
    """Validate basic registry entry structure."""
    from .jsonl import validate_entry

    errors = validate_entry(entry, ["doc_id", "path", "title", "doc_type", "status", "authority"])

    if entry.get("doc_type") not in load_valid_doc_types():
        errors.append(f"INVALID_DOC_TYPE: {entry.get('doc_type')}")
    if entry.get("authority") not in VALID_AUTHORITIES:
        errors.append(f"INVALID_AUTHORITY: {entry.get('authority')}")

    return errors
