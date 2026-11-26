"""Bounded native systemd identity/currentness readback, not activation.

A manager observation is not an execution or consumer-success receipt.
"""
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
