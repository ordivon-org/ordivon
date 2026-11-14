"""Cross-language replay of Rust-created Space/Topic through original Python Host.

Requires disposable PG18 schema13. The Rust Social PG tests have already
committed the fixtures before this script executes. Does not touch prod.
"""

from __future__ import annotations

import os
from datetime import datetime

import psycopg
from pydantic import ValidationError

from ordivon_host_v2.collaboration_inputs import (
    ParticipationStanding,
    SpaceInput,
    TopicInput,
)
from ordivon_host_v2.social_store import SocialStore

dsn = os.environ["HOST_RUST_TEST_DSN"]
assert dsn == os.environ["ORDIVON_HOST_V2_DSN"], "refuse mismatched PG credentials"
assert "127.0.0.1:" in dsn or "localhost:" in dsn, "disposable loopback DB only"

store = SocialStore(dsn)
actor = "actor:host-rust-b:space-create-r3"
space_ref = "space:host-rust-b:space-create-r3"
request = "request:host-rust-b:space-create-r3"
space = SpaceInput(
    space_ref=space_ref,
    purpose="Rust 领域创建 Space 🧩",
    actor_ref=actor,
    subject_refs=["topic:引用", "work:backlink"],
)
space_replay = store.create_space(space, client_request_id=request)
assert space_replay["admission"] == "existing", space_replay
assert space_replay["subjectRefs"] == ["topic:引用", "work:backlink"]
assert space_replay["createdAt"].endswith("+08:00"), space_replay

fresh_space = store.get_space(space_ref)
assert fresh_space["subjectCount"] == 2
assert fresh_space["subjectRefs"] == space_replay["subjectRefs"]
assert datetime.fromisoformat(fresh_space["createdAt"]) == datetime.fromisoformat(
    space_replay["createdAt"]
)

new_topic = TopicInput(
    topic_ref="topic:host-rust-b:native-r3-new",
    space_ref="space:host-rust-b:native-topic-create-r3",
    title="Native Rust discussion 🧩",
    actor_ref="actor:host-rust-b:native-topic-create-r3",
)
topic_replay = store.create_topic(
    new_topic, client_request_id="request:host-rust-b:r3-topic-create"
)
assert topic_replay["admission"] == "existing", topic_replay
assert topic_replay["topicRef"] == new_topic.topic_ref
assert topic_replay["createdAt"].endswith("+08:00"), topic_replay

with psycopg.connect(dsn) as conn:
    before = conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()[0]
    before_row = conn.execute(
        "SELECT standing,updated_at,change_sequence FROM participations "
        "WHERE space_ref=%s AND actor_ref=%s",
        ("space:host-rust-b:native-topic-create-r3", "actor:host-rust-b:native-topic-create-r3"),
    ).fetchone()
joining = store.set_participation(
    space_ref="space:host-rust-b:native-topic-create-r3",
    actor_ref="actor:host-rust-b:native-topic-create-r3",
    standing=ParticipationStanding.JOINED,
    client_request_id="same-identity",
)
assert joining["standing"] == "joined"
with psycopg.connect(dsn) as conn:
    after = conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone()[0]
    after_row = conn.execute(
        "SELECT standing,updated_at,change_sequence FROM participations "
        "WHERE space_ref=%s AND actor_ref=%s",
        ("space:host-rust-b:native-topic-create-r3", "actor:host-rust-b:native-topic-create-r3"),
    ).fetchone()
assert after_row == before_row, (before_row, after_row)
# Schema13 computes the change-clock DEFAULT even if ON CONFLICT's WHERE
# suppresses the physical UPDATE. This does not add a new changed owner row
# but advances the global horizon (a real pre-existing Python/PG design cost).
assert after >= before
print(f"B_PG_DESIRED_STATE_NOOP_CLOCK_HORIZON_ADVANCE={after - before}")

try:
    SpaceInput(
        space_ref="space:bad\u001c",
        purpose="purpose",
        actor_ref=actor,
    )
except ValidationError:
    pass
else:
    raise AssertionError("Python SpaceInput must reject U+001C trailing whitespace")

print(
    "B_PYTHON_READ_RUST_SOCIAL_PASS"
    " space_receipt=EXACT topic_receipt=EXACT"
    " space_timestamp=INSTANT_EQUIVALENT"
    " participation_owner_row=UNCHANGED"
    " whitespace=PYTHON_REFERENCE"
)
