"""KnowledgeFeedbackPacket no-ORM-write structural invariant tests."""

import json

from knowledge.feedback import KnowledgeFeedbackPacket


def test_feedback_packet_is_self_contained():
    """KnowledgeFeedbackPacket has no ORM/db/session/repository attributes."""
    packet = KnowledgeFeedbackPacket(
        recommendation_id="reco-1",
        knowledge_entry_ids=("ke-1", "ke-2"),
    )

    assert not hasattr(packet, "db")
    assert not hasattr(packet, "session")
    assert not hasattr(packet, "repository")
    assert not hasattr(packet, "orm")


def test_feedback_packet_to_payload_has_no_db_references():
    """to_payload() serialized to JSON contains no ORM references."""
    packet = KnowledgeFeedbackPacket(
        recommendation_id="reco-1",
        knowledge_entry_ids=("ke-1", "ke-2"),
    )
    payload = packet.to_payload()
    serialized = json.dumps(payload)

    assert "sqlalchemy" not in serialized
    assert "Session" not in serialized
    assert "engine" not in serialized
