"""Bounded native systemd identity/currentness readback, not activation.

A manager observation is not an execution or consumer-success receipt.
"""
import json
from pathlib import Path

UNIT_PROPERTIES = ("LoadState", "FragmentPath", "DropInPaths", "NeedDaemonReload")


def require_loaded_identity(output: str, expected_fragment: Path) -> None:
    """Require exactly one observation of each declared native property.

    The owner declares a single fragment and no drop-ins. Unknown/malformed
    observations are rejected, never treated as proof of currentness.
    """
    fields: dict[str, str] = {}
    for line in output.splitlines():
        key, sep, value = line.partition("=")
        if not sep or key not in UNIT_PROPERTIES or key in fields:
            raise ValueError("Invalid or ambiguous native unit metadata")
        fields[key] = value
    expected = {
        "LoadState": "loaded",
        "FragmentPath": str(expected_fragment),
        "DropInPaths": "",
        "NeedDaemonReload": "no",
    }
    if fields != expected:
        raise ValueError("Native unit identity/currentness not qualified")



def single_property_row(value: object, signature: str, width: int) -> list:
    """Consume the native busctl JSON property envelope, not display text."""
    if not isinstance(value, dict) or set(value) != {"type", "data"} or value["type"] != signature:
        raise ValueError("Unexpected native property signature")
    rows = value["data"]
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError("Unexpected native property cardinality")
    row = rows[0]
    if not isinstance(row, list) or len(row) != width:
        raise ValueError("Unexpected native property row")
    return row


def require_command(value: object, expected_argv: list[str]) -> None:
    row = single_property_row(value, "a(sasbttttuii)", 10)
    path, argv, ignore_errors, *observations = row
    if path != expected_argv[0] or argv != expected_argv or ignore_errors is not False:
        raise ValueError("Native loaded command does not match declared tuple")
    # Native execution coordinates are dynamic. Qualify their shape only;
    # a valid tuple is NOT evidence that this command executed successfully.
    bounds = [2**64] * 4 + [2**32]
    if any(type(n) is not int or not 0 <= n < bound
           for n, bound in zip(observations[:5], bounds, strict=True)):
        raise ValueError("Malformed native command observation")
    if any(type(n) is not int or not -(2**31) <= n < 2**31
           for n in observations[5:]):
        raise ValueError("Malformed native command result")


def require_calendar(value: object, expected_expression: str) -> None:
    row = single_property_row(value, "a(sst)", 3)
    kind, expression, next_elapse = row
    if (kind != "OnCalendar" or expression != expected_expression
            or type(next_elapse) is not int or not 0 <= next_elapse < 2**64):
        raise ValueError("Native loaded calendar does not match declared tuple")

def unique_fields(pairs: list[tuple[str, object]]) -> dict:
    fields = {}
    for key, value in pairs:
        if key in fields:
            raise ValueError("Duplicate native D-Bus JSON field")
        fields[key] = value
    return fields


def reject_constant(value: str) -> None:
    raise ValueError("Nonfinite native D-Bus JSON constant")


def decode_native_json(raw: str) -> object:
    return json.loads(raw, object_pairs_hook=unique_fields, parse_constant=reject_constant)


def unit_object_path(value: object) -> str:
    if (not isinstance(value, dict) or set(value) != {"type", "data"}
            or value["type"] != "o" or not isinstance(value["data"], list)
            or len(value["data"]) != 1 or not isinstance(value["data"][0], str)
            or not value["data"][0].startswith("/org/freedesktop/systemd1/unit/")):
        raise ValueError("No unique native loaded unit identity")
    return value["data"][0]


def require_unit_id(value: object, expected: str) -> None:
    if value != {"type": "s", "data": expected}:
        raise ValueError("Native loaded object identity mismatch")
