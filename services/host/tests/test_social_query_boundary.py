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
    assert all(callable(getattr(SocialReadQueries, name)) for name in queries)
    assert all(name not in SocialStore.__dict__ for name in queries)
    from ordivon_host_v2.social_message_queries import SocialMessageReadQueries
    from ordivon_host_v2.social_space_queries import SocialSpaceReadQueries
    from ordivon_host_v2.social_topic_queries import SocialTopicReadQueries

    assert {name for name in queries if name in SocialSpaceReadQueries.__dict__} == {
        "get_space",
        "list_space_subjects",
        "list_participations",
        "list_spaces",
        "_get_space_in_tx",
    }
    assert {name for name in queries if name in SocialMessageReadQueries.__dict__} == {
        "list_message_relations",
        "_verify_message_content_digest",
        "get_message",
        "search_messages",
        "_require_message",
    }
    assert {name for name in queries if name in SocialTopicReadQueries.__dict__} == {
        "list_topics",
        "resume_topic",
        "get_topic_cursor",
    }


def test_social_query_facet_cannot_own_insert_or_mutation_commands() -> None:
    source_dir = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    read_sources = [
        (source_dir / module).read_text()
        for module in (
            "social_queries.py",
            "social_space_queries.py",
            "social_message_queries.py",
            "social_topic_queries.py",
        )
    ]
    combined = "\n".join(read_sources)
    tree = ast.parse(combined)
    assert "claim_command_receipt" not in combined.lower()
    assert "record_command_receipt" not in combined.lower()
    query_literals = " ".join(
        str(n.value).lower()
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    )
    for term in ("insert into ", "update spaces ", "delete from ", "on conflict "):
        assert term not in query_literals
