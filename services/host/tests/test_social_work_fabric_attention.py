from pathlib import Path

ROOT = Path(__file__).parents[1]
ATTENTION = ROOT / "src" / "ordivon_host_v2" / "social_attention.py"
MIGRATION = ROOT / "migrations" / "versions" / "0008_social_work_fabric_attention.py"


def test_attention_uses_owner_rows_not_attention_event_bus() -> None:
    migration = MIGRATION.read_text().lower()
    source = ATTENTION.read_text().lower()
    assert "create table attention_events" not in migration
    assert "from work_snapshots" in source
    assert "from messages" in source
    assert "from coordination_intents" in source


def test_attention_is_actor_scoped_and_subscription_bounded() -> None:
    source = ATTENTION.read_text()
    sql = source.split("    def _delta_sql", 1)[1]
    assert "subscriptions" in sql
    assert "actor_ref=%(actor_ref)s" in sql
    assert "target_kind='work'" in sql
    assert "target_kind='space'" in sql
    assert "target_kind='topic'" in sql


def test_attention_mentions_and_replies_route_without_global_scan() -> None:
    sql = ATTENTION.read_text().split("    def _delta_sql", 1)[1]
    assert "mr.relation='mentions'" in sql
    assert "reply.relation='reply_to'" in sql
    assert "parent.author_actor_ref=%(actor_ref)s" in sql


def test_attention_cursor_is_monotonic_and_horizon_bounded() -> None:
    source = ATTENTION.read_text()
    assert "attention cursor cannot move backwards" in source
    assert "cannot acknowledge beyond current change horizon" in source
    assert "WHERE attention_cursors.cursor <= EXCLUDED.cursor" in source
    assert "RETURNING cursor" in source
    assert '"snapshotHighSequence"' in source


def test_attention_never_ranks() -> None:
    source = ATTENTION.read_text()
    assert '"rankingApplied": False' in source
    assert "ORDER BY change_sequence,event_kind,source_ref" in source
    assert "ORDER BY priority" not in source
    assert "ORDER BY score" not in source


def test_subscription_is_routing_preference_not_assignment() -> None:
    source = ATTENTION.read_text().lower()
    assert (
        "attention routing preference only; not assignment, priority, ownership, or authorization"
        in source
    )


def test_attention_change_clock_is_transactional_not_postgres_sequence() -> None:
    migration = MIGRATION.read_text().lower()
    source = ATTENTION.read_text().lower()
    assert "create sequence swf_change_sequence" not in migration
    assert "create table swf_change_clock" in migration
    assert "create function swf_next_change_sequence" in migration
    assert "update swf_change_clock" in migration
    assert "select value from swf_change_clock where singleton" in source


def test_subscription_horizon_does_not_replay_pre_follow_history() -> None:
    sql = ATTENTION.read_text().split("    def _delta_sql", 1)[1]
    assert sql.count("change_sequence > s.change_sequence") >= 6
