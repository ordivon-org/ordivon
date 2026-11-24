"""The output qualifier is reusable without a Playwright or Windows transport."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = "https://chatgpt.com/c/12345678-1234-1234-1234-123456789abc"


def load_evidence():
    path = ROOT / "scripts" / "conversation_output_evidence.py"
    assert path.is_file(), "transport-independent output evidence must exist"
    spec = importlib.util.spec_from_file_location("conversation_output_evidence", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot():
    return {
        "url": RESOURCE,
        "messages": [
            {"role": "user", "text": "request", "visible": True},
            {"role": "assistant", "text": "answer", "visible": True},
        ],
        "generating": False,
        "fetchError": None,
        "challenge": False,
    }


def test_transport_independent_exact_output():
    m = load_evidence()
    value = m.qualify_snapshot(snapshot(), RESOURCE, "request", RESOURCE)
    assert value["standing"] == "CAPTURED"
    assert value["assistantOutput"] == "answer"
    assert value["assistantOutputRead"] is True


@pytest.mark.parametrize("change", [
    {"generating": True},
    {"fetchError": ""},
    {"challenge": True},
    {"messages": [{"role": "user", "text": "request", "visible": 1}]},
    {"messages": [{"role": "user", "text": "request", "visible": True},
                  {"role": "assistant", "text": "answer", "visible": False}]},
    {"messages": [{"role": "user", "text": "request", "visible": True},
                  {"role": "assistant", "text": "answer", "visible": True},
                  {"role": "user", "text": "request", "visible": False}]},
])
def test_unqualified_snapshot_never_delivers_bytes(change):
    m = load_evidence()
    value = m.qualify_snapshot({**snapshot(), **change}, RESOURCE, "request", RESOURCE)
    assert value["standing"] != "CAPTURED"
    assert value["assistantOutput"] is None
    assert value["assistantOutputDigest"] is None
    assert value["assistantOutputRead"] is False


def test_drift_and_missing_generation_evidence():
    m = load_evidence()
    data = snapshot()
    assert m.qualify_snapshot(data, RESOURCE, "request", "about:blank")["standing"] == "TARGET_RESOURCE_DRIFTED"
    del data["generating"]
    assert m.qualify_snapshot(data, RESOURCE, "request", RESOURCE)["standing"] == "OBSERVATION_INVALID"


def test_static_expression_has_no_effect_commands():
    m = load_evidence()
    expression = m.DOM_SNAPSHOT_EXPRESSION
    assert isinstance(expression, str)
    assert "location.href" in expression
    for fragment in ("fetch(", ".click(", "window.close(", "document.cookie", "localStorage"):
        assert fragment not in expression
    assert isinstance(json.dumps(m.DOM_SNAPSHOT_ARGS), str)


def test_digest_match_is_equivalent_to_exact_text_and_withholds_hidden_duplicates():
    m = load_evidence()
    exact = snapshot()
    digest = m.sha256_bytes(b"request")
    value = m.qualify_snapshot_by_digest(exact, RESOURCE, digest, RESOURCE)
    assert value == m.qualify_snapshot(exact, RESOURCE, "request", RESOURCE)
    exact["messages"].append({"role": "user", "text": "request", "visible": False})
    value = m.qualify_snapshot_by_digest(exact, RESOURCE, digest, RESOURCE)
    assert value["standing"] == "EXPECTED_USER_TURN_AMBIGUOUS"
    assert value["assistantOutput"] is None


def test_digest_matching_never_normalizes_provider_bytes_after_observation():
    m = load_evidence()
    exact = snapshot()
    exact["messages"][0]["text"] = "request\r\nline"
    digest = m.sha256_bytes(b"request\nline")
    value = m.qualify_snapshot_by_digest(exact, RESOURCE, digest, RESOURCE)
    assert value["standing"] == "EXPECTED_USER_TURN_NOT_VISIBLE"
    assert value["assistantOutput"] is None


def test_bad_or_empty_prompt_digest_is_not_valid_evidence():
    m = load_evidence()
    for value in ("sha256:bad", "", m.sha256_bytes(b"")):
        with pytest.raises(ValueError):
            m.qualify_snapshot_by_digest(snapshot(), RESOURCE, value, RESOURCE)


def repeated_history():
    before = snapshot()
    before["messages"][0]["messageId"] = "old-user"
    before["messages"][1]["messageId"] = "old-assistant"
    after = {**before, "messages": before["messages"] + [
        {"role": "user", "text": "request", "visible": True, "messageId": "new-user"},
        {"role": "assistant", "text": "new answer", "visible": True, "messageId": "new-assistant"},
    ]}
    return before, after


def test_same_prompt_old_history_is_not_new_turn():
    m = load_evidence()
    before, after = repeated_history()
    digest = m.sha256_bytes(b"request")
    # Without a causal witness the lone old occurrence looks like a role pair.
    assert m.qualify_snapshot_by_digest(before, RESOURCE, digest, RESOURCE)["standing"] == "CAPTURED"
    anchored = m.qualify_snapshot_by_digest(
        before, RESOURCE, digest, RESOURCE, expected_dom_user_message_id="new-user",
    )
    assert anchored["standing"] == "EXPECTED_USER_MESSAGE_ID_NOT_VISIBLE"
    assert anchored["assistantOutput"] is None
    assert m.qualify_snapshot_by_digest(after, RESOURCE, digest, RESOURCE)["standing"] == "EXPECTED_USER_TURN_AMBIGUOUS"
    result = m.qualify_snapshot_by_digest(
        after, RESOURCE, digest, RESOURCE, expected_dom_user_message_id="new-user",
    )
    assert result["standing"] == "CAPTURED"
    assert result["assistantOutput"] == "new answer"
    assert result["observedDomUserMessageId"] == "new-user"


def test_only_one_new_ordered_user_message_creates_append_witness():
    m = load_evidence()
    before, after = repeated_history()
    digest = m.sha256_bytes(b"request")
    witness = m.qualify_user_append_witness(before, after, RESOURCE, digest)
    assert witness["evidenceScope"] == "OBSERVED_DOM_APPEND_ONLY"
    assert witness["domUserMessageId"] == "new-user"
    assert witness["promptDigest"] == digest
    assert witness["previousUserCount"] == 1
    assert witness["observedUserCount"] == 2
    assert "new answer" not in str(witness)
    assert "old-user" not in str(witness)
    assert m.qualify_user_append_witness(before, before, RESOURCE, digest) is None


@pytest.mark.parametrize("change", ["missing-id", "duplicate-id", "history-edit", "history-drop",
                                    "two-appends", "wrong-prompt", "drift", "challenge", "hidden-user"])
def test_unqualified_append_has_no_witness(change):
    m = load_evidence()
    before, after = repeated_history()
    after = {**after, "messages": [dict(x) for x in after["messages"]]}
    if change == "missing-id":
        del after["messages"][2]["messageId"]
    elif change == "duplicate-id":
        after["messages"][2]["messageId"] = "old-user"
    elif change == "history-edit":
        after["messages"][0]["text"] = "edited"
    elif change == "history-drop":
        after["messages"] = after["messages"][2:]
    elif change == "two-appends":
        after["messages"].append({"role":"user","text":"another","visible":True,"messageId":"third-user"})
    elif change == "wrong-prompt":
        after["messages"][2]["text"] = "other"
    elif change == "drift":
        after["url"] = "https://chatgpt.com/c/different"
    elif change == "challenge":
        after["challenge"] = True
    elif change == "hidden-user":
        after["messages"][2]["visible"] = False
    assert m.qualify_user_append_witness(before, after, RESOURCE, m.sha256_bytes(b"request")) is None


@pytest.mark.parametrize("change", ["wrong-text", "hidden", "duplicate-id", "wrong-role"])
def test_anchored_message_conflict_never_returns_output(change):
    m = load_evidence()
    _, after = repeated_history()
    if change == "wrong-text":
        after["messages"][2]["text"] = "other"
    elif change == "hidden":
        after["messages"][2]["visible"] = False
    elif change == "duplicate-id":
        after["messages"][0]["messageId"] = "new-user"
    else:
        after["messages"][2]["role"] = "assistant"
    result = m.qualify_snapshot_by_digest(
        after, RESOURCE, m.sha256_bytes(b"request"), RESOURCE,
        expected_dom_user_message_id="new-user",
    )
    assert result["standing"] != "CAPTURED"
    assert result["assistantOutput"] is None
