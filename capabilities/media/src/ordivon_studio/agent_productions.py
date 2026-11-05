"""Read-only Media Production identity and standing projections.

A known Production is not automatically the current user/Agent intent. Real
production descriptors remain source-owned; this module only enumerates them.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _production_root(root: Path, production_id: str) -> Path:
    if not production_id or "/" in production_id or "\\" in production_id or production_id in {".", ".."}:
        raise ValueError("productionId must be one direct Production id")
    production_root = (root / "productions" / production_id).resolve()
    expected_parent = (root / "productions").resolve()
    if production_root.parent != expected_parent or not (production_root / "production.json").is_file():
        raise ValueError(f"unknown Production: {production_id}")
    return production_root


def production_standing(root: Path = ROOT) -> dict[str, Any]:
    productions_root = root / "productions"
    productions: list[dict[str, Any]] = []
    if productions_root.is_dir():
        for production_root in sorted(path for path in productions_root.iterdir() if path.is_dir()):
            production_path = production_root / "production.json"
            if not production_path.is_file():
                continue
            value = json.loads(production_path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError(f"Production descriptor must be an object: {production_path}")
            outputs: list[dict[str, Any]] = []
            raw_outputs = value.get("outputs", [])
            if isinstance(raw_outputs, list):
                for output in raw_outputs:
                    if not isinstance(output, dict):
                        continue
                    outputs.append(
                        {
                            "id": output.get("id"),
                            "kind": output.get("kind"),
                            "status": output.get("status"),
                            "profile": output.get("profile"),
                        }
                    )
            productions.append(
                {
                    "productionId": production_root.name,
                    "title": value.get("title"),
                    "status": value.get("status"),
                    "intent": value.get("intent"),
                    "audiences": list(value.get("audiences", []))
                    if isinstance(value.get("audiences"), list)
                    else [],
                    "outputs": outputs,
                    "source": {
                        "path": str(production_path.relative_to(root)),
                        "digest": "sha256:" + hashlib.sha256(production_path.read_bytes()).hexdigest(),
                    },
                }
            )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-production-standing",
        "truthRole": "derived-read-only-owner-production-index",
        "currentProductionId": None,
        "selectionStanding": "OWNER_CURRENT_INTENT_NOT_ESTABLISHED",
        "productions": productions,
        "claims": {
            "ownerCurrentIntentEstablished": False,
            "selectionPriorityInferred": False,
            "productionIdentityInvented": False,
        },
        "nextWhenSelected": "studio_production_context",
        "boundary": (
            "Studio can enumerate exact Production identity mechanically, but it does not infer "
            "which Production the caller means by current work. Caller/owner intent must ground "
            "that semantic selection before a Production-specific context is useful."
        ),
    }
