"""Read one exact turn without switching the daemon's shared browser session."""
from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

import pytest

RESOURCE = "https://chatgpt.com/c/12345678-1234-1234-1234-123456789abc"
OTHER = "https://chatgpt.com/c/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
PROMPT = "synthetic request"
PROMPT_DIGEST = "sha256:" + hashlib.sha256(PROMPT.encode()).hexdigest()


def reader():
    return importlib.import_module("scripts.existing_browser_harness_output")


def tab(target="target-1", url=RESOURCE):
    return {"type": "page", "targetId": target, "url": url}


class Transport:
    def __init__(self, *, before=None, after=None, snapshot=None, alive=True,
                 fail=None, bad_attach=False):
        self.before = [tab()] if before is None else before
        self.after = [tab()] if after is None else after
        self.snapshot = {
            "url": RESOURCE, "generating": False, "fetchError": None, "challenge": False,
            "messages": [
                {"role": "user", "text": "unrelated private input", "visible": True},
                {"role": "assistant", "text": "unrelated private answer", "visible": True},
                {"role": "user", "text": PROMPT, "visible": True},
                {"role": "assistant", "text": "synthetic answer", "visible": True},
            ],
        } if snapshot is None else snapshot
        self.alive = alive
        self.fail = fail
        self.bad_attach = bad_attach
        self.calls = []
        self.lists = 0

    def ping(self):
        self.calls.append(("ping", {}, None))
        return self.alive

    def call(self, method, params, session_id=None):
        self.calls.append((method, params, session_id))
        if self.fail == method:
            raise RuntimeError("private transport diagnostics must not escape")
        if method == "Target.getTargets":
            self.lists += 1
            return {"targetInfos": self.before if self.lists == 1 else self.after}
        if method == "Target.attachToTarget":
            assert params == {"targetId": "target-1", "flatten": True}
            return {} if self.bad_attach else {"sessionId": "exact-sid"}
        if method == "Runtime.evaluate":
            assert session_id == "exact-sid"
            assert params["returnByValue"] is True
            assert "document.cookie" not in params["expression"]
            return {"result": {"type": "object", "value": self.snapshot}}
        if method == "Target.detachFromTarget":
            assert params == {"sessionId": "exact-sid"}
            assert session_id is None
            return {}
        raise AssertionError(method)


def run(t, **kwargs):
    inputs = dict(target_resource=RESOURCE, expected_prompt=PROMPT,
                  expected_prompt_digest=PROMPT_DIGEST, observation_id="obs-1")
    inputs.update(kwargs)
    return reader().read_existing_turn(t, **inputs)


def test_exact_scoped_read_and_detach_no_other_content():
    t = Transport()
    result = run(t)
    assert result["standing"] == "CAPTURED"
    assert result["assistantOutput"] == "synthetic answer"
    assert result["assistantOutputDigest"] == "sha256:" + hashlib.sha256(b"synthetic answer").hexdigest()
    assert result["sessionDetached"] is True
    assert result["observationId"] == "obs-1"
    assert result["expectedPromptDigest"] == PROMPT_DIGEST
    assert result["targetId"] == "target-1"
    assert result["providerEffectAttempted"] is False
    assert result["releaseAttempted"] is False
    assert "unrelated private" not in str(result)
    assert [c[0] for c in t.calls] == [
        "ping", "Target.getTargets", "Target.attachToTarget", "Runtime.evaluate",
        "Target.getTargets", "Target.detachFromTarget",
    ]


@pytest.mark.parametrize("before,standing", [
    ([], "TARGET_NOT_VISIBLE"),
    ([tab(), tab("other")], "TARGET_AMBIGUOUS"),
    ([tab(url=OTHER)], "TARGET_NOT_VISIBLE"),
    ([{"type": "page", "url": RESOURCE}], "OBSERVATION_INVALID"),
])
def test_bad_target_selection_never_attaches(before, standing):
    t = Transport(before=before)
    result = run(t)
    assert result["standing"] == standing
    assert result["assistantOutput"] is None
    assert [c[0] for c in t.calls] == ["ping", "Target.getTargets"]


@pytest.mark.parametrize("after", [[], [tab("replacement")], [tab(), tab("other")], [tab(url=OTHER)]])
def test_target_set_drift_discards_already_read_bytes(after):
    t = Transport(after=after)
    result = run(t)
    assert result["standing"] == "TARGET_RESOURCE_DRIFTED"
    assert result["assistantOutput"] is None
    assert result["sessionDetached"] is True


