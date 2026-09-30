from __future__ import annotations

from collections.abc import Callable, Sequence

from .canonical import canonical_bytes

DEFAULT_COLLECTION_MAX_BYTES = 262_144
DEFAULT_MESSAGE_COLLECTION_MAX_BYTES = 524_288
DEFAULT_SPACE_MAX_BYTES = 2_097_152
MAX_COLLECTION_MAX_BYTES = 4_194_304
MIN_COLLECTION_MAX_BYTES = 16_384
MIN_MESSAGE_COLLECTION_MAX_BYTES = 131_072
MIN_SPACE_MAX_BYTES = 1_048_576


def validate_max_bytes(max_bytes: int, *, minimum: int = MIN_COLLECTION_MAX_BYTES) -> None:
    if not minimum <= max_bytes <= MAX_COLLECTION_MAX_BYTES:
        raise ValueError(f"max_bytes must be in [{minimum},{MAX_COLLECTION_MAX_BYTES}]")


def bounded_prefix[T](
    items: Sequence[T],
    *,
    max_bytes: int,
    envelope: Callable[[list[T]], object],
    minimum: int = MIN_COLLECTION_MAX_BYTES,
) -> tuple[list[T], bool]:
    """Return the longest prefix whose complete canonical response fits max_bytes."""
    validate_max_bytes(max_bytes, minimum=minimum)
    page: list[T] = []
    for item in items:
        candidate = [*page, item]
        if len(canonical_bytes(envelope(candidate))) > max_bytes:
            if not page:
                raise ValueError("max_bytes cannot fit one legal item plus response envelope")
            return page, True
        page = candidate
    return page, False
