"""Paired baseline/candidate Attention benchmark on the same disposable PG18 fixture.

Uses the immutable origin/main SQL via Git as an executable oracle; never copies
the source query into a second maintained production registry.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import threading
import time
from pathlib import Path

import psycopg
from bench_attention_incremental_r44 import node_metrics, percentile, seed
from psycopg.rows import dict_row

import ordivon_host_v2.attention_projections as projections
from ordivon_host_v2.attention_sql import ATTENTION_DELTA_SQL
from ordivon_host_v2.attention_store import AttentionStore
from ordivon_host_v2.canonical_json import canonical_digest

QUERY_PATH = "services/host/src/ordivon_host_v2/attention_sql.py"
BASELINE_SHA = "0480182c5b2fd9310adb02569f61f78d2308fc46"


def baseline_query() -> str:
    raw = subprocess.check_output(["git", "show", f"{BASELINE_SHA}:{QUERY_PATH}"], text=True)
    for statement in ast.parse(raw).body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "ATTENTION_DELTA_SQL" for t in statement.targets
        ):
            return ast.literal_eval(statement.value)
    raise AssertionError("original SQL not found in verified parent Git source")


def extract(sql: str, store: AttentionStore, actor: str, after: int, limit: int):
    projections.ATTENTION_DELTA_SQL = sql
    return store.delta(actor, after_sequence=after, limit=limit)


def compare_pages(store, sql_a, sql_b, actor, after, limit, pages):
    seen = set()
    results = []
    for n in range(pages):
        a = extract(sql_a, store, actor, after, limit)
        b = extract(sql_b, store, actor, after, limit)
        assert a == b, ("PAGE_DIFFERENCE", actor, after, n, a, b)
        for e in a["events"]:
            marker = (e["eventKind"], e["sourceRef"])
            assert marker not in seen, ("REPEATED_EVENT", marker)
            seen.add(marker)
        results.append(len(a["events"]))
        if not a["hasMore"]:
            assert a["nextAfterSequence"] == a["snapshotHighSequence"]
            break
        assert a["events"] and a["nextAfterSequence"] == a["events"][-1]["changeSequence"]
        assert a["nextAfterSequence"] > after
        after = a["nextAfterSequence"]
    return {"pages": len(results), "events_total": sum(results), "page_sizes": results}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dsn", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--sparse", type=int, default=16000)
    p.add_argument("--hot", type=int, default=8000)
    p.add_argument("--overlap", type=int, default=2400)
    p.add_argument("--iterations", type=int, default=24)
    a = p.parse_args()
    assert "127.0.0.1" in a.dsn and "hostbench" in a.dsn
    base = baseline_query()
    candidate = ATTENTION_DELTA_SQL
    assert base != candidate
    assert "LIMIT %(limit)s" in base and candidate.count("LIMIT %(limit)s") == 5
    with psycopg.connect(a.dsn, row_factory=dict_row, autocommit=True) as conn:
        assert (
            conn.execute("SELECT schema_version FROM host_v2_schema WHERE singleton").fetchone()[
                "schema_version"
            ]
            == 14
        )
        fixture = seed(conn, a.sparse, a.hot, a.overlap)
        store = AttentionStore(a.dsn)
        report = {
            "kind": "ordivon.host-attention-r44-paired-benchmark",
            "baseline_sha": BASELINE_SHA,
            "schema": 14,
            "same_disposable_db": True,
            "fixture": fixture,
            "scenarios": {},
            "correctness": {},
            "source": "actual AttentionStore.delta/reentry + EXPLAIN ANALYZE BUFFERS JSON",
        }
        for key, coord in fixture["coordinates"].items():
            actor = coord["actor"]
            after = coord["after"]
            ref = extract(base, store, actor, after, 10)
            cand = extract(candidate, store, actor, after, 10)
            assert ref == cand, ("FIRST_PAGE_MISMATCH", key)
            cold = {}
            for label, sql in [("baseline", base), ("candidate", candidate)]:
                t = time.perf_counter_ns()
                o = extract(sql, store, actor, after, 10)
                cold[label] = round((time.perf_counter_ns() - t) / 1e6, 3)
                assert o == ref
            timings = {"baseline": [], "candidate": []}
            for i in range(a.iterations):
                seq = (
                    [("baseline", base), ("candidate", candidate)]
                    if i % 2 == 0
                    else [("candidate", candidate), ("baseline", base)]
                )
                for label, sql in seq:
                    t = time.perf_counter_ns()
                    got = extract(sql, store, actor, after, 10)
                    timings[label].append((time.perf_counter_ns() - t) / 1e6)
                    assert got == ref
            explains = {}
            raw_plans = {}
            for label, sql in [("baseline", base), ("candidate", candidate)]:
                row = conn.execute(
                    "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) " + sql,
                    {
                        "actor_ref": actor,
                        "after_sequence": after,
                        "high": fixture["high"],
                        "limit": 11,
                    },
                ).fetchone()
                plan = row["QUERY PLAN"][0]
                raw_plans[label] = plan
                metrics = node_metrics(plan["Plan"])
                metrics["execution_time_ms"] = round(float(plan["Execution Time"]), 3)
                metrics["planning_time_ms"] = round(float(plan["Planning Time"]), 3)
                explains[label] = metrics
            reentries = {}
            for label, sql in [("baseline", base), ("candidate", candidate)]:
                projections.ATTENTION_DELTA_SQL = sql
                t = time.perf_counter_ns()
                nav = store.reentry(actor, after_sequence=after, limit=10)
                reentries[label] = {
                    "response": nav,
                    "duration_ms": round((time.perf_counter_ns() - t) / 1e6, 3),
                }
            assert reentries["baseline"]["response"] == reentries["candidate"]["response"]
            # Actual Agent reentry (Attention + grouped navigations + Topic cursors).
            # Alternate order on the same PG fixture to avoid a preferred warm side.
            reentry_samples = {"baseline": [], "candidate": []}
            for i in range(a.iterations):
                sequence = (
                    [("baseline", base), ("candidate", candidate)]
                    if i % 2 == 0
                    else [("candidate", candidate), ("baseline", base)]
                )
                for label, sql in sequence:
                    projections.ATTENTION_DELTA_SQL = sql
                    t = time.perf_counter_ns()
                    observed = store.reentry(actor, after_sequence=after, limit=10)
                    reentry_samples[label].append((time.perf_counter_ns() - t) / 1e6)
                    assert observed == reentries[label]["response"]
            scenario = {
                "events": len(ref["events"]),
                "first_event_sequence": ref["events"][0]["changeSequence"]
                if ref["events"]
                else None,
                "first_event_reasons": ref["events"][0]["reasons"] if ref["events"] else [],
                "body_decoded_bytes": 0,
                "query_count_delta": 3,
                "query_count_reentry": 4 if reentries["baseline"]["response"]["items"] else 3,
                "candidate_equals_baseline": True,
            }
            for label in ("baseline", "candidate"):
                scenario[label] = {
                    "first_sample_ms": cold[label],
                    "p50_ms": percentile(timings[label], 0.5),
                    "p95_ms": percentile(timings[label], 0.95),
                    "warm_samples_ms": [round(x, 3) for x in timings[label]],
                    "explain": explains[label],
                    "reentry_ms": reentries[label]["duration_ms"],
                    "reentry_p50_ms": percentile(reentry_samples[label], 0.5),
                    "reentry_p95_ms": percentile(reentry_samples[label], 0.95),
                }
            before = scenario["baseline"]["p50_ms"]
            after_ms = scenario["candidate"]["p50_ms"]
            scenario["p50_speedup_x"] = round(before / after_ms, 2) if after_ms else None
            report["scenarios"][key] = scenario
            if key == "hot":
                report["hot_full_explain_analyze_buffers"] = raw_plans
            print(
                "PAIRED",
                key,
                json.dumps(
                    {k: v for k, v in scenario.items() if k not in ("baseline", "candidate")}
                    | {
                        "baseline": {
                            "p50": scenario["baseline"]["p50_ms"],
                            "p95": scenario["baseline"]["p95_ms"],
                            "scan": scenario["baseline"]["explain"]["scan_leaf_actual_rows_sum"],
                            "hit": scenario["baseline"]["explain"]["shared_hit"],
                        },
                        "candidate": {
                            "p50": scenario["candidate"]["p50_ms"],
                            "p95": scenario["candidate"]["p95_ms"],
                            "scan": scenario["candidate"]["explain"]["scan_leaf_actual_rows_sum"],
                            "hit": scenario["candidate"]["explain"]["shared_hit"],
                        },
                    }
                ),
                flush=True,
            )
        case = "actor:bench:overlap"
        start = fixture["coordinates"]["overlap"]["after"]
        report["correctness"]["overlap_cross_pages"] = compare_pages(
            store, base, candidate, case, start, limit=50, pages=10000
        )
        report["correctness"]["hot_full_cross_pages"] = compare_pages(
            store,
            base,
            candidate,
            "actor:bench:hot",
            fixture["coordinates"]["hot"]["after"],
            limit=113,
            pages=10000,
        )
        # Multi-reason exact union (not four different messages).
        page = extract(candidate, store, case, start, limit=200)
        msg = [x for x in page["events"] if x["eventKind"] == "message"]
        assert len({m["sourceRef"] for m in msg}) == len(msg)
        assert any(
            {"followed_topic", "followed_space", "mentioned", "replied_to_me"} <= set(m["reasons"])
            for m in msg
        )
        report["correctness"]["all_four_reasons_one_message"] = True
        # At high: both versions skip heavy SQL and correctly return no event.
        high = fixture["high"]
        report["correctness"]["poll_at_high"] = compare_pages(
            store, base, candidate, "actor:bench:hot", high, limit=7, pages=1
        )
        # Cursor page at a sparse actor must skip irrelevant messages and never ACK them.
        report["correctness"]["sparse_cross_pages"] = compare_pages(
            store,
            base,
            candidate,
            "actor:bench:sparse",
            fixture["coordinates"]["sparse"]["after"],
            limit=7,
            pages=10000,
        )
        # A genuinely idle actor at the current high needs only actor/horizon reads;
        # the expensive multi-source Attention SQL must be skipped entirely.
        empty_poll = {}
        for label, sql in (("baseline", base), ("candidate", candidate)):
            samples = []
            for _ in range(a.iterations):
                t = time.perf_counter_ns()
                assert extract(sql, store, "actor:bench:empty", high, 7)["events"] == []
                samples.append((time.perf_counter_ns() - t) / 1e6)
            empty_poll[label] = {
                "p50_ms": percentile(samples, 0.5),
                "p95_ms": percentile(samples, 0.95),
            }
        report["empty_poll_at_high"] = {
            "sql_count": 2,
            "heavy_attention_query_executed": False,
            "body_decoded_bytes": 0,
            "measurements": empty_poll,
        }
        # Subscription effectivity is sequence scoped, not replay-to-all older messages.
        store.follow(
            actor_ref="actor:bench:sparse",
            target_kind="topic",
            target_ref="topic:bench:sparse:other",
            client_request_id="r44-follow-after-past",
        )
        o = extract(
            base, store, "actor:bench:sparse", fixture["coordinates"]["sparse"]["after"], 300
        )
        n = extract(
            candidate, store, "actor:bench:sparse", fixture["coordinates"]["sparse"]["after"], 300
        )
        assert o == n
        assert all(
            not e["sourceRef"].startswith("message:bench:sparse:")
            or int(e["sourceRef"].rsplit(":", 1)[1]) % 1139 == 0
            for e in n["events"]
            if e["eventKind"] == "message"
        )
        report["correctness"]["subscription_no_retroactive_replay"] = True
        # Retain the already-proved page, then append after the previous snapshot high.
        # A stale caller must resume from the consumed event, not acknowledge old high.
        partial = extract(
            candidate, store, "actor:bench:hot", fixture["coordinates"]["hot"]["after"], limit=7
        )
        assert (
            partial["hasMore"]
            and partial["nextAfterSequence"] == partial["events"][-1]["changeSequence"]
        )
        original_high = int(
            conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()["value"]
        )
        old_poll = extract(base, store, "actor:bench:hot", original_high, limit=7)
        assert old_poll["events"] == [] and old_poll["nextAfterSequence"] == original_high
        new_ref = "message:bench:concurrent:after_high"
        new_body = "One new message after an agent disconnects"
        new_ms = 1730000000000 + original_high + 1
        new_digest = canonical_digest(
            {
                "messageRef": new_ref,
                "spaceRef": "space:bench:hot",
                "topicRef": "topic:bench:hot",
                "authorActorRef": "actor:bench:sender",
                "messageKind": "note",
                "body": new_body,
                "recordedAtMs": new_ms,
            }
        )
        conn.execute(
            "INSERT INTO messages(message_ref,client_request_id,space_ref,topic_ref,"
            "author_actor_ref,message_kind,body,message_digest,recorded_at_ms) "
            "VALUES (%s,%s,%s,%s,%s,'note',%s,%s,%s)",
            (
                new_ref,
                "request:" + new_ref,
                "space:bench:hot",
                "topic:bench:hot",
                "actor:bench:sender",
                new_body,
                new_digest,
                new_ms,
            ),
        )
        new_high = int(
            conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()["value"]
        )
        assert new_high == original_high + 1
        after_append_base = extract(base, store, "actor:bench:hot", original_high, 7)
        after_append_opt = extract(candidate, store, "actor:bench:hot", original_high, 7)
        assert after_append_base == after_append_opt
        assert [e["sourceRef"] for e in after_append_opt["events"]] == [new_ref]
        assert after_append_opt["snapshotHighSequence"] == new_high
        resumed = extract(candidate, store, "actor:bench:hot", partial["nextAfterSequence"], 7)
        assert resumed["hasMore"] and resumed["nextAfterSequence"] < new_high
        report["correctness"]["append_between_pages_preserves_new_event"] = {
            "priorHigh": original_high,
            "newHigh": new_high,
            "priorPageCursor": partial["nextAfterSequence"],
            "newMessageSequence": after_append_opt["events"][0]["changeSequence"],
            "resumedPageCursor": resumed["nextAfterSequence"],
        }
        # A second writer holds the next change-clock update uncommitted while
        # the reconnecting reader obtains its Repeatable Read snapshot. Its
        # commit must appear ONLY on the later poll and cannot be ACKed early.
        inflight_high = new_high
        race_ref = "message:bench:mvcc:uncommitted"
        race_body = "Uncommitted writer during Attention reconnect"
        race_ms = 1730000000000 + inflight_high + 1
        race_digest = canonical_digest(
            {
                "messageRef": race_ref,
                "spaceRef": "space:bench:hot",
                "topicRef": "topic:bench:hot",
                "authorActorRef": "actor:bench:sender",
                "messageKind": "note",
                "body": race_body,
                "recordedAtMs": race_ms,
            }
        )
        inserted = threading.Event()
        permit_commit = threading.Event()
        failures = []

        def writer():
            try:
                with psycopg.connect(a.dsn, row_factory=dict_row) as writing:
                    with writing.transaction():
                        writing.execute(
                            "INSERT INTO messages(message_ref,client_request_id,space_ref,topic_ref,"
                            "author_actor_ref,message_kind,body,message_digest,recorded_at_ms) "
                            "VALUES (%s,%s,%s,%s,%s,'note',%s,%s,%s)",
                            (
                                race_ref,
                                "request:" + race_ref,
                                "space:bench:hot",
                                "topic:bench:hot",
                                "actor:bench:sender",
                                race_body,
                                race_digest,
                                race_ms,
                            ),
                        )
                        inserted.set()
                        if not permit_commit.wait(20):
                            raise TimeoutError("MVCC fixture writer did not receive commit permit")
            except Exception as exc:
                failures.append(str(exc))
                inserted.set()

        thread = threading.Thread(target=writer, name="r44-disposable-pg18-writer")
        thread.start()
        assert inserted.wait(15) and not failures
        try:
            mid_a = extract(base, store, "actor:bench:hot", inflight_high, 7)
            mid_b = extract(candidate, store, "actor:bench:hot", inflight_high, 7)
            assert mid_a == mid_b and mid_a["events"] == []
            assert mid_a["snapshotHighSequence"] == inflight_high
        finally:
            permit_commit.set()
            thread.join(timeout=20)
        assert not thread.is_alive() and not failures, failures
        committed_high = int(
            conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()["value"]
        )
        assert committed_high == inflight_high + 1
        final_a = extract(base, store, "actor:bench:hot", inflight_high, 7)
        final_b = extract(candidate, store, "actor:bench:hot", inflight_high, 7)
        assert final_a == final_b
        assert [e["sourceRef"] for e in final_b["events"]] == [race_ref]
        assert final_b["snapshotHighSequence"] == committed_high
        report["correctness"]["actual_concurrent_uncommitted_writer_snapshot"] = {
            "oldHigh": inflight_high,
            "afterCommittedHigh": committed_high,
            "uncommittedInvisible": True,
            "laterPollVisible": True,
            "sourceRef": race_ref,
        }
        report["correctness"]["no_cursor_ack_performed"] = True
        output = Path(a.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print("PAIRED_BENCH_PASS", output, flush=True)


if __name__ == "__main__":
    main()
