"""Exact numeric interpretation shared by native AV and Python QC."""
from __future__ import annotations

import json
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any


def positive_rate(value: object) -> Fraction:
    if not isinstance(value, str) or re.fullmatch(r"[1-9][0-9]*/[1-9][0-9]*", value) is None:
        raise ValueError(f"invalid positive rational frame rate: {value!r}")
    return Fraction(value)


def observed_rate(stream: dict[str, Any]) -> object:
    primary = stream.get("avg_frame_rate")
    return stream.get("r_frame_rate") if primary is None or primary == "" else primary


def rates_equal(actual: object, expected: object) -> bool:
    try:
        return positive_rate(actual) == positive_rate(expected)
    except ValueError:
        return False


def exact_integer(value: object, *, field: str) -> int | None:
    if value is None:
        return None
    if type(value) is int:
        return value
    if isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        try:
            return int(value)
        except ValueError:
            pass
    raise ValueError(f"{field} must be an integer, found {value!r}")


def main() -> int:
    if len(sys.argv) != 3:
        return 64
    profile, probe = (json.loads(Path(path).read_bytes()) for path in sys.argv[1:])
    video = next((row for row in probe.get("streams", []) if row.get("codec_type") == "video"), {})
    actual = observed_rate(video)
    expected = profile["video"]["frameRate"]
    print(json.dumps({"name": "video.frameRate", "actual": actual,
                      "expected": expected, "ok": rates_equal(actual, expected)}, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
