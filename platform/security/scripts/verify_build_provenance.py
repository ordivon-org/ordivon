#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_security_v2.provenance import verify_build_provenance


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--provenance", type=Path, required=True)
    p.add_argument("--source-revision", required=True)
    args = p.parse_args()
    statement = json.loads(args.provenance.read_text())
    result = verify_build_provenance(
        statement,
        artifact=args.artifact,
        expected_source_revision=args.source_revision,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
