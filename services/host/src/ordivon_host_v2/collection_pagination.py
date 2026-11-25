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


def bounded_page[T](
    items: Sequence[T],
    *,
    max_bytes: int,
    collection_key: str,
    envelope: Callable[[T | None, bool], dict[str, Any]],
    source_has_more: bool,
    minimum: int = MIN_COLLECTION_MAX_BYTES,
) -> dict[str, Any]:
    """Return an exact wire page within the canonical byte budget.

    The same projection supplies metadata for sizing and for return.
    RFC 8785 array elements are independently encoded and joined by commas.
    Stop at first overflowing prefix; only a consumed source can return
    hasMore=false. Cursor metadata belongs to the last returned item.
    """
    validate_max_bytes(max_bytes, minimum=minimum)
    page: list[T] = []
    array_bytes = 0
    accepted_metadata = None

    def metadata_for(last: T | None, has_more: bool) -> dict[str, Any]:
        metadata = envelope(last, has_more)
        if collection_key in metadata:
            raise ValueError("collection metadata must omit its array")
        return metadata

    if not items:
        if source_has_more:
            raise ValueError("empty source page cannot have more items")
        metadata = metadata_for(None, False)
        result = {**metadata, collection_key: []}
        if len(canonical_bytes(result)) > max_bytes:
            raise ValueError("max_bytes cannot fit the empty response envelope")
        return result

    for index, item in enumerate(items):
        has_more = source_has_more or index + 1 < len(items)
        metadata = metadata_for(item, has_more)
        next_array_bytes = array_bytes + len(canonical_bytes(item)) + int(bool(page))
        size = len(canonical_bytes({**metadata, collection_key: []})) + next_array_bytes
        if size > max_bytes:
            if accepted_metadata is None:
                raise ValueError("max_bytes cannot fit one legal item plus response envelope")
            return {**accepted_metadata, collection_key: page}
        page.append(item)
        array_bytes = next_array_bytes
        accepted_metadata = metadata
    if accepted_metadata is None:
        raise RuntimeError("nonempty source produced no page")
    return {**accepted_metadata, collection_key: page}
