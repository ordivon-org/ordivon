from __future__ import annotations

import argparse
from datetime import UTC, datetime
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ordivon_studio.ecology import (  # noqa: E402
    collection_feed_item,
    derive_activity_feed,
    derive_board_threads,
    normalize_board_source,
    thread_feed_items,
    validate_collection,
)

HERE = Path(__file__).resolve().parent


def _read_json(name: str) -> object:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def _iso(ms: object) -> str:
    value = int(ms)
    return datetime.fromtimestamp(value / 1000, tz=UTC).isoformat(timespec="seconds")


def _projection() -> dict[str, object]:
    board = _read_json("board-snapshot.json")
    messages, board_source_fence = normalize_board_source(board)
    threads = derive_board_threads(messages)
    collection_raw = _read_json("daily-cabinet.collection.json")
    if not isinstance(collection_raw, dict):
        raise ValueError("daily-cabinet.collection.json must be an object")
    collection = validate_collection(collection_raw)
    items = thread_feed_items(threads) + [collection_feed_item(collection)]
    observed_at_ms = max(int(item["observedAtMs"]) for item in items)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.media.ecology-pilot-encounter",
        "boardSourceFence": board_source_fence,
        "threads": threads,
        "collections": [collection],
        "feed": derive_activity_feed(items, observed_at_ms=observed_at_ms),
        "truthBoundary": (
            "Human encounter over derived Media projections only. Host Board and member owners "
            "retain source truth; card order is not priority."
        ),
    }


