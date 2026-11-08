"""Source-bound Production and Ecology projection CLI handlers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..ecology.board import compose_board_source_set, derive_board_threads
from ..ecology.collection import collection_feed_item, validate_collection
from ..ecology.feed import derive_activity_feed, thread_feed_items
from ..production_context import build_production_context
from . import _write_json


def _parse_named_paths(values: list[str], *, option: str) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for value in values:
        name, separator, path = value.partition("=")
        if not separator or not name or not path:
            raise ValueError(f"{option} must use ID=PATH")
        if name in paths:
            raise ValueError(f"duplicate {option} id: {name}")
        paths[name] = Path(path)
    return paths


def _parse_source_repositories(values: list[str]) -> dict[str, Path]:
    return _parse_named_paths(values, option="--source-repo")


def _command_production_context(args: argparse.Namespace) -> int:
    _write_json(
        build_production_context(
            Path(args.production_root),
            source_repositories=_parse_source_repositories(args.source_repo),
            output_files=_parse_named_paths(args.output_file, option="--output-file"),
        )
    )
    return 0


def _read_json_file(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _command_ecology_threads(args: argparse.Namespace) -> int:
    messages, source_fence = compose_board_source_set([_read_json_file(path) for path in args.board])
    _write_json({
        "schemaVersion": 1,
        "kind": "ordivon.media.board-thread-set-projection",
        "boardSourceFence": source_fence,
        "threads": derive_board_threads(messages),
        "sourceMessageCount": len(messages),
        "truthBoundary": "Thread identity is derived from Host Board reply relations; this output does not create a second conversation authority.",
    })
    return 0


def _command_ecology_collection(args: argparse.Namespace) -> int:
    document = _read_json_file(args.collection)
    if not isinstance(document, dict):
        raise ValueError("Collection input must be a JSON object")
    _write_json(validate_collection(document))
    return 0


def _command_ecology_project(args: argparse.Namespace) -> int:
    feed_items: list[dict[str, object]] = []
    threads: list[dict[str, object]] = []
    board_source_fence: dict[str, object] | None = None
    if args.board:
        messages, board_source_fence = compose_board_source_set(
            [_read_json_file(path) for path in args.board]
        )
        threads = derive_board_threads(messages)
        feed_items.extend(thread_feed_items(threads))
    collections: list[dict[str, object]] = []
    for path in args.collection:
        document = _read_json_file(path)
        if not isinstance(document, dict):
            raise ValueError("Collection input must be a JSON object")
        collection = validate_collection(document)
        collections.append(collection)
        feed_items.append(collection_feed_item(collection))
    if not threads and not collections:
        raise ValueError("ecology project requires at least one Board or Collection source")
    if args.observed_at_ms is not None:
        observed_at_ms = args.observed_at_ms
    elif feed_items:
        observed_at_ms = max(int(item["observedAtMs"]) for item in feed_items)
    else:
        observed_at_ms = max(int(thread["lastRecordedAtMs"]) for thread in threads)
    _write_json({
        "schemaVersion": 1,
        "kind": "ordivon.media.ecology-projection",
        "boardSourceFence": board_source_fence,
        "threads": threads,
        "collections": collections,
        "feed": derive_activity_feed(feed_items, observed_at_ms=observed_at_ms),
        "truthBoundary": "This is a derived Media projection over explicitly supplied sources. It does not replace Host, Task, Production, collection-member, or owner truth.",
    })
    return 0
