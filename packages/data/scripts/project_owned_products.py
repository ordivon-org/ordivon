#!/usr/bin/env python3
"""Project current Git-tracked producer ODPS files into read-only DCAT metadata."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO = PACKAGE_ROOT.parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))
from ordivon_data.odps_projection import project_catalog


def tracked_owner_products(repo: Path) -> list[Path]:
    """Use Git's existing tracked source inventory, not another product registry."""
    result = subprocess.run(
        [
            "/usr/bin/git",
            "--no-replace-objects",
            "-C",
            str(repo),
            "ls-files",
            "-z",
            "--",
            "*/odps.json",
        ],
        check=True,
        capture_output=True,
    )
    return sorted(
        repo / path.decode("utf-8") for path in result.stdout.split(b"\0") if path
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--product",
        action="append",
        type=Path,
        default=[],
        help="Explicit owner-supplied ODPS 1.1 file; repeatable",
    )
    args = parser.parse_args()
    source_files = args.product or tracked_owner_products(REPO)
    try:
        projected = project_catalog(source_files)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"ODPS discovery projection failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(projected, sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