def _render(
    projection: dict[str, object],
    *,
    activity_limit: int | None = None,
    thread_limit: int | None = None,
) -> str:
    feed = projection["feed"]
    threads = projection["threads"]
    collections = projection["collections"]
    board_source_fence = projection.get("boardSourceFence")
    assert isinstance(feed, dict)
    assert isinstance(threads, list)
    assert isinstance(collections, list)

    if isinstance(board_source_fence, dict):
        source_kind = str(board_source_fence.get("kind"))
        if source_kind == "ordivon.media.host-board-source-set":
            source_note = (
                "Board acquisition: <strong>independent source set</strong>"
                f" · {int(board_source_fence['scopeCount'])} scopes"
                f" · {int(board_source_fence['returnedMessageCount'])} exact messages"
                " · completeness not claimed"
            )
        else:
            selection_mode = escape(str(board_source_fence.get("selectionMode")))
            requested_limit = board_source_fence.get("requestedLimit")
            source_note = (
                f"Board acquisition: <strong>{selection_mode}</strong>"
                + (
                    f" · requested limit {int(requested_limit)}"
                    if isinstance(requested_limit, int)
                    else ""
                )
                + " · completeness not claimed"
            )
    else:
        source_note = "Board acquisition: raw message array · source selection semantics unavailable"

    feed_items = list(feed["items"])
    thread_items = list(threads)
    if activity_limit is not None:
        if activity_limit < 1:
            raise ValueError("activity_limit must be positive when supplied")
        feed_items = feed_items[:activity_limit]
    if thread_limit is not None:
        if thread_limit < 1:
            raise ValueError("thread_limit must be positive when supplied")
        thread_items = thread_items[:thread_limit]
    activity_window = (
        f"showing {len(feed_items)} of {len(feed['items'])} · chronological window · not priority"
    )
    thread_window = (
        f"showing {len(thread_items)} of {len(threads)} · latest observed threads · not priority"
    )

    feed_cards: list[str] = []
    for item in feed_items:
        feed_cards.append(
            f'''<article class="card activity" data-kind="{escape(str(item['kind']))}">
  <div class="eyebrow">{escape(str(item['kind']))} · derived</div>
  <h2>{escape(str(item['title']))}</h2>
  <p>{escape(str(item['summary']))}</p>
  <div class="meta"><time>{escape(_iso(item['observedAtMs']))}</time><span>not priority</span></div>
  <code>{escape(str(item['sourceIdentity']))}</code>
</article>'''
        )

    thread_cards: list[str] = []
    for thread in thread_items:
        root_present = thread.get("rootStatus") == "present"
        if root_present:
            coordinate = str(thread["threadId"])
            title = str(thread.get("rootTopic") or coordinate)
            eyebrow = "conversation projection"
            identity_detail = (
                f"<code>{escape(coordinate)}</code>"
                f"<p>Root: {escape(str(thread['rootClientMessageId']))}</p>"
            )
        else:
            ancestor = str(thread["externalAncestorClientMessageId"])
            topics = thread.get("topics") or []
            title = str(topics[0]) if topics else "Reply branch · context outside supplied source"
            eyebrow = "reply branch · ancestor outside source"
            identity_detail = (
                "<p>No complete Thread identity is claimed.</p>"
                f"<p>External ancestor: <code>{escape(ancestor)}</code></p>"
            )
        thread_cards.append(
            f'''<article class="card conversation-card" data-root-status="{escape(str(thread['rootStatus']))}">
  <div class="eyebrow">{escape(eyebrow)}</div>
  <h2>{escape(title)}</h2>
  <p>{int(thread['messageCount'])} visible messages · {int(thread['replyCount'])} replies · visible depth {int(thread['maxDepth'])}</p>
  <div class="chips">{''.join(f'<span>{escape(str(topic))}</span>' for topic in thread['topics'])}</div>
  <details><summary>Exact Board coordinate</summary>{identity_detail}</details>
</article>'''
        )

    collection_cards: list[str] = []
    for collection in collections:
        members: list[str] = []
        for member in collection["members"]:
            source_objects = "".join(
                f"<li><code>{escape(str(obj['path']))}</code><small>{escape(str(obj['digest']))}</small></li>"
                for obj in member["sourceObjects"]
            )
            members.append(
                f'''<article class="work">
  <div class="eyebrow">{escape(str(member['sourceOwner']))}</div>
  <h3>{escape(str(member['title']))}</h3>
  <code>{escape(str(member['sourceIdentity']))}</code>
  <details><summary>Provenance · {len(member['sourceObjects'])} object(s)</summary>
    <p>revision <code>{escape(str(member['sourceRevision']))}</code></p><ul>{source_objects}</ul>
  </details>
</article>'''
            )
        collection_cards.append(
            f'''<section class="collection card">
  <div class="eyebrow">curated collection · member truth stays source-owned</div>
  <h2>{escape(str(collection['title']))}</h2>
  <p>{escape(str(collection['curatorialBoundary']))}</p>
  <div class="works">{''.join(members)}</div>
</section>'''
        )

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ordivon Media Ecology — Pilot</title>
<style>
:root {{ color-scheme: light dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: Canvas; color: CanvasText; }}
main {{ width: min(1160px, calc(100% - 32px)); margin: 0 auto; padding: 48px 0 80px; }}
header {{ display: grid; gap: 12px; margin-bottom: 36px; max-width: 840px; }}
h1 {{ margin: 0; font-size: clamp(2rem, 6vw, 4.8rem); line-height: .95; letter-spacing: -.055em; }}
header p, .card > p {{ line-height: 1.55; max-width: 72ch; }}
.rule {{ border-top: 1px solid color-mix(in srgb, CanvasText 22%, transparent); margin: 34px 0; }}
section.zone > h2 {{ font-size: .82rem; text-transform: uppercase; letter-spacing: .16em; opacity: .68; }}
.grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }}
.card {{ border: 1px solid color-mix(in srgb, CanvasText 18%, transparent); border-radius: 20px; padding: 20px; background: color-mix(in srgb, Canvas 96%, CanvasText 4%); min-width: 0; }}
.card h2, .work h3 {{ margin: 8px 0 10px; letter-spacing: -.025em; }}
.eyebrow {{ font-size: .72rem; text-transform: uppercase; letter-spacing: .13em; opacity: .62; }}
.meta {{ display: flex; flex-wrap: wrap; gap: 8px 18px; font-size: .78rem; opacity: .65; margin: 16px 0 10px; }}
code {{ display: inline-block; max-width: 100%; overflow-wrap: anywhere; font-size: .75rem; opacity: .78; }}
.chips {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 14px 0; }}
.chips span {{ border: 1px solid color-mix(in srgb, CanvasText 18%, transparent); border-radius: 999px; padding: 5px 9px; font-size: .72rem; }}
details {{ margin-top: 14px; }}
summary {{ cursor: pointer; font-size: .8rem; }}
.works {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 18px; }}
.work {{ padding: 16px; border-radius: 14px; background: color-mix(in srgb, Canvas 90%, CanvasText 10%); min-width: 0; }}
.work ul {{ padding-left: 18px; }} .work li {{ margin: 9px 0; }} .work small {{ display: block; overflow-wrap: anywhere; opacity: .55; }}
.source-fence {{ padding: 10px 12px; border: 1px solid color-mix(in srgb, CanvasText 18%, transparent); border-radius: 12px; font-size: .78rem; opacity: .76; }}
.boundary {{ margin-top: 32px; padding: 16px 0; border-top: 1px solid color-mix(in srgb, CanvasText 18%, transparent); font-size: .82rem; opacity: .68; }}
@media (max-width: 760px) {{ main {{ width: min(100% - 22px, 680px); padding-top: 28px; }} .grid, .works {{ grid-template-columns: 1fr; }} .card {{ border-radius: 16px; }} }}
</style>
</head>
<body>
<main>
<header>
  <div class="eyebrow">Media Ecology · natural pilot · 2026-08-30</div>
  <h1>Activity without a second truth system.</h1>
  <p>A Human-facing encounter over explicit Board and Collection projections. Threads are derived from Host reply edges; collection membership is curatorial; chronological placement is not priority.</p>
  <p class="source-fence">{source_note}</p>