def test_no_daemon_is_a_read_only_hold():
    t = Transport(alive=False)
    assert run(t)["standing"] == "DAEMON_UNAVAILABLE"
    assert t.calls == [("ping", {}, None)]


@pytest.mark.parametrize("fail,standing", [
    ("Target.attachToTarget", "SESSION_ATTACHMENT_UNKNOWN"),
    ("Runtime.evaluate", "TRANSPORT_ERROR"),
    ("Target.detachFromTarget", "SESSION_DETACH_UNCONFIRMED"),
])
def test_uncertain_transport_never_delivers_output(fail, standing):
    t = Transport(fail=fail)
    result = run(t)
    assert result["standing"] == standing
    assert result["assistantOutput"] is None
    assert result["assistantOutputDigest"] is None
    assert "private transport diagnostics" not in str(result)
    if fail == "Runtime.evaluate":
        assert t.calls[-1][0] == "Target.detachFromTarget"


def test_malformed_attach_is_unknown_not_retried():
    t = Transport(bad_attach=True)
    result = run(t)
    assert result["standing"] == "SESSION_ATTACHMENT_UNKNOWN"
    assert result["sessionDetached"] is None
    assert [c[0] for c in t.calls] == ["ping", "Target.getTargets", "Target.attachToTarget"]


@pytest.mark.parametrize("change,standing", [
    ({"generating": True}, "ASSISTANT_GENERATING"),
    ({"challenge": True}, "CHALLENGE_GATED"),
    ({"fetchError": "unrelated private server error"}, "CONVERSATION_FETCH_FAILED"),
    ({"url": OTHER}, "TARGET_RESOURCE_DRIFTED"),
])
def test_nonqualified_snapshot_does_not_leak_content(change, standing):
    base = Transport()
    t = Transport(snapshot={**base.snapshot, **change})
    result = run(t)
    assert result["standing"] == standing
    assert result["assistantOutput"] is None
    assert "unrelated private" not in str(result)
    assert result["sessionDetached"] is True


@pytest.mark.parametrize("kwargs", [
    {"expected_prompt_digest": "sha256:" + "a" * 64},
    {"expected_prompt": " "},
    {"target_resource": "https://example.test/"},
    {"observation_id": ""},
])
def test_invalid_input_no_transport(kwargs):
    t = Transport()
    with pytest.raises(ValueError):
        run(t, **kwargs)
    assert not t.calls


def test_remote_javascript_exception_withholds_data_and_detaches():
    class BadEvaluation(Transport):
        def call(self, method, params, session_id=None):
            value = super().call(method, params, session_id)
            if method == "Runtime.evaluate":
                return {**value, "exceptionDetails": {"text": "private error"}}
            return value

    t = BadEvaluation()
    value = run(t)
    assert value["standing"] == "OBSERVATION_INVALID"
    assert value["assistantOutput"] is None
    assert "private error" not in str(value)
    assert value["sessionDetached"] is True
    assert t.calls[-1][0] == "Target.detachFromTarget"


def test_incompatible_sdk_never_imports_or_connects(monkeypatch):
    m = reader()
    monkeypatch.setattr(m.importlib.metadata, "version", lambda _: "999.0")
    transport = m.ExistingDaemonTransport("approved")
    assert transport.ping() is False
    with pytest.raises(RuntimeError, match="unavailable"):
        transport.call("Target.getTargets", {})


def test_release_manifest_includes_transport():
    from scripts.agent_automation_release import RELEASE_PATHS
    assert "scripts/existing_browser_harness_output.py" in RELEASE_PATHS
    assert (Path(__file__).resolve().parents[1] / "scripts" / "existing_browser_harness_output.py").is_file()


def test_digest_only_reader_needs_no_prompt_or_temporal_payload():
    t = Transport()
    value = run(t, expected_prompt=None)
    assert value["standing"] == "CAPTURED"
    assert value["assistantOutput"] == "synthetic answer"
    assert value["expectedPromptDigest"] == PROMPT_DIGEST
    assert PROMPT not in str(t.calls)
    assert "unrelated private" not in str(value)


def test_digest_only_different_valid_digest_does_not_capture():
    t = Transport()
    value = run(t, expected_prompt=None,
                expected_prompt_digest="sha256:" + hashlib.sha256(b"other").hexdigest())
    assert value["standing"] == "EXPECTED_USER_TURN_NOT_VISIBLE"
    assert value["assistantOutput"] is None
