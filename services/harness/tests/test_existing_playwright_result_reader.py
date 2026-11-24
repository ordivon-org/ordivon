"""Reading an existing result must not navigate, create or close a page."""

from __future__ import annotations

import hashlib
from types import SimpleNamespace
from unittest.mock import Mock, PropertyMock

import pytest

import playwright_browserless_conversation_output as reader

RESOURCE = "https://chatgpt.com/c/12345678-1234-1234-1234-123456789abc"
DIGEST = "sha256:" + hashlib.sha256(b"same prompt").hexdigest()


def page(url=RESOURCE):
    p = Mock()
    p.url = url
    p.evaluate.return_value = {
        "url": RESOURCE,
        "messages": [
            {"role": "user", "text": "same prompt", "visible": True, "messageId": "old-user"},
            {"role": "assistant", "text": "old reply", "visible": True, "messageId": "old-answer"},
            {"role": "user", "text": "same prompt", "visible": True, "messageId": "new-user"},
            {"role": "assistant", "text": "new reply", "visible": True, "messageId": "new-answer"},
        ],
        "generating": False,
        "fetchError": None,
        "challenge": False,
    }
    return p


def read(browser, message="new-user"):
    return reader.read_existing_playwright_output(
        browser,
        target_resource=RESOURCE,
        expected_prompt_digest=DIGEST,
        expected_dom_user_message_id=message,
    )


def test_exact_existing_page_and_message_id_select_new_reply():
    target = page()
    unrelated = page("about:blank")
    context = SimpleNamespace(pages=[target, unrelated])
    b = SimpleNamespace(contexts=[context])
    result = read(b)
    assert result["standing"] == "CAPTURED"
    assert result["assistantOutput"] == "new reply"
    assert result["observedDomUserMessageId"] == "new-user"
    assert result["evidenceScope"] == "OBSERVED_DOM_MESSAGE_ID_MATCH"
    assert result["releaseAttempted"] is False
    assert [call[0] for call in target.method_calls] == ["evaluate"]
    assert unrelated.method_calls == []


@pytest.mark.parametrize(
    "pages,standing",
    [
        ([], "TARGET_NOT_VISIBLE"),
        ([page("about:blank")], "TARGET_NOT_VISIBLE"),
        ([page(), page()], "TARGET_AMBIGUOUS"),
    ],
)
def test_absent_or_duplicate_target_never_creates_or_navigates(pages, standing):
    ctx = Mock()
    ctx.pages = pages
    browser = SimpleNamespace(contexts=[ctx])
    result = read(browser)
    assert result["standing"] == standing
    assert result["assistantOutput"] is None
    assert result["assistantOutputDigest"] is None
    ctx.new_page.assert_not_called()
    for p in pages:
        assert p.method_calls == []


def test_target_cardinality_drift_withholds_captured_output():
    p = page()
    ctx = Mock()
    type(ctx).pages = PropertyMock(side_effect=[[p], [p, page()]])
    try:
        result = read(SimpleNamespace(contexts=[ctx]))
    finally:
        del type(ctx).pages
    assert result["standing"] == "TARGET_RESOURCE_DRIFTED"
    assert result["assistantOutput"] is None
    assert result["assistantOutputDigest"] is None
    assert result["observedDomUserMessageId"] is None


def test_missing_new_message_never_falls_back_to_old_same_text():
    p = page()
    p.evaluate.return_value["messages"] = p.evaluate.return_value["messages"][:2]
    result = read(SimpleNamespace(contexts=[SimpleNamespace(pages=[p])]))
    assert result["standing"] == "EXPECTED_USER_MESSAGE_ID_NOT_VISIBLE"
    assert result["assistantOutput"] is None


def test_transport_exception_does_not_return_private_diagnostics():
    p = page()
    p.evaluate.side_effect = RuntimeError("private synthetic content")
    result = read(SimpleNamespace(contexts=[SimpleNamespace(pages=[p])]))
    assert result["standing"] == "TRANSPORT_ERROR"
    assert "private synthetic content" not in str(result)
    assert result["assistantOutput"] is None


def test_multiple_contexts_do_not_select_arbitrarily():
    p = page()
    result = read(SimpleNamespace(contexts=[SimpleNamespace(pages=[p]), SimpleNamespace(pages=[])]))
    assert result["standing"] == "CONTEXT_AMBIGUOUS"
    assert p.method_calls == []


@pytest.mark.parametrize("raw", [b"same prompt", b"same prompt\n", b"same prompt\r\n"])
def test_prompt_file_transport_newline_preserves_original_contract(tmp_path, raw):
    path = tmp_path / "prompt.txt"
    path.write_bytes(raw)
    actual, file_digest = reader._prompt_file_digests(path)
    assert actual == DIGEST
    assert file_digest == "sha256:" + hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("raw", [b" same prompt", b"same prompt\n\n", b"", b"\xff"])
def test_prompt_file_rejects_noncanonical_or_unreadable_bytes(tmp_path, raw):
    path = tmp_path / "prompt.txt"
    path.write_bytes(raw)
    with pytest.raises((ValueError, UnicodeError)):
        reader._prompt_file_digests(path)


def test_result_does_not_disclose_raw_page_query_or_fetch_error():
    p = page(RESOURCE + "?private=synthetic-query")
    p.evaluate.return_value["url"] = p.url
    p.evaluate.return_value["fetchError"] = "synthetic-private-error"
    result = read(SimpleNamespace(contexts=[SimpleNamespace(pages=[p])]))
    assert result["standing"] == "CONVERSATION_FETCH_FAILED"
    assert result["pageUrlObserved"] == RESOURCE
    assert result["conversationFetchError"] == "OBSERVED"
    assert "synthetic-query" not in str(result)
    assert "synthetic-private-error" not in str(result)
