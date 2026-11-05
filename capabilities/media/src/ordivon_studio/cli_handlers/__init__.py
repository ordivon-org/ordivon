"""Domain-specific handlers for the single Ordivon Studio CLI entry point."""

from __future__ import annotations

import json
import sys


def _write_json(value: object) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
