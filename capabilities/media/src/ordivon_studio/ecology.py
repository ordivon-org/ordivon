from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from hashlib import sha256
import json


BOARD_THREAD_TRUTH_ROLE = "derived-coordination-view-not-task-or-domain-truth"
COLLECTION_TRUTH_ROLE = "curation-relation-not-member-truth"
FEED_TRUTH_ROLE = "derived-activity-view-not-priority-or-domain-truth"


def _canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return "sha256:" + sha256(payload).hexdigest()


def _string(value: object, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _integer(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def normalize_board_source(
    document: object,
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    """Preserve Host Board acquisition semantics alongside consumed messages.

    Bare message arrays remain supported but have no source-envelope semantics. A Host Board
    response produced before query-fence fields existed is explicitly marked unknown rather
    than inferred from hasMore/cursors.
    """

    if isinstance(document, list):
        messages = document
        fence = None
    elif isinstance(document, Mapping) and isinstance(document.get("messages"), list):
        messages = document["messages"]
        if document.get("kind") == "ordivon.host-board-list":
            selection_mode = document.get("selectionMode")
            if selection_mode is None:
                mode = "unknown-legacy-response"
                requested_after: int | None = None
                requested_limit: int | None = None
            else:
                if selection_mode not in {"latest-window", "incremental-page"}:
                    raise ValueError("Host Board selectionMode is invalid")
                mode = str(selection_mode)
                raw_after = document.get("requestedAfterSequence")
                if raw_after is not None:
                    _integer(raw_after, "requestedAfterSequence")
                requested_after = None if raw_after is None else int(raw_after)
                raw_limit = document.get("requestedLimit")
                if type(raw_limit) is not int or raw_limit < 1 or raw_limit > 100:
                    raise ValueError("Host Board requestedLimit must be in [1, 100]")
                requested_limit = int(raw_limit)
                if mode == "latest-window" and requested_after is not None:
                    raise ValueError("latest-window Board response must have null requestedAfterSequence")
                if mode == "incremental-page" and requested_after is None:
                    raise ValueError("incremental-page Board response must preserve requestedAfterSequence")

            topic = document.get("topic")
            if topic is not None:
                _string(topic, "topic")
            reply_target = document.get("replyToClientMessageId")
            if reply_target is not None:
                _string(reply_target, "replyToClientMessageId")

            def optional_nonnegative(field: str) -> int | None:
                raw = document.get(field)
                if raw is None:
                    return None
                return _integer(raw, field)

            raw_has_more = document.get("hasMore")
            if raw_has_more is not None and type(raw_has_more) is not bool:
                raise ValueError("Host Board hasMore must be boolean when present")
            fence = {
                "schemaVersion": 1,
                "kind": "ordivon.media.host-board-source-fence",
                "sourceKind": "ordivon.host-board-list",
                "selectionMode": mode,
                "requestedAfterSequence": requested_after,
                "requestedLimit": requested_limit,
                "topic": topic,
                "replyToClientMessageId": reply_target,
                "globalMessageCount": optional_nonnegative("messageCount"),
                "lastSequence": optional_nonnegative("lastSequence"),
                "nextAfterSequence": optional_nonnegative("nextAfterSequence"),
                "hasMore": raw_has_more,
                "returnedMessageCount": len(messages),
                "sourceCompletenessClaimed": False,
                "truthRole": "source-acquisition-fence-not-board-or-domain-truth",
                "truthBoundary": (
                    "This fence preserves how Host selected the supplied Board bytes. It does not "
                    "turn a latest window or one incremental page into a complete-history claim."
                ),
            }
        else:
            fence = None
    else:
        raise ValueError("Board input must be a message list or an object with messages[]")

    if not all(isinstance(item, Mapping) for item in messages):
        raise ValueError("Board messages must be JSON objects")
    return [dict(item) for item in messages], fence


def compose_board_sources(
    documents: Sequence[object],
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    """Compose one or more explicit Board inputs without erasing page acquisition fences."""

    if not documents:
        raise ValueError("at least one Board source is required")
    normalized = [normalize_board_source(document) for document in documents]
    if len(normalized) == 1:
        return normalized[0]

    if any(fence is None for _, fence in normalized):
        raise ValueError("multiple Board sources require self-describing Host Board responses")
    fences = [fence for _, fence in normalized if fence is not None]
    if any(fence["selectionMode"] != "incremental-page" for fence in fences):
        raise ValueError("multiple Board sources must form an incremental-page chain")

    topic = fences[0].get("topic")
    reply_target = fences[0].get("replyToClientMessageId")
    for fence in fences[1:]:
        if fence.get("topic") != topic or fence.get("replyToClientMessageId") != reply_target:
            raise ValueError("Board page filters differ within one source scan")

    for previous, current in zip(fences, fences[1:]):
        if previous.get("nextAfterSequence") != current.get("requestedAfterSequence"):
            raise ValueError("Board page cursor chain is discontinuous")
        previous_last = previous.get("lastSequence")
        current_last = current.get("lastSequence")
        if isinstance(previous_last, int) and isinstance(current_last, int) and current_last < previous_last:
            raise ValueError("Board page high-water regressed within one source scan")

    messages: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    seen_sequences: set[int] = set()
    for page_messages, _ in normalized:
        for message in page_messages:
            client_id = _string(message.get("clientMessageId"), "clientMessageId")
            sequence = _integer(message.get("sequence"), "sequence")
            if client_id in seen_ids or sequence in seen_sequences:
                raise ValueError("Board page chain contains duplicate message identity")
            seen_ids.add(client_id)
            seen_sequences.add(sequence)
            messages.append(message)
    messages.sort(key=lambda item: (int(item["sequence"]), str(item["clientMessageId"])))

    scan = {
        "schemaVersion": 1,
        "kind": "ordivon.media.host-board-source-scan",
        "sourceKind": "ordivon.host-board-list",
        "selectionMode": "incremental-page-chain",
        "pageCount": len(fences),
        "pageFences": fences,
        "topic": topic,
        "replyToClientMessageId": reply_target,
        "scanStartAfterSequence": fences[0].get("requestedAfterSequence"),
        "finalNextAfterSequence": fences[-1].get("nextAfterSequence"),
        "finalLastSequence": fences[-1].get("lastSequence"),
        "scanExhaustedAtFinalRead": fences[-1].get("hasMore") is False,
        "returnedMessageCount": len(messages),
        "sourceCompletenessClaimed": False,
        "truthRole": "source-acquisition-scan-not-board-or-domain-truth",
        "truthBoundary": (
            "This scan composes an exact cursor-linked sequence of Host Board pages. Exhaustion means "
            "the final filtered read had no later matching row at that observation; it is not a future "
            "completeness, conversation-boundary, priority, or domain-truth claim."
        ),
    }
    return messages, scan


def compose_board_source_set(
    documents: Sequence[object],
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    """Compose independent Board source scopes while preserving each acquisition fence.

    Multiple pages with the same exact Host filters are one cursor-linked source scan. Different
    filter scopes remain independent members of a source set. Message overlap across scopes is
    deduplicated only when the exact Board bytes agree.
    """

    if not documents:
        raise ValueError("at least one Board source is required")
    if len(documents) == 1:
        return normalize_board_source(documents[0])

    normalized = [normalize_board_source(document) for document in documents]
    if any(fence is None for _, fence in normalized):
        raise ValueError("multiple Board sources require self-describing Host Board responses")
    fences = [fence for _, fence in normalized if fence is not None]
    if any(fence["selectionMode"] == "unknown-legacy-response" for fence in fences):
        raise ValueError("legacy Board responses cannot be safely composed across source scopes")

    groups: dict[tuple[object, object], list[object]] = defaultdict(list)
    first_index: dict[tuple[object, object], int] = {}
    for index, (document, fence) in enumerate(zip(documents, fences)):
        key = (fence.get("topic"), fence.get("replyToClientMessageId"))
        groups[key].append(document)
        first_index.setdefault(key, index)

    descriptors: list[dict[str, object]] = []
    merged_by_id: dict[str, dict[str, object]] = {}
    sequence_to_id: dict[int, str] = {}
    raw_count = 0

    for key in sorted(groups, key=lambda item: first_index[item]):
        group_documents = groups[key]
        if len(group_documents) == 1:
            messages, descriptor = normalize_board_source(group_documents[0])
        else:
            group_normalized = [normalize_board_source(document) for document in group_documents]
            group_fences = [fence for _, fence in group_normalized if fence is not None]
            modes = {str(fence["selectionMode"]) for fence in group_fences}
            if modes != {"incremental-page"}:
                raise ValueError(
                    "multiple Board responses with the same filters must form one incremental-page chain"
                )
            messages, descriptor = compose_board_sources(group_documents)
        if descriptor is None:
            raise ValueError("multi-scope Board composition lost a source descriptor")
        descriptors.append(descriptor)
        raw_count += len(messages)
        for message in messages:
            client_id = _string(message.get("clientMessageId"), "clientMessageId")
            sequence = _integer(message.get("sequence"), "sequence")
            prior = merged_by_id.get(client_id)
            if prior is not None:
                if prior != message:
                    raise ValueError("overlapping Board scopes disagree on one message identity")
                continue
            prior_id = sequence_to_id.get(sequence)
            if prior_id is not None and prior_id != client_id:
                raise ValueError("overlapping Board scopes disagree on sequence identity")
            merged_by_id[client_id] = dict(message)
            sequence_to_id[sequence] = client_id

    messages = sorted(
        merged_by_id.values(),
        key=lambda item: (int(item["sequence"]), str(item["clientMessageId"])),
    )
    source_set = {
        "schemaVersion": 1,
        "kind": "ordivon.media.host-board-source-set",
        "sourceKind": "ordivon.host-board-list",
        "scopeCount": len(descriptors),
        "scopes": descriptors,
        "rawReturnedMessageCount": raw_count,
        "returnedMessageCount": len(messages),
        "overlapMessageCount": raw_count - len(messages),
        "sourceCompletenessClaimed": False,
        "truthRole": "source-acquisition-set-not-board-or-domain-truth",
        "truthBoundary": (
            "This set preserves independent Host Board acquisition scopes and only reunifies exact "
            "message bytes for derived reply-graph recovery. Scope membership, final-page exhaustion, "
            "and combined visibility do not establish global completeness, conversation boundaries, "
            "priority, or domain truth."
        ),
    }
    return messages, source_set


def derive_board_threads(messages: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    """Project Host Board reply relations into thread-shaped views.

    The projection deliberately does not create or persist a second conversation identity.
    When the root is present, the root Board clientMessageId is the stable thread coordinate.
    A bounded/paged snapshot may omit an ancestor; in that case the projection preserves an
    explicit outside-snapshot ancestor instead of inventing a root.
    """

    by_id: dict[str, dict[str, object]] = {}
    ordered: list[dict[str, object]] = []
    for raw in messages:
        item = dict(raw)
        client_id = _string(item.get("clientMessageId"), "clientMessageId")
        if client_id in by_id:
            raise ValueError("board snapshot contains duplicate clientMessageId")
        _integer(item.get("sequence"), "sequence")
        _integer(item.get("recordedAtMs"), "recordedAtMs")
        _string(item.get("authorLabel"), "authorLabel")
        _string(item.get("messageKind"), "messageKind")
        topic = item.get("topic")
        if topic is not None:
            _string(topic, "topic")
        parent = item.get("replyToClientMessageId")
        if parent is not None:
            _string(parent, "replyToClientMessageId")
        by_id[client_id] = item
        ordered.append(item)

    ordered.sort(key=lambda item: (int(item["sequence"]), str(item["clientMessageId"])))

    groups: dict[tuple[str, str], list[tuple[dict[str, object], int]]] = defaultdict(list)
    root_meta: dict[tuple[str, str], dict[str, object]] = {}

    for item in ordered:
        current = item
        depth = 0
        seen: set[str] = set()
        while True:
            current_id = str(current["clientMessageId"])
            if current_id in seen:
                raise ValueError("board reply graph contains a cycle")
            seen.add(current_id)
            parent = current.get("replyToClientMessageId")
            if parent is None:
                key = ("root", current_id)
                root_meta[key] = current
                break
            parent_item = by_id.get(str(parent))
            depth += 1
            if parent_item is None:
                key = ("outside-snapshot", str(parent))
                break
            current = parent_item
        groups[key].append((item, depth))

    result: list[dict[str, object]] = []
    for key, members in groups.items():
        mode, coordinate = key
        members.sort(key=lambda pair: (int(pair[0]["sequence"]), str(pair[0]["clientMessageId"])))
        topics = sorted(
            {str(item["topic"]) for item, _ in members if item.get("topic") is not None}
        )
        authors = sorted({str(item["authorLabel"]) for item, _ in members})
        start = int(members[0][0]["sequence"])
        end = int(members[-1][0]["sequence"])
        first_ms = min(int(item["recordedAtMs"]) for item, _ in members)
        last_ms = max(int(item["recordedAtMs"]) for item, _ in members)
        root = root_meta.get(key)
        projection: dict[str, object] = {
            "schemaVersion": 1,
            "kind": "ordivon.media.board-thread-projection",
            "threadId": f"board-thread:{coordinate}" if mode == "root" else None,
            "rootStatus": "present" if mode == "root" else "outside-snapshot",
            "rootClientMessageId": coordinate if mode == "root" else None,
            "externalAncestorClientMessageId": coordinate if mode != "root" else None,
            "messageCount": len(members),
            "replyCount": sum(
                1 for item, _ in members if item.get("replyToClientMessageId") is not None
            ),
            "maxDepth": max(depth for _, depth in members),
            "sequenceStart": start,
            "sequenceEnd": end,
            "firstRecordedAtMs": first_ms,
            "lastRecordedAtMs": last_ms,
            "topics": topics,
            "authors": authors,
            "messageClientIds": [str(item["clientMessageId"]) for item, _ in members],
            "rootMessageKind": None if root is None else root.get("messageKind"),
            "rootTopic": None if root is None else root.get("topic"),
            "truthRole": BOARD_THREAD_TRUTH_ROLE,
            "sourceRole": "Host Board messages remain the durable collaboration source",
        }
        projection["projectionDigest"] = _canonical_digest(projection)
        result.append(projection)

    result.sort(
        key=lambda item: (
            -int(item["lastRecordedAtMs"]),
            str(item.get("threadId") or item.get("externalAncestorClientMessageId")),
        )
    )
    return result


def validate_collection(value: Mapping[str, object]) -> dict[str, object]:
    """Validate a small Media curation relation without minting member truth."""

    allowed = {
        "schemaVersion",
        "kind",
        "id",
        "title",
        "publishedAtMs",
        "curatorLabel",
        "curatorialBoundary",
        "members",
        "truthRole",
    }
    if set(value) != allowed:
        raise ValueError("collection fields differ from the v1 profile")
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.media.collection":
        raise ValueError("collection identity differs")
    if value.get("truthRole") != COLLECTION_TRUTH_ROLE:
        raise ValueError("collection truthRole differs")
    collection_id = _string(value.get("id"), "id")
    if not collection_id.startswith("collection:"):
        raise ValueError("collection id must start with collection:")
    _string(value.get("title"), "title")
    _integer(value.get("publishedAtMs"), "publishedAtMs")
    _string(value.get("curatorLabel"), "curatorLabel")
    _string(value.get("curatorialBoundary"), "curatorialBoundary")
    raw_members = value.get("members")
    if not isinstance(raw_members, list) or not raw_members:
        raise ValueError("collection members must be a non-empty list")

    member_ids: set[str] = set()
    normalized_members: list[dict[str, object]] = []
    member_fields = {
        "memberId",
        "title",
        "sourceOwner",
        "sourceIdentity",
        "sourceRevision",
        "sourceObjects",
        "note",
    }
    for raw in raw_members:
        if not isinstance(raw, Mapping) or set(raw) != member_fields:
            raise ValueError("collection member fields differ from the v1 profile")
        member_id = _string(raw.get("memberId"), "memberId")
        if member_id in member_ids:
            raise ValueError("collection memberId values must be unique")
        member_ids.add(member_id)
        source_revision = _string(raw.get("sourceRevision"), "sourceRevision")
        if source_revision.startswith("turn"):
            raise ValueError("ephemeral conversation citation cannot be a collection source revision")
        source_objects = raw.get("sourceObjects")
        if not isinstance(source_objects, list) or not source_objects:
            raise ValueError("sourceObjects must be a non-empty list")
        normalized_objects: list[dict[str, str]] = []
        seen_paths: set[str] = set()
        for source_object in source_objects:
            if not isinstance(source_object, Mapping) or set(source_object) != {"path", "digest"}:
                raise ValueError("sourceObjects entries must contain exactly path and digest")
            source_path = _string(source_object.get("path"), "sourceObjects.path")
            source_digest = _string(source_object.get("digest"), "sourceObjects.digest")
            if source_path in seen_paths:
                raise ValueError("sourceObjects paths must be unique within one member")
            seen_paths.add(source_path)
            if not source_digest.startswith("sha256:") or len(source_digest) != 71:
                raise ValueError("sourceObjects.digest must be one exact sha256 digest")
            normalized_objects.append({"path": source_path, "digest": source_digest})
        note = raw.get("note")
        if note is not None:
            _string(note, "note", allow_empty=False)
        normalized_members.append(
            {
                "memberId": member_id,
                "title": _string(raw.get("title"), "title"),
                "sourceOwner": _string(raw.get("sourceOwner"), "sourceOwner"),
                "sourceIdentity": _string(raw.get("sourceIdentity"), "sourceIdentity"),
                "sourceRevision": source_revision,
                "sourceObjects": normalized_objects,
                "note": note,
            }
        )

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.media.collection",
        "id": collection_id,
        "title": str(value["title"]),
        "publishedAtMs": int(value["publishedAtMs"]),
        "curatorLabel": str(value["curatorLabel"]),
        "curatorialBoundary": str(value["curatorialBoundary"]),
        "members": normalized_members,
        "truthRole": COLLECTION_TRUTH_ROLE,
    }
    return result


def collection_feed_item(collection: Mapping[str, object]) -> dict[str, object]:
    item = validate_collection(collection)
    return {
        "kind": "collection",
        "sourceIdentity": item["id"],
        "observedAtMs": item["publishedAtMs"],
        "title": item["title"],
        "summary": f"Curated collection with {len(item['members'])} independently sourced members.",
        "truthRole": item["truthRole"],
        "sourceDigest": _canonical_digest(item),
    }


def thread_feed_items(threads: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for thread in threads:
        if thread.get("kind") != "ordivon.media.board-thread-projection":
            raise ValueError("thread feed input is not a Board thread projection")
        if thread.get("rootStatus") != "present":
            continue
        thread_id = _string(thread.get("threadId"), "threadId")
        topics = thread.get("topics")
        if not isinstance(topics, list):
            raise ValueError("thread topics must be a list")
        result.append(
            {
                "kind": "board-thread",
                "sourceIdentity": thread_id,
                "observedAtMs": _integer(thread.get("lastRecordedAtMs"), "lastRecordedAtMs"),
                "title": str(thread.get("rootTopic") or thread_id),
                "summary": (
                    f"{int(thread['messageCount'])} messages; "
                    f"{int(thread['replyCount'])} replies; topics={','.join(map(str, topics)) or 'none'}"
                ),
                "truthRole": BOARD_THREAD_TRUTH_ROLE,
                "sourceDigest": _string(thread.get("projectionDigest"), "projectionDigest"),
            }
        )
    return result


def derive_activity_feed(
    items: Iterable[Mapping[str, object]], *, observed_at_ms: int
) -> dict[str, object]:
    """Build an exhaustive time-ordered projection over the explicitly supplied input set."""

    _integer(observed_at_ms, "observedAtMs")
    normalized: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for raw in items:
        kind = _string(raw.get("kind"), "kind")
        identity = _string(raw.get("sourceIdentity"), "sourceIdentity")
        key = (kind, identity)
        if key in seen:
            raise ValueError("feed input contains duplicate source identity")
        seen.add(key)
        normalized.append(
            {
                "kind": kind,
                "sourceIdentity": identity,
                "observedAtMs": _integer(raw.get("observedAtMs"), "observedAtMs"),
                "title": _string(raw.get("title"), "title"),
                "summary": _string(raw.get("summary"), "summary"),
                "truthRole": _string(raw.get("truthRole"), "truthRole"),
                "sourceDigest": _string(raw.get("sourceDigest"), "sourceDigest"),
            }
        )
    normalized.sort(key=lambda item: (-int(item["observedAtMs"]), str(item["sourceIdentity"])))
    projection: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.media.activity-feed-projection",
        "observedAtMs": observed_at_ms,
        "ordering": "source-observed-time-descending",
        "inputItemCount": len(normalized),
        "items": normalized,
        "priorityInferred": False,
        "sourceCompletenessClaimed": False,
        "truthRole": FEED_TRUTH_ROLE,
        "truthBoundary": (
            "The feed orders only the explicitly supplied source projections. Presence does not "
            "create priority or truth; absence does not establish that an event, work, message, "
            "Task, Production, or source object does not exist."
        ),
    }
    projection["projectionDigest"] = _canonical_digest(projection)
    return projection
