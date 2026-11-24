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
