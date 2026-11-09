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
from ordivon_data.git_sources import committed_owner_products
from ordivon_data.local_evidence import LocalEvidenceBinding
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
    parser.add_argument(
        "--bind-local",
        action="append",
        nargs=5,
        default=[],
        metavar=(
            "PRODUCT_ID",
            "PORT_NAME",
            "PATH_PROPERTY",
            "SHA_PROPERTY",
            "OWNER_ROOT",
        ),
        help=(
            "Optional exact owner-ODPS metadata and owner-root binding for a "
            "local file; checks declared SHA-256 against the current bytes. "
            "No source paths or port mappings are inferred."
        ),
    )
    parser.add_argument(
        "--at-commit",
        metavar="REVISION",
        help=(
            "Read ODPS metadata from one exact committed Git tree, ignoring "
            "uncommitted changes. The commit does not freeze separately bound "
            "local data file bytes."
        ),
    )
    args = parser.parse_args()
    if args.at_commit and args.product:
        parser.error("--at-commit and --product are mutually exclusive")
    bindings = tuple(
        LocalEvidenceBinding(
            product_id=product_id,
            port_name=port_name,
            path_property=path_property,
            digest_property=digest_property,
            owner_root=Path(owner_root),
        )
        for product_id, port_name, path_property, digest_property, owner_root in args.bind_local
    )
    try:
        if args.at_commit:
            revision, source_files = committed_owner_products(REPO, args.at_commit)
        else:
            revision = None
            source_files = args.product or tracked_owner_products(REPO)
        projected = project_catalog(source_files, bindings=bindings)
    except (
        OSError,
        ValueError,
        TypeError,
        UnicodeError,
        json.JSONDecodeError,
    ) as error:
        print(f"ODPS discovery projection failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(projected, sort_keys=True, indent=2, ensure_ascii=False))
    if revision is not None:
        print(f"sourceCommit={revision} (metadata only)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
