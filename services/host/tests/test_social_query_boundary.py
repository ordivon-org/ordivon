"""Host Social queries retain exactly one natural PostgreSQL write authority."""

import ast
from pathlib import Path

from ordivon_host_v2.social_queries import SocialReadQueries
from ordivon_host_v2.social_store import SocialStore


def test_social_queries_are_inherited_not_reimplemented_in_the_write_owner() -> None:
    queries = {
        "list_message_relations",
        "get_space",
        "list_space_subjects",
        "list_participations",
        "list_topics",
        "list_spaces",
        "_verify_message_content_digest",
        "get_message",
        "search_messages",
        "resume_topic",
        "get_topic_cursor",
        "_get_space_in_tx",
        "_require_message",
    }
    assert issubclass(SocialStore, SocialReadQueries)
    assert all(name in SocialReadQueries.__dict__ for name in queries)
    assert all(name not in SocialStore.__dict__ for name in queries)


def test_social_query_facet_cannot_own_insert_or_mutation_commands() -> None:
    src = Path(__file__).parents[1] / "src" / "ordivon_host_v2" / "social_queries.py"
    tree = ast.parse(src.read_text())
    source = src.read_text().lower()
    assert "claim_command_receipt" not in source
    assert "record_command_receipt" not in source
    query_literals = " ".join(
        str(n.value).lower()
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    )
    for term in ("insert into ", "update spaces ", "delete from ", "on conflict "):
        assert term not in query_literals
