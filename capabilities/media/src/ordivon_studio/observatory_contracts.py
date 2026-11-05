from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

OBSERVATION_KIND = "ordivon.studio-cultural-observation"
SNAPSHOT_KIND = "ordivon.studio-cultural-snapshot"
REPORT_KIND = "ordivon.studio-cultural-analysis"

def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")



def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
