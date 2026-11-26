"""Disposable-PG18 Attention benchmark fixture and EXPLAIN metrics.

Synthetic, isolated schema14 fixtures, never production rows or credentials.
"""

from __future__ import annotations

from ordivon_host_v2.canonical_json import canonical_digest


def percentile(values: list[float], q: float) -> float:
    s = sorted(values)
    return round(s[min(len(s) - 1, max(0, int((len(s) - 1) * q + 0.999999)))], 3)


def node_metrics(plan: dict) -> dict:
    leaves = []
    all_nodes = []

    def visit(n: dict):
        all_nodes.append(n)
        if not n.get("Plans"):
            leaves.append(n)
        for ch in n.get("Plans", []):
            visit(ch)

    visit(plan)
    return {
        "scan_leaf_actual_rows_sum": int(
            sum(n.get("Actual Rows", 0) * n.get("Actual Loops", 1) for n in leaves)
        ),
        "rows_removed_filter_all_nodes": int(
            sum(
                (n.get("Rows Removed by Filter", 0) + n.get("Rows Removed by Index Recheck", 0))
                * n.get("Actual Loops", 1)
                for n in all_nodes
            )
        ),
        "shared_hit": int(plan.get("Shared Hit Blocks", 0)),
        "shared_read": int(plan.get("Shared Read Blocks", 0)),
        "shared_dirtied": int(plan.get("Shared Dirtied Blocks", 0)),
        "shared_written": int(plan.get("Shared Written Blocks", 0)),
        "execution_ms": round(float(plan.get("Actual Total Time", 0)), 3),
        "top_rows": int(plan.get("Actual Rows", 0)),
        "indexes_used": sorted({n["Index Name"] for n in all_nodes if n.get("Index Name")}),
        "node_types": {
            n["Node Type"]: sum(1 for x in all_nodes if x["Node Type"] == n["Node Type"])
            for n in all_nodes
        },
    }


def copy_messages(conn, docs: list[tuple]) -> None:
    with conn.cursor().copy(
        "COPY messages (message_ref,client_request_id,space_ref,topic_ref,author_actor_ref,message_kind,body,message_digest,recorded_at_ms,change_sequence) FROM STDIN"
    ) as cp:
        for m in docs:
            cp.write_row(m)


def seed(conn, sparse: int, hot: int, overlap: int) -> dict:
    actors = [
        "actor:bench:sparse",
        "actor:bench:hot",
        "actor:bench:overlap",
        "actor:bench:empty",
        "actor:bench:sender",
    ]
    for actor in actors:
        conn.execute("INSERT INTO actor_refs(actor_ref,actor_kind) VALUES (%s,'agent')", (actor,))
    spaces = [
        ("sparse", "space:bench:sparse"),
        ("hot", "space:bench:hot"),
        ("overlap", "space:bench:overlap"),
    ]
    for short, space in spaces:
        conn.execute(
            "INSERT INTO spaces(space_ref,purpose,created_by_actor_ref) VALUES (%s,'attention latency benchmark','actor:bench:sender')",
            (space,),
        )
    topics = [
        ("topic:bench:sparse:follow", "space:bench:sparse"),
        ("topic:bench:sparse:other", "space:bench:sparse"),
        ("topic:bench:hot", "space:bench:hot"),
        ("topic:bench:overlap", "space:bench:overlap"),
    ]
    for t, s in topics:
        conn.execute(
            "INSERT INTO topics(topic_ref,space_ref,title,state,created_by_actor_ref) VALUES (%s,%s,%s,'open','actor:bench:sender')",
            (t, s, t),
        )
    subs = [
        ("actor:bench:sparse", "topic", "topic:bench:sparse:follow"),
        ("actor:bench:hot", "topic", "topic:bench:hot"),
        ("actor:bench:overlap", "topic", "topic:bench:overlap"),
        ("actor:bench:overlap", "space", "space:bench:overlap"),
    ]
    for s in subs:
        conn.execute(
            "INSERT INTO subscriptions(actor_ref,target_kind,target_ref) VALUES (%s,%s,%s)", s
        )
    base = int(
        conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()["value"]
    )
    rows = []
    coords = {}
    num = base + 100
    body = "Latency synthetic text " + ("alpha beta gamma " * 18)

    def append(name: str, space: str, topic: str, author: str, kind: str = "note"):
        nonlocal num
        num += 1
        ref = f"message:bench:{name}"
        ms = 1730000000000 + num
        digest = canonical_digest(
            {
                "messageRef": ref,
                "spaceRef": space,
                "topicRef": topic,
                "authorActorRef": author,
                "messageKind": kind,
                "body": body,
                "recordedAtMs": ms,
            }
        )
        rows.append((ref, "request:" + ref, space, topic, author, kind, body, digest, ms, num))
        return (ref, num)

    # Parent authored by the subscribed actor, before later reply messages.
    parent = append("parent", "space:bench:overlap", "topic:bench:overlap", "actor:bench:overlap")[
        0
    ]
    for i in range(sparse):
        append(
            f"sparse:{i}",
            "space:bench:sparse",
            "topic:bench:sparse:follow" if i % 1139 == 0 else "topic:bench:sparse:other",
            "actor:bench:sender",
        )
    coords["sparse"] = {"actor": "actor:bench:sparse", "after": base + 100, "size": sparse}
    for i in range(hot):
        append(f"hot:{i}", "space:bench:hot", "topic:bench:hot", "actor:bench:sender")
    coords["hot"] = {"actor": "actor:bench:hot", "after": base + 100 + sparse + 1, "size": hot}
    overlap_msgs = []
    for i in range(overlap):
        ref, seq = append(
            f"overlap:{i}", "space:bench:overlap", "topic:bench:overlap", "actor:bench:sender"
        )
        if i % 3 == 0:
            overlap_msgs.append(ref)
    coords["overlap"] = {
        "actor": "actor:bench:overlap",
        "after": base + 100 + sparse + hot + 1,
        "size": overlap,
    }
    with conn.transaction():
        copy_messages(conn, rows)
        relations = []
        for ref in overlap_msgs:
            num += 1
            relations.append((ref, "mentions", "actor:bench:overlap", "actor:bench:sender", num))
            num += 1
            relations.append((ref, "reply_to", parent, "actor:bench:sender", num))
        with conn.cursor().copy(
            "COPY message_relations(source_message_ref,relation,target_ref,created_by_actor_ref,change_sequence) FROM STDIN"
        ) as cp:
            for rel in relations:
                cp.write_row(rel)
        conn.execute("UPDATE swf_change_clock SET value=%s WHERE singleton", (num,))
    conn.execute("ANALYZE")
    conn.commit()
    coords["empty"] = {"actor": "actor:bench:empty", "after": base + 100, "size": 0}
    return {
        "coordinates": coords,
        "high": num,
        "total_messages": len(rows),
        "total_relations": len(relations),
        "body_bytes_per_message": len(body.encode()),
        "initial_high": base,
    }
