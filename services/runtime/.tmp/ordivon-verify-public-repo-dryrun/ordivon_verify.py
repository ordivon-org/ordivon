#!/usr/bin/env python3
"""Ordivon Verify — thin compatibility wrapper.

Delegates to the ordivon_verify package. All logic lives in src/ordivon_verify/.

Usage:
    uv run python scripts/ordivon_verify.py all
    uv run python scripts/ordivon_verify.py all --json
    uv run python -m ordivon_verify all
"""

import sys
from pathlib import Path

# Ensure src/ is on sys.path
_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from ordivon_verify.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
