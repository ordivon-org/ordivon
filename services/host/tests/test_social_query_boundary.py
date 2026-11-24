"""Host Social queries retain exactly one natural PostgreSQL write authority."""

import ast
from pathlib import Path

from ordivon_host_v2.social_store import SocialStore


def test_social_public_queries_use_one_explicit_message_record_helper() -> None:
    """The public SocialStore facade stays callable without a hidden Message MRO hook."""
    from ordivon_host_v2 import (
        social_message_commands,
        social_message_queries,
        social_topic_queries,
    )
    from ordivon_host_v2.social_message_records import (
        require_message,
        verify_message_content_digest,
    )

    public_queries = {
        "list_message_relations",
        "get_space",
        "list_space_subjects",
        "list_participations",
        "list_topics",
        "list_spaces",
        "get_message",
        "search_messages",
        "resume_topic",
        "get_topic_cursor",
    }
    assert all(callable(getattr(SocialStore, name)) for name in public_queries)
    assert (
        social_message_commands.verify_message_content_digest
        is social_message_queries.verify_message_content_digest
        is social_topic_queries.verify_message_content_digest
    )
    assert (
        social_message_commands.require_message
        is social_message_queries.require_message
        is require_message
    )
    assert not hasattr(SocialStore, "_verify_message_content_digest")
    assert not hasattr(SocialStore, "_require_message")
    assert callable(verify_message_content_digest)


def test_social_query_facet_cannot_own_insert_or_mutation_commands() -> None:
    source_dir = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    read_sources = [
        (source_dir / module).read_text()
        for module in (
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
