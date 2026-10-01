#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ordivon_security_v2.subject_exposure import (
    SubjectExposureError,
    build_subject_exposure_snapshot_from_dict,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        value = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise SubjectExposureError("input root must be an object")
        result = build_subject_exposure_snapshot_from_dict(value)
    except (OSError, json.JSONDecodeError, KeyError, SubjectExposureError) as exc:
        raise SystemExit(f"DW01 subject/exposure binding failed: {exc}") from exc

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