</header>
<div class="rule"></div>
<section class="zone"><h2>Recent activity · {escape(activity_window)}</h2><div class="grid">{''.join(feed_cards)}</div></section>
<div class="rule"></div>
<section class="zone"><h2>Conversation · {escape(thread_window)}</h2><div class="grid">{''.join(thread_cards)}</div></section>
<div class="rule"></div>
<section class="zone"><h2>Collection</h2>{''.join(collection_cards)}</section>
<p class="boundary">{escape(str(projection['truthBoundary']))}</p>
</main>
<script>
const root = document.documentElement;
root.dataset.overflowX = String(root.scrollWidth > root.clientWidth);
root.dataset.activityCards = String(document.querySelectorAll('.activity').length);
root.dataset.activityTotal = "{len(feed['items'])}";
root.dataset.threadCards = String(document.querySelectorAll('.conversation-card').length);
root.dataset.threadTotal = "{len(threads)}";
root.dataset.collectionWorks = String(document.querySelectorAll('.work').length);
</script>
</body>
</html>'''


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render one Human-facing Media Ecology projection without changing source truth."
    )
    parser.add_argument("--projection", help="existing ecology projection JSON; default rebuilds the pilot")
    parser.add_argument("--html", help="HTML output path; default is the pilot index.html")
    parser.add_argument("--activity-limit", type=int, help="chronological Human presentation window")
    parser.add_argument("--thread-limit", type=int, help="latest-observed Human thread window")
    args = parser.parse_args()

    if args.projection:
        raw = json.loads(Path(args.projection).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("projection input must be a JSON object")
        projection = raw
    else:
        projection = _projection()
        (HERE / "projection.json").write_text(
            json.dumps(projection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    html_path = Path(args.html) if args.html else HERE / "index.html"
    html_path.write_text(
        _render(
            projection,
            activity_limit=args.activity_limit,
            thread_limit=args.thread_limit,
        )
        + "\n",
        encoding="utf-8",
    )
    print(projection["feed"]["projectionDigest"])


if __name__ == "__main__":
    main()
