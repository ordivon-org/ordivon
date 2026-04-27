"""KnowledgeFeedbackPacket advisory-only structural invariant tests."""

import pytest

from knowledge.feedback import KnowledgeFeedbackPacket


def test_knowledge_feedback_packet_is_advisory_by_default():
    """is_advisory_only is hardcoded to True for all packets."""
    packet = KnowledgeFeedbackPacket(
        recommendation_id="reco-1",
        knowledge_entry_ids=("ke-1", "ke-2"),
    )
    assert packet.is_advisory_only is True


def test_knowledge_feedback_packet_serializes_advisory_flag():
    """to_payload() includes advisory_only=True and semantic_class."""
    packet = KnowledgeFeedbackPacket(
        recommendation_id="reco-1",
        knowledge_entry_ids=("ke-1",),
    )
    payload = packet.to_payload()

    assert payload["advisory_only"] is True
    assert payload["semantic_class"] == "derived_feedback_packet"


def test_knowledge_feedback_packet_requires_recommendation_id():
    """Empty recommendation_id raises ValueError on construction."""
    with pytest.raises(ValueError):
        KnowledgeFeedbackPacket(
            recommendation_id="",
            knowledge_entry_ids=("ke-1",),
        )
