"""Independent consumer oracle for the current four native assertion contracts.

Checks named inventory, selected policy and reported facts; does not prove
that the native provider's reported facts were derived from raw evidence.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Any


def same_json(a: Any, b: Any) -> bool:
    if type(a) in (int, float) and type(b) in (int, float):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same_json(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same_json(x, y) for x, y in zip(a, b, strict=True))
    return a == b


def _policy(profile, key):
    value = profile.get(key, True)
    if type(value) is not bool:
        raise ValueError(f"invalid selected policy {key}")
    return value


def _expected(kind, p):
    if kind == "av":
        return {**{f"video.{key}": p["video"][key] for key in (
            "streamCount", "codec", "width", "height", "frameRate", "pixelFormat",
            "colorPrimaries", "colorTransfer", "colorSpace", "colorRange",
        )}, "audio.presence": p["audio"]["presence"]}
    if kind == "audio":
        return {**{f"audio.{key}": p["audio"][key] for key in (
            "streamCount", "codec", "sampleRate", "channels", "channelLayout",
        )}, "loudness.integratedLufs": {"target": p["loudness"]["targetLufs"], "tolerance": p["loudness"]["toleranceLu"]},
            "loudness.truePeakDbtp": {"max": p["loudness"]["maxTruePeakDbtp"]}}
    if kind == "otio":
        return {**{f"otio.{key}": p[key] for key in (
            "timelineName", "startTimecode", "endTimecode", "durationTimecode",
            "trackCount", "clipCount", "mediaReferenceCount",
        )}, "otio.rangesInBounds": True, "otio.mediaReferencePrefix": p.get("requiredMediaPrefix")}
    if kind == "timed-text":
        return {
            "timedText.cueCount": p["expectedCueCount"],
            "timedText.nonnegativeStart": ">=0",
            "timedText.positiveDurations": True if _policy(p, "requirePositiveDurations") else None,
            "timedText.nonemptyPackets": True if _policy(p, "requireNonemptyPackets") else None,
            "timedText.maxEndSeconds": {"max": p["maxEndSeconds"]},
            "timedText.language": p.get("expectedLanguage"),
        }
    raise ValueError("unsupported assertion contract")


def _number(value):
    return type(value) in (int, float)


def _rate_equal(actual, expected):
    try:
        return all(isinstance(x, str) and re.fullmatch(r"[1-9][0-9]*/[1-9][0-9]*", x) for x in (actual, expected)) and Fraction(actual) == Fraction(expected)
    except (ValueError, ZeroDivisionError):
        return False


def _verdict(name, row, expected, profile):
    actual = row["actual"]
    if name == "video.frameRate":
        return _rate_equal(actual, expected)
    if name == "audio.presence":
        if actual not in ("present", "absent") or expected not in ("required", "forbidden", "optional"):
            raise ValueError("invalid audio presence observation")
        return expected == "optional" or actual == ("present" if expected == "required" else "absent")
    if name.startswith("loudness."):
        standing = row.get("observationStanding")
        if standing == "finite":
            if not _number(actual):
                raise ValueError("invalid finite loudness observation")
            if name == "loudness.integratedLufs":
                return abs(actual - expected["target"]) <= expected["tolerance"]
            return actual <= expected["max"]
        if standing not in ("negative-infinity", "positive-infinity", "not-a-number", "unobserved-or-invalid") or actual is not None:
            raise ValueError("invalid nonfinite loudness observation")
        return False
    if name == "otio.rangesInBounds":
        if actual is not None and type(actual) is not bool:
            raise ValueError("invalid range observation")
        return not _policy(profile, "requireAllRangesInBounds") or actual is True
    if name == "otio.mediaReferencePrefix":
        count = actual.get("badReferenceCount") if isinstance(actual, dict) else None
        if type(count) is not int or count < 0:
            raise ValueError("invalid media reference count")
        return expected is None or count == 0
    if name in ("timedText.positiveDurations", "timedText.nonemptyPackets"):
        if type(actual) is not bool or row.get("required") is not (expected is True):
            raise ValueError("invalid timed-text optional policy observation")
        return expected is None or actual
    if name == "timedText.nonnegativeStart":
        return _number(actual) and actual >= 0
    if name == "timedText.maxEndSeconds":
        return _number(actual) and actual <= expected["max"]
    if name == "timedText.language" and expected is None:
        return True
    return same_json(actual, expected)


def validate_assertion_contract(kind: str, profile: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    try:
        expected = _expected(kind, profile)
        observed = {}
        for row in checks:
            name = row.get("name")
            if not isinstance(name, str) or name in observed:
                raise ValueError("duplicate or invalid assertion identity")
            observed[name] = row
        if observed.keys() != expected.keys():
            raise ValueError("assertion inventory mismatch")
        for name, value in expected.items():
            row = observed[name]
            if "expected" not in row or not same_json(row["expected"], value) or "actual" not in row:
                raise ValueError(f"selected assertion expectation mismatch: {name}")
            if row["ok"] is not _verdict(name, row, value, profile):
                raise ValueError(f"reported assertion verdict mismatch: {name}")
    except (KeyError, TypeError) as exc:
        raise ValueError("invalid selected assertion contract") from exc
