"""Historical reply rank is audited without changing the normal integrity contract."""

from __future__ import annotations

import os
import unittest
from uuid import uuid4

import psycopg

from ordivon_host_v2.collaboration_inputs import (
    MessageInput,
    MessageRelationInput,
    MessageRelationKind,
    SpaceInput,
    TopicInput,
)
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.service import HostV2
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")


@unittest.skipUnless(DSN, "requires disposable Host PostgreSQL test DSN")
class HistoryReplyRankTest(unittest.TestCase):
    def test_retained_rank_violation_is_history_only_and_read_only(self) -> None:
        assert DSN is not None
        HostV2(DSN).initialize()
        token = uuid4().hex
        prefix = f"history-rank:{token}"
        actor = f"actor:agent:{prefix}"
        space = f"space:{prefix}"
        topic = f"topic:{prefix}"
        earlier, later = f"message:{prefix}:1", f"message:{prefix}:2"
        social = SocialStore(DSN)
        ActorReferenceStore(DSN).declare_actor(
            ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
            client_request_id=f"{prefix}:actor",
        )
        try:
            status = HostV2(DSN)
            baseline = status.status(detail="history")["doctor"]
            baseline_check = {x["name"]: x for x in baseline["checks"]}["social.reply_history_rank"]
            baseline_invalid = int(baseline_check["detail"].removeprefix("invalid="))
            social.create_space(
                SpaceInput(space_ref=space, purpose="history rank test", actor_ref=actor),
                client_request_id=f"{prefix}:space",
            )
            social.create_topic(
                TopicInput(topic_ref=topic, space_ref=space, title="history rank", actor_ref=actor),
                client_request_id=f"{prefix}:topic",
            )
            for idx, ref in enumerate((earlier, later)):
                social.post_message(
                    MessageInput(
                        message_ref=ref,
                        client_request_id=f"{prefix}:message:{idx}",
                        space_ref=space,
                        topic_ref=topic,
                        author_actor_ref=actor,
                        body="synthetic",
                        recorded_at_ms=2 - idx,
                    )
                )
            for idx, (source, relation, target) in enumerate(
                (
                    (later, MessageRelationKind.REPLY_TO, earlier),
                    (earlier, MessageRelationKind.REFERENCES, later),
                    (later, MessageRelationKind.REFERENCES, earlier),
                )
            ):
                social.add_message_relation(
                    MessageRelationInput(
                        source_message_ref=source,
                        relation=relation,
                        target_ref=target,
                        actor_ref=actor,
                    ),
                    client_request_id=f"{prefix}:relation:{idx}",
                )
            valid = status.status(detail="history")["doctor"]
            self.assertEqual(
                {x["name"]: x for x in valid["checks"]}["social.reply_history_rank"],
                baseline_check,
            )
            before_regular = status.status(detail="integrity")["doctor"]
            # Simulate retained legacy edges, never write to the production DSN.
            with psycopg.connect(DSN) as conn:
                for source, target in ((earlier, earlier), (earlier, later)):
                    conn.execute(
                        "INSERT INTO message_relations"
                        "(source_message_ref,relation,target_ref,created_by_actor_ref) "
                        "VALUES (%s,'reply_to',%s,%s)",
                        (source, target, actor),
                    )
                before = conn.execute(
                    "SELECT count(*) FROM message_relations WHERE source_message_ref=ANY(%s)",
                    ([earlier, later],),
                ).fetchone()
            regular = HostV2(DSN).status(detail="integrity")["doctor"]
            history = HostV2(DSN).status(detail="history")["doctor"]
            assert regular is not None and history is not None
            self.assertEqual(regular["healthy"], before_regular["healthy"])
            self.assertEqual(
                {x["name"]: x["status"] for x in regular["checks"]},
                {x["name"]: x["status"] for x in before_regular["checks"]},
            )
            self.assertNotIn("social.reply_history_rank", {x["name"] for x in regular["checks"]})
            check = {x["name"]: x for x in history["checks"]}.get("social.reply_history_rank")
            self.assertEqual(
                check,
                {
                    "name": "social.reply_history_rank",
                    "status": "error",
                    "detail": f"invalid={baseline_invalid + 2}",
                },
            )
            self.assertFalse(history["healthy"])
            with psycopg.connect(DSN) as conn:
                after = conn.execute(
                    "SELECT count(*) FROM message_relations WHERE source_message_ref=ANY(%s)",
                    ([earlier, later],),
                ).fetchone()
            self.assertEqual(before, after)
        finally:
            with psycopg.connect(DSN) as conn:
                conn.execute(
                    "DELETE FROM message_relations WHERE source_message_ref=ANY(%s)",
                    ([earlier, later],),
                )
                conn.execute("DELETE FROM messages WHERE message_ref=ANY(%s)", ([earlier, later],))
                conn.execute("DELETE FROM topics WHERE topic_ref=%s", (topic,))
                conn.execute("DELETE FROM spaces WHERE space_ref=%s", (space,))
                conn.execute("DELETE FROM actor_refs WHERE actor_ref=%s", (actor,))
                conn.execute(
                    "DELETE FROM command_receipts WHERE client_request_id LIKE %s", (prefix + ":%",)
                )


if __name__ == "__main__":
    unittest.main()
