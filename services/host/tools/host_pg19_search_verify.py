"""Native search-index refinement witness for a private PG major upgrade.

A copied index is a derived representation, not the message authority.
PG19 can change lexical classification under non-libc locale providers.
The independent sequential oracle uses the current server's predicate;
cross-major lexical equality is deliberately not the acceptance criterion.
"""

from __future__ import annotations

from typing import Any

import psycopg

from ordivon_host_v2.collaboration_inputs import MessageInput
from ordivon_host_v2.social_store import SocialStore

FTS_INDEX = "message_search_fts_idx"
PREDICATE = "to_tsvector('simple',body) @@ websearch_to_tsquery('simple',%s)"
CASES = (
    ("dash", "host—migration"),
    ("middle-dot", "host·migration"),
    ("emoji", "host🙂migration"),
    ("curly", "host“migration”"),
    ("accent", "Éclair résumé"),
    ("cjk", "独立迁移证据𠀀"),
)
QUERIES = ("host", "migration", "éclair", "résumé", "absenttoken")


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(reason)


def seed_search(dsn: str, *, space: str, topic: str, actor: str) -> None:
    social = SocialStore(dsn)
    for n, (name, body) in enumerate(CASES, 10):
        social.post_message(
            MessageInput(
                message_ref=f"message:pg19:search:{name}",
                client_request_id=f"pg19:search:{name}",
                space_ref=space,
                topic_ref=topic,
                author_actor_ref=actor,
                body=body,
                recorded_at_ms=n,
            )
        )


def _plan_nodes(node: dict[str, Any]):
    yield node
    for child in node.get("Plans", []):
        yield from _plan_nodes(child)


def _read(dsn: str, query: str, *, indexed: bool) -> list[str]:
    sql = f"SELECT message_ref FROM messages WHERE {PREDICATE} ORDER BY message_ref"
    with psycopg.connect(dsn) as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        conn.execute("SET LOCAL enable_indexscan=off")
        conn.execute("SET LOCAL enable_indexonlyscan=off")
        conn.execute("SET LOCAL enable_seqscan=" + ("off" if indexed else "on"))
        conn.execute("SET LOCAL enable_bitmapscan=" + ("on" if indexed else "off"))
        row = conn.execute("EXPLAIN (FORMAT JSON) " + sql, (query,)).fetchone()
        require(row is not None, "missing native search plan")
        nodes = list(_plan_nodes(row[0][0]["Plan"]))
        if indexed:
            require(any(n.get("Index Name") == FTS_INDEX for n in nodes), "FTS index plan missing")
        else:
            require(
                any(
                    n.get("Node Type") == "Seq Scan" and n.get("Relation Name") == "messages"
                    for n in nodes
                ),
                "sequential search oracle plan missing",
            )
        return [r[0] for r in conn.execute(sql, (query,)).fetchall()]


def observe_search(dsn: str) -> dict[str, Any]:
    with psycopg.connect(dsn) as conn:
        row = conn.execute(
            "SELECT datlocprovider,datcollate,datctype,datlocale,datcollversion "
            "FROM pg_database WHERE datname=current_database()"
        ).fetchone()
        require(row is not None, "missing database locale identity")
        index = conn.execute(
            "SELECT indisvalid,indisready,pg_get_indexdef(indexrelid) FROM pg_index "
            "WHERE indexrelid=to_regclass('message_search_fts_idx') "
            "AND indrelid=to_regclass('messages')"
        ).fetchone()
        require(
            index is not None and tuple(index[:2]) == (True, True),
            "missing or invalid Host FTS index",
        )
        require(
            "to_tsvector" in index[2] and "USING gin" in index[2], "unexpected Host FTS definition"
        )
        vector_columns = conn.execute(
            "SELECT attname FROM pg_attribute WHERE attrelid=to_regclass('messages') "
            "AND attnum>0 AND NOT attisdropped AND atttypid='tsvector'::regtype"
        ).fetchall()
        require(not vector_columns, "stored tsvector requires recomputation")
        trgm = conn.execute("SELECT to_regclass('message_body_trgm_idx') IS NOT NULL").fetchone()
        require(trgm is not None and not trgm[0], "retired trigram index unexpectedly exists")
        vectors = conn.execute(
            "SELECT message_ref,to_tsvector('simple',body)::text FROM messages ORDER BY message_ref"
        ).fetchall()
    return {
        "locale": list(row),
        "indexDefinition": index[2],
        "vectors": dict(vectors),
        "indexed": {q: _read(dsn, q, indexed=True) for q in QUERIES},
        "sequential": {q: _read(dsn, q, indexed=False) for q in QUERIES},
    }


def reindex_and_verify(dsn: str, *, topic: str, before: dict[str, Any]) -> dict[str, Any]:
    # This witness is invoked only from the disposable private-cluster upgrade.
    stale = observe_search(dsn)
    require(stale["locale"][:4] == before["locale"][:4], "locale identity changed")
    require(before["indexed"] == before["sequential"], "original index disagrees with scan")
    require(stale["indexed"] != stale["sequential"], "stale copied index negative not observed")
    mismatches = [q for q in QUERIES if stale["indexed"][q] != stale["sequential"][q]]
    print(f"stale_fts_index_negative={mismatches!r}", flush=True)
    print(f"stale_index_observed={stale['indexed']!r}", flush=True)
    print(f"current_sequential_oracle={stale['sequential']!r}", flush=True)
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("REINDEX INDEX message_search_fts_idx")
    repaired = observe_search(dsn)
    require(
        repaired["indexed"] == repaired["sequential"] == stale["sequential"],
        "reindex did not refine current lexical semantics",
    )
    require(repaired["vectors"] == stale["vectors"], "reindex changed native lexical values")
    social = SocialStore(dsn)
    for q in QUERIES:
        page = social.search_messages(q, topic_ref=topic)
        require(not page["hasMore"], "unexpected search witness pagination")
        require(
            sorted(r["messageRef"] for r in page["messages"]) == repaired["sequential"][q],
            "public Host search differs from current scan",
        )
    print(
        f"lexical_changes={sum(before['vectors'][k] != v for k, v in repaired['vectors'].items())}",
        flush=True,
    )
    print("fts_reindex_indexed_sequential_public_exact=true", flush=True)
    return repaired
