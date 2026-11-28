"""Legacy R5/R6 research CLI report-file serialization."""

from __future__ import annotations

import json
from pathlib import Path


def write_report_json(path: str | Path, value: object) -> None:
    """Write sorted, indented UTF-8 with a trailing newline.

    Preserve historical JSON encoding (including non-finite values) and
    overwrite behavior. This is report output, not atomic custody or
    strict JSON admission.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
