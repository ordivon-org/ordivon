"""Disposable PG18 falsifier for R44 per-subscription LATERAL at high fanout."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import psycopg
from bench_attention_compare_r44 import baseline_query, compare_pages, extract
from bench_attention_incremental_r44 import node_metrics, percentile
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

import ordivon_host_v2.attention_projections as projections
from ordivon_host_v2.attention_sql import ATTENTION_DELTA_SQL
from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.canonical_json import canonical_digest


def seed(conn: psycopg.Connection) -> tuple[int, int]:
    sender = "actor:bench:r47:sender"
    levels = (1, 8, 32, 128, 256)
    actors = [f"actor:bench:r47:fanout:{k}" for k in levels]
    overlap_actor = "actor:bench:r47:fanout:space-and-128"
    for actor in (sender, *actors, overlap_actor):
        conn.execute("INSERT INTO actor_refs(actor_ref,actor_kind) VALUES (%s,'agent')", (actor,))
    space = "space:bench:r47:manytopics"
    conn.execute(
        "INSERT INTO spaces(space_ref,purpose,created_by_actor_ref) VALUES (%s,%s,%s)",
        (space, "PG18 R47 synthetic fanout only", sender),
    )
    for i in range(256):
        topic = f"topic:bench:r47:manytopics:{i:03d}"
        conn.execute(
            "INSERT INTO topics(topic_ref,space_ref,title,state,created_by_actor_ref) VALUES (%s,%s,%s,'open',%s)",
            (topic, space, topic, sender),
        )
    for n, actor in zip(levels, actors):
        for i in range(n):
            conn.execute(
                "INSERT INTO subscriptions(actor_ref,target_kind,target_ref) VALUES (%s,'topic',%s)",
                (actor, f"topic:bench:r47:manytopics:{i:03d}"),
            )
    for i in range(128):
        conn.execute(
            "INSERT INTO subscriptions(actor_ref,target_kind,target_ref) VALUES (%s,'topic',%s)",
            (overlap_actor, f"topic:bench:r47:manytopics:{i:03d}"),
        )
    conn.execute(
        "INSERT INTO subscriptions(actor_ref,target_kind,target_ref) VALUES (%s,'space',%s)",
        (overlap_actor, space),
    )
    base = int(
        conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()["value"]
    )
    cursor = base + 100
    docs = []
    body = "R47 synthetic content no production references."
    # Mixed topic order; every target has 32 messages (256*32=8192).
    for i in range(8192):
        cursor += 1
        topic = f"topic:bench:r47:manytopics:{i % 256:03d}"
        ref = f"message:bench:r47:{i:05d}"
        ms = 1730000000000 + cursor
        digest = canonical_digest(
            {
                "messageRef": ref,
                "spaceRef": space,
                "topicRef": topic,
                "authorActorRef": sender,
                "messageKind": "note",
                "body": body,
                "recordedAtMs": ms,
            }
        )
        docs.append((ref, "request:" + ref, space, topic, sender, "note", body, digest, ms, cursor))
    with conn.transaction():
        with conn.cursor().copy(
            "COPY messages (message_ref,client_request_id,space_ref,topic_ref,"
            "author_actor_ref,message_kind,body,message_digest,recorded_at_ms,change_sequence) FROM STDIN"
        ) as cp:
            for row in docs:
                cp.write_row(row)
        conn.execute("UPDATE swf_change_clock SET value=%s WHERE singleton", (cursor,))
    conn.execute("ANALYZE")
    conn.commit()
    return base + 100, cursor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--iterations", type=int, default=48)
    parser.add_argument("--output", required=True)
    a = parser.parse_args()
    opts = conninfo_to_dict(a.dsn)
    if opts.get("host") != "127.0.0.1" or opts.get("dbname") != "hostbench":
        raise ValueError("R47 requires a fresh loopback-only disposable hostbench database")
    if a.iterations < 24:
        raise ValueError("R47 requires at least 24 paired samples")
    with psycopg.connect(a.dsn, row_factory=dict_row, autocommit=True) as conn:
        assert (
            int(
                conn.execute(
                    "SELECT schema_version FROM host_v2_schema WHERE singleton"
                ).fetchone()["schema_version"]
            )
            == 14
        )
        # Refuse nonempty schemas before modifying any owner's existing records.
        for relation in ("actor_refs", "spaces", "topics", "messages", "subscriptions"):
            if conn.execute(f"SELECT count(*) AS n FROM {relation}").fetchone()["n"] != 0:
                raise ValueError(f"R47 requires a fresh empty schema: {relation} is not empty")
        after, high = seed(conn)
        store = AttentionStore(a.dsn)
        base, candidate = baseline_query(), ATTENTION_DELTA_SQL
        report = {
            "kind": "ordivon.host.attention.fanout.r47",
            "schema": 14,
            "total_messages": 8192,
            "topic_count": 256,
            "after": after,
            "high": high,
            "iterations": a.iterations,
            "actors": {},
        }
        for name, actor in [
            *((str(k), f"actor:bench:r47:fanout:{k}") for k in (1, 8, 32, 128, 256)),
            ("space_plus_128", "actor:bench:r47:fanout:space-and-128"),
        ]:
            ref = extract(base, store, actor, after, 10)
            assert ref == extract(candidate, store, actor, after, 10)
            timings = {"baseline": [], "candidate": []}
            navs = {"baseline": [], "candidate": []}
            for i in range(a.iterations):
                pair = (
                    (("baseline", base), ("candidate", candidate))
                    if i % 2 == 0
                    else (("candidate", candidate), ("baseline", base))
                )
                nav_responses = {}
                for label, sql in pair:
                    t0 = time.perf_counter_ns()
                    x = extract(sql, store, actor, after, 10)
                    timings[label].append((time.perf_counter_ns() - t0) / 1e6)
                    assert x == ref
                    projections.ATTENTION_DELTA_SQL = sql
                    t1 = time.perf_counter_ns()
                    nav = store.reentry(actor, after_sequence=after, limit=10)
                    navs[label].append((time.perf_counter_ns() - t1) / 1e6)
                    nav_responses[label] = nav
                assert nav_responses["baseline"] == nav_responses["candidate"]
            exp = {}
            for label, sql in (("baseline", base), ("candidate", candidate)):
                row = conn.execute(
                    "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql,
                    {"actor_ref": actor, "after_sequence": after, "high": high, "limit": 11},
                ).fetchone()
                plan = row["QUERY PLAN"][0]
                exp[label] = node_metrics(plan["Plan"]) | {
                    "execution_ms": round(float(plan["Execution Time"]), 3),
                    "planning_ms": round(float(plan["Planning Time"]), 3),
                }
            pages = compare_pages(store, base, candidate, actor, after, limit=101, pages=200)
            data = {
                "first_page_count": len(ref["events"]),
                "first_reasons": ref["events"][0]["reasons"] if ref["events"] else [],
                "pages": pages,
                "baseline": {
                    "delta_p50": percentile(timings["baseline"], 0.5),
                    "delta_p95": percentile(timings["baseline"], 0.95),
                    "reentry_p50": percentile(navs["baseline"], 0.5),
                    "reentry_p95": percentile(navs["baseline"], 0.95),
                    "explain": exp["baseline"],
                },
                "candidate": {
                    "delta_p50": percentile(timings["candidate"], 0.5),
                    "delta_p95": percentile(timings["candidate"], 0.95),
                    "reentry_p50": percentile(navs["candidate"], 0.5),
                    "reentry_p95": percentile(navs["candidate"], 0.95),
                    "explain": exp["candidate"],
                },
            }
            report["actors"][name] = data
            print(
                "R47_FANOUT",
                name,
                json.dumps(
                    {
                        t: {k: v for k, v in data[t].items() if k != "explain"}
                        | {
                            "sql_ms": data[t]["explain"]["execution_ms"],
                            "leaf_rows": data[t]["explain"]["scan_leaf_actual_rows_sum"],
                            "buffers": data[t]["explain"]["shared_hit"],
                        }
                        for t in ("baseline", "candidate")
                    }
                    | {
                        "pages": pages["pages"],
                        "total_events": pages["events_total"],
                        "first_reasons": data["first_reasons"],
                    }
                ),
                flush=True,
            )
        output = Path(a.output)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print("R47_FANOUT_ALL_PASS", str(output), flush=True)


if __name__ == "__main__":
    main()
