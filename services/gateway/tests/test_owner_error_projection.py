from __future__ import annotations

from ordivon_gateway.logic.owner_protocol import OwnerCallError
from ordivon_gateway.transport.owner_error_projection import owner_error_result


def _host_error(**overrides):
    data = {
        "kind": "ordivon.host-domain-error",
        "schemaVersion": 1,
        "code": "CONFLICT",
        "reason": "topic_resume_cursor_ahead",
        "retryable": False,
        "resourceKind": "topic",
        "requestedAfterSequence": 100000000,
        "observedTopicHighSequence": 30362,
        "suggestedAction": "reread-topic-horizon-and-check-cursor-domain",
        "evidenceBoundary": "same-transaction-topic-message-horizon",
        "detail": "PRIVATE_OWNER_DETAIL_DO_NOT_PROJECT",
    }
    data.update(overrides)
    return data


def test_host_typed_error_visible_without_raw_detail():
    payload = _host_error()
    exc = OwnerCallError(
        "owner tool returned error: host/topic.resume",
        owner_id="host",
        tool_name="topic.resume",
        error=payload,
    )
    result = owner_error_result(exc)
    message = result.content[0].text
    assert "reason=topic_resume_cursor_ahead" in message
    assert "observedTopicHighSequence=30362" in message
    assert "requestedAfterSequence=100000000" in message
    assert "PRIVATE_OWNER_DETAIL" not in message
    assert result.structured_content["error"] == payload
    assert result.is_error is True


def test_host_domain_unknown_string_is_not_exposed():
    exc = OwnerCallError(
        "safe generic",
        owner_id="host",
        tool_name="topic.resume",
        error=_host_error(reason="SECRET Value"),
    )
    message = owner_error_result(exc).content[0].text
    assert "SECRET" not in message
    assert message == "safe generic"


def test_unvalidated_upstream_does_not_gain_public_error_authority():
    exc = OwnerCallError(
        "safe generic",
        owner_id="runtime.linux",
        error=_host_error(reason="topic_resume_cursor_ahead"),
    )
    assert owner_error_result(exc).content[0].text == "safe generic"
    exc = OwnerCallError("safe generic", owner_id="host", error=_host_error(schemaVersion=True))
    assert owner_error_result(exc).content[0].text == "safe generic"
