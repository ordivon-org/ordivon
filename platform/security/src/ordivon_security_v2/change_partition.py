"""Pure set partition of already observed changes; no observation or I/O."""

from __future__ import annotations

from collections.abc import Mapping


def partition_changes(
    changes: Mapping[str, set[str]],
) -> tuple[list[str], dict[str, list[str]]]:
    """Return changes common to every group and each group's remaining changes.

    The input must contain at least one observed group. Empty change sets are
    valid and distinct from an absent group. Never modify the input.
    """
    if not changes:
        raise ValueError("at least one observed group is required")
    shared = set.intersection(*changes.values())
    local = {}
    for group in sorted(changes):
        remainder = changes[group] - shared
        if remainder:
            local[group] = sorted(remainder)
    return sorted(shared), local
