from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")


def snapshot_materials(paths: Iterable[Path]) -> dict[str, Any]:
    materials = [file_fact(path) for path in paths]
    return {
        "capturedAt": utc_now(),
        "materials": materials,
        "note": (
            "Operational immutable-input snapshot. Durable build provenance should "
            "be emitted as an in-toto Statement/SLSA Provenance predicate."
        ),
    }
