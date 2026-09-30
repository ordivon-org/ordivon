from pathlib import Path

ROOT = Path(__file__).parents[1]
STORE = ROOT / "src" / "ordivon_host_v2" / "social_store.py"


def test_social_store_does_not_use_participation_as_authorization() -> None:
    text = STORE.read_text()
    post = text.split("    def post_message", 1)[1].split("    def add_message_relation", 1)[0]
    assert "participations" not in post
    assert "authorization" in post


def test_reply_relation_is_same_topic_only() -> None:
    text = STORE.read_text()
    validation = text.split("    def _validate_relation_target", 1)[1]
    assert "reply_to cannot cross topics" in validation
    assert "cannot cross spaces" in validation


def test_mentions_require_actor_but_references_can_be_opaque() -> None:
    text = STORE.read_text()
    validation = text.split("    def _validate_relation_target", 1)[1]
    assert "MessageRelationKind.MENTIONS" in validation
    assert "self._require_actor(conn, value.target_ref)" in validation
    assert "references/about intentionally accept opaque external refs" in validation


def test_coordination_intent_never_becomes_lock_or_assignment() -> None:
    text = STORE.read_text().lower()
    result_boundary = "coordination intent only; not assignment, reservation, lock, lease, scheduler decision, or effectauthority"
    assert result_boundary in text
    sql_lines = [
        line.lower()
        for line in text.splitlines()
        if "select " in line.lower() or "insert " in line.lower() or "update " in line.lower()
    ]
    sql = "\n".join(sql_lines)
    for forbidden in ("lock_owner", "lease_owner", "assignee", "priority", "winner"):
        assert forbidden not in sql


def test_released_intent_cannot_be_resurrected() -> None:
    text = STORE.read_text()
    assert "released coordination intent cannot be resurrected" in text


def test_topic_resume_is_bounded_and_cursor_based() -> None:
    text = STORE.read_text()
    resume = text.split("    def resume_topic", 1)[1].split("    def _get_space_in_tx", 1)[0]
    assert "after_sequence" in resume
    assert "limit + 1" in resume
    assert '"hasMore"' in resume
    assert '"nextAfterSequence"' in resume
