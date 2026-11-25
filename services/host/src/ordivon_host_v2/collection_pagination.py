from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from .canonical_json import canonical_bytes

DEFAULT_COLLECTION_MAX_BYTES = 262_144
DEFAULT_MESSAGE_COLLECTION_MAX_BYTES = 524_288
DEFAULT_SPACE_MAX_BYTES = 2_097_152
MAX_COLLECTION_MAX_BYTES = 4_194_304
MIN_COLLECTION_MAX_BYTES = 16_384
MIN_MESSAGE_COLLECTION_MAX_BYTES = 131_072
MIN_SPACE_MAX_BYTES = 1_048_576


def validate_max_bytes(max_bytes: int, *, minimum: int = MIN_COLLECTION_MAX_BYTES) -> None:
    if type(max_bytes) is not int or not minimum <= max_bytes <= MAX_COLLECTION_MAX_BYTES:
        raise ValueError(f"max_bytes must be in [{minimum},{MAX_COLLECTION_MAX_BYTES}]")


def bounded_prefix[T](
    items: Sequence[T],
    *,
    max_bytes: int,
    collection_key: str,
    envelope: Callable[[T], dict[str, Any]],
    minimum: int = MIN_COLLECTION_MAX_BYTES,
) -> tuple[list[T], bool]:
    """Bound a prefix by exact canonical bytes, without re-encoding earlier items.

    The envelope supplies non-collection metadata for a nonempty prefix using
    only its final item. The collection is inserted under collection_key.
    RFC 8785 arrays are independently canonicalized elements joined by commas:
    size(full) = size(envelope with empty array) + sum(element sizes) + commas.
    Retain the existing first-overflow rule even if cursor metadata shrinks.
    Empty inputs and the first-item-too-large error retain their prior behavior.
    """
    validate_max_bytes(max_bytes, minimum=minimum)
    page: list[T] = []
    array_bytes = 0
    for item in items:
        metadata = envelope(item)
        if collection_key in metadata:
            raise ValueError("collection metadata must omit its array")
        next_array_bytes = array_bytes + len(canonical_bytes(item)) + int(bool(page))
        size = len(canonical_bytes({**metadata, collection_key: []})) + next_array_bytes
        if size > max_bytes:
            if not page:
                raise ValueError("max_bytes cannot fit one legal item plus response envelope")
            return page, True
        page.append(item)
        array_bytes = next_array_bytes
    return page, False
