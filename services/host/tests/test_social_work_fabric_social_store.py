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



def test_causal_reply_pure_decision_covers_signed_bigint_edges() -> None:
    """The native Host consumer uses the same signed-order pure decision."""
    from ordivon_host_v2.social_store import _reply_target_precedes_source

    lower, upper = -(2**63), 2**63 - 1
    for src, dst, expected in (
        (2, 1, True),
        (1, 2, False),
        (1, 1, False),
        (upper, lower, True),
        (lower, upper, False),
        (lower, lower, False),
        (upper, upper, False),
    ):
        assert _reply_target_precedes_source(src, dst) is expected



def test_reply_symbolic_contract_is_bound_to_actual_host_consumer() -> None:
    """R2.1 goal is independently fixed, not controlled by the candidate's docstring."""
    import ast
    import inspect

    from ordivon_host_v2.social_store import _reply_target_precedes_source

    normative_post = {
        "post: __return__ == (target_sequence < source_sequence)",
        "post: __return__ == (not (target_sequence >= source_sequence))",
    }
    declared = {
        line.strip()
        for line in inspect.getdoc(_reply_target_precedes_source).splitlines()
        if line.strip().startswith("post:")
    }
    assert declared == normative_post

    source = ast.parse(STORE.read_text())
    owner = next(node for node in source.body if isinstance(node, ast.ClassDef) and node.name == "SocialStore")
    validator = next(
        node
        for node in owner.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_validate_relation_target"
    )
    guarded = [
        node
        for node in ast.walk(validator)
        if isinstance(node, ast.If)
        and "value.relation == MessageRelationKind.REPLY_TO" in ast.unparse(node.test)
        and "not _reply_target_precedes_source(source['sequence'], target['sequence'])"
        in ast.unparse(node.test)
        and any(
            isinstance(item, ast.Raise)
            and item.exc is not None
            and "reply_to must target an earlier message" in ast.unparse(item.exc)
            for item in node.body
        )
    ]
    assert len(guarded) == 1, "symbolically verified pure decision must gate Host relation writes"


def test_message_sequence_follows_same_topic_commit_visibility() -> None:
    """Guard a known PG identity-allocation versus commit-order cursor race.

    The topic row must be locked before allocating the message sequence.
    This is a source-level guard, not a live multi-transaction proof.
    """
    text = STORE.read_text()
    post = text.split('    def post_message', 1)[1].split('    def add_message_relation', 1)[0]
    assert 'self._require_topic(conn, value.topic_ref, for_no_key_update=True)' in post
    helper = text.split('    def _require_topic(', 1)[1].split('    def _require_message(', 1)[0]
    assert 'FOR NO KEY UPDATE' in helper
    # This lock mode does not conflict with FK KEY SHARE on topics.
    assert 'FOR UPDATE' not in helper


def test_two_writer_committed_prefix_interleaving_exhaustive() -> None:
    """Exhaustively check two writers with the real v8 global change clock.

    Identity allocation precedes the change-clock default. The singleton
    clock lock is held until transaction commit, but another writer can
    reach the clock first if the earlier identity allocator is descheduled.
    A topic lock BEFORE identity allocation rules out that schedule.
    Seven-event enumeration is an abstract model, not a production PG proof.
    """
    from itertools import permutations

    events = ("alloc1", "clock1", "commit1", "alloc2", "clock2", "commit2", "read")
    old_schedules = 0
    old_skipped = 0
    locked_schedules = 0

    for order in permutations(events):
        rank = {event: i for i, event in enumerate(order)}
        a1, k1, c1 = (rank[x] for x in ("alloc1", "clock1", "commit1"))
        a2, k2, c2 = (rank[x] for x in ("alloc2", "clock2", "commit2"))
        if not (a1 < k1 < c1 and a2 < k2 < c2 and a1 < a2):
            continue
        # swf_change_clock's UPDATE obtains one row lock until commit;
        # the second writer cannot enter the clock while the first holds it.
        if not (c1 < k2 or c2 < k1):
            continue
        old_schedules += 1
        skipped = c2 < rank["read"] < c1
        old_skipped += int(skipped)
        if c1 < a2:  # same-topic row lock held before allocating identity
            locked_schedules += 1
            assert not skipped

    assert old_schedules > 0
    assert old_skipped > 0  # Clock serialization alone does not prove safety.
    assert locked_schedules > 0
