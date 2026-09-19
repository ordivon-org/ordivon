from __future__ import annotations

import argparse
import json
from pathlib import Path

from .model_lineage import persist_monitoring_evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--duckdb",
        type=Path,
        default=Path("/opt/ordivon/external/duckdb/1.5.5-1/duckdb"),
    )
    args = parser.parse_args()
    result = persist_monitoring_evidence(
        evidence_path=args.evidence,
        output_dir=args.output_dir,
        duckdb_binary=args.duckdb,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
