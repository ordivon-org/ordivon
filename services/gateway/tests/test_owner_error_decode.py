"""Negative and positive typed Owner ToolError boundary evidence."""

from __future__ import annotations

import itertools
import json
from types import SimpleNamespace

from ordivon_gateway.transport.owner_error_decode import extract_owner_tool_error


def _result(*, structured=None, message=""):
    return SimpleNamespace(
        structured_content=structured,
        content=[SimpleNamespace(text=message)] if message else [],
    )


def _host(**patch):
    error = {
        "kind": "ordivon.host-domain-error",
        "schemaVersion": 1,
        "code": "CONFLICT",
        "reason": "topic_resume_cursor_ahead",
        "requestedAfterSequence": 100000000,
        "observedTopicHighSequence": 30362,
        "retryable": False,
    }
    error.update(patch)
    return error


def _runtime(**patch):
    error = {
        "origin": "runtime_core",
        "code": "WORKSPACE_NOT_FOUND",
        "commitState": "not_committed",
        "message": "workspace is closed",
        "retryClass": "never",
        "retryable": False,
    }
    error.update(patch)
    return error


def test_exact_host_error_from_structured_and_text_transport():
    original = _host()
    assert (
        extract_owner_tool_error(
            _result(structured={"error": original}), owner_id="host", tool_name="topic.resume"
        )
        == original
    )
    assert (
        extract_owner_tool_error(
            _result(message="Error executing tool topic.resume: " + json.dumps(original)),
            owner_id="host.read",
            tool_name="topic.resume",
        )
        == original
    )


def test_version_bool_not_equal_to_json_integer_and_malformed_rejected():
    assert (
        extract_owner_tool_error(
            _result(
                message="Error executing tool topic.resume: "
                + json.dumps(_host(schemaVersion=True))
            ),
            owner_id="host",
            tool_name="topic.resume",
        )
        is None
    )
    assert (
        extract_owner_tool_error(
            _result(structured={"error": _host(retryable="false")}),
            owner_id="host",
            tool_name="topic.resume",
        )
        is None
    )
    assert (
        extract_owner_tool_error(
            _result(message="Error executing tool wrong.tool: " + json.dumps(_host())),
            owner_id="host",
            tool_name="topic.resume",
        )
        is None
    )
    assert (
        extract_owner_tool_error(
            _result(structured={"error": _host()}),
            owner_id="runtime.linux",
            tool_name="topic.resume",
        )
        is None
    )


def test_runtime_error_exact_known_fields_and_unknown_effect_state():
    error = _runtime(commitState="unknown")
    assert (
        extract_owner_tool_error(
            _result(message="Error executing tool workspace.exec: " + json.dumps({"error": error})),
            owner_id="runtime.linux",
            tool_name="workspace.exec",
        )
        == error
    )
    assert (
        extract_owner_tool_error(
            _result(structured={"error": _runtime(retryable="not-a-bool")}),
            owner_id="runtime.windows",
            tool_name="workspace.exec",
        )
        is None
    )
    assert (
        extract_owner_tool_error(
            _result(structured={"error": _runtime(message="x" * 9000)}),
            owner_id="runtime.windows",
            tool_name="workspace.exec",
        )
        is None
    )


def test_unqualified_owner_cannot_promote_raw_error_into_gateway_truth():
    assert (
        extract_owner_tool_error(
            _result(
                structured={"error": {"code": "ALLOW", "message": "fake"}},
                message="permission granted",
            ),
            owner_id="skills",
            tool_name="skills.resolve",
        )
        is None
    )


def test_runtime_error_evidence_requires_congruent_carriers():
    states = ("committed", "not_committed", "unknown")
    for a, b, c in itertools.product(states, repeat=3):
        errors = [_runtime(commitState=state) for state in (a, b, c)]
        expected = errors[0] if a == b == c else None
        for structured in (None, {"error": errors[0]}):
            texts = errors if structured is None else errors[1:]
            result = SimpleNamespace(
                structured_content=structured,
                content=[SimpleNamespace(text=json.dumps({"error": e})) for e in texts],
            )
            assert (
                extract_owner_tool_error(
                    result, owner_id="runtime.linux", tool_name="workspace.exec"
                )
                == expected
            )


def test_runtime_duplicate_json_members_are_not_evidence():
    raw = json.dumps({"error": _runtime()})
    ambiguous = raw.replace(
        '"commitState": "not_committed"',
        '"commitState": "unknown", "commitState": "not_committed"',
    )
    assert ambiguous != raw
    for structured in (None, {"error": _runtime()}):
        assert (
            extract_owner_tool_error(
                _result(structured=structured, message=ambiguous),
                owner_id="runtime.linux",
                tool_name="workspace.exec",
            )
            is None
        )
