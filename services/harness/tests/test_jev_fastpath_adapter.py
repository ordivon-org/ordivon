from __future__ import annotations

import importlib.util
from pathlib import Path
import json
import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/jev_fastpath_adapter.py"
SPEC = importlib.util.spec_from_file_location("jev_fastpath_adapter", MODULE_PATH)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class FakeAgent:
    instances = 0

    def __init__(self, url, goal, screenshots=False, *, status="done", text="Success visible", fail=False):
        type(self).instances += 1
        self.url = url
        self.goal = goal
        self._status = status
        self._text = text
        self._fail = fail
        self.state = {
            "status": "ready",
            "page": {"url": url, "title": "Demo", "text": "Start", "fingerprint": "f0"},
            "history": [],
            "elapsed_ms": 0,
        }

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def run(self):
        if self._fail:
            self.state["history"].append(
                {
                    "step": 1,
                    "kind": "click",
                    "operation": "CLICK",
                    "action": "Open",
                    "choice": "e1",
                    "page_changed": True,
                    "url": self.url,
                    "text": None,
                }
            )
            raise RuntimeError("fixture failure")
        self.state["status"] = self._status
        self.state["page"] = {
            "url": self.url + "/done",
            "title": "Finished",
            "text": self._text,
            "fingerprint": "f1",
        }
        yield self.snapshot()

    def snapshot(self):
        return {
            "status": self.state["status"],
            "page": self.state["page"],
            "history": list(self.state["history"]),
            "elapsed_ms": 1,
        }


def req(**extra):
    value = {"requestId": "r1", "url": "https://example.test", "goal": "Open the result"}
    value.update(extra)
    return value


def factory(**kw):
    return lambda url, goal, screenshots=False: FakeAgent(url, goal, screenshots, **kw)


def test_bounded_html_data_url_is_admitted_for_deterministic_fixture():
    value = M.validate_request(
        req(url="data:text/html;charset=utf-8,%3Cbutton%3EOk%3C%2Fbutton%3E")
    )
    assert value["url"].startswith("data:text/html")
    with pytest.raises(ValueError, match="bounded text/html"):
        M.validate_request(req(url="data:text/plain,not-html"))
    with pytest.raises(ValueError, match="exceeds 65536"):
        M.validate_request(req(url="data:text/html," + ("x" * 70000)))


def test_dpapi_binding_resolves_without_mutating_caller_environment(monkeypatch):
    monkeypatch.setattr(
        M,
        "_dpapi_unprotect",
        lambda path: "typesafe-value" if "typesafe" in path else "text-value",
    )
    env = {
        "ORDIVON_JEV_TYPESAFE_DPAPI_FILE": r"C:\\Secrets\\typesafe.dpapi",
        "ORDIVON_JEV_TEXT_MODEL_DPAPI_FILE": r"C:\\Secrets\\text.dpapi",
    }
    resolved = M._provider_environment(env, require_text=True)
    assert resolved["TYPESAFE_API_KEY"] == "typesafe-value"
    assert resolved["TEXT_MODEL_API_KEY"] == "text-value"
    assert "TYPESAFE_API_KEY" not in env
    assert "TEXT_MODEL_API_KEY" not in env


def test_missing_typesafe_blocks_before_fence(tmp_path):
    out = M.execute_request(req(), state_root=tmp_path, env={}, agent_factory=factory())
    assert out["standing"] == "CREDENTIAL_MISSING"
    assert out["providerEffectMayHaveOccurred"] is False
    assert list(tmp_path.rglob("*.json")) == []


def test_require_text_fails_closed_without_text_key(tmp_path):
    out = M.execute_request(
        req(requireText=True),
        state_root=tmp_path,
        env={"TYPESAFE_API_KEY": "x"},
        agent_factory=factory(),
    )
    assert out["standing"] == "CREDENTIAL_MISSING"
    assert out["missingCredentials"] == ["TEXT_MODEL_API_KEY"]


def test_done_needs_explicit_witness_for_pass(tmp_path):
    out = M.execute_request(
        req(witness={"textContains": "Success visible"}),
        state_root=tmp_path,
        env={"TYPESAFE_API_KEY": "x"},
        agent_factory=factory(),
    )
    assert out["standing"] == "PASS"
    assert out["outcomeWitness"]["standing"] == "PASS"


def test_done_without_witness_is_not_success(tmp_path):
    out = M.execute_request(
        req(),
        state_root=tmp_path,
        env={"TYPESAFE_API_KEY": "x"},
        agent_factory=factory(),
    )
    assert out["standing"] == "DONE_UNVERIFIED"


def test_witness_failure_is_explicit(tmp_path):
    out = M.execute_request(
        req(witness={"titleContains": "Missing"}),
        state_root=tmp_path,
        env={"TYPESAFE_API_KEY": "x"},
        agent_factory=factory(),
    )
    assert out["standing"] == "DONE_WITNESS_FAILED"
    assert out["outcomeWitness"]["standing"] == "FAIL"


def test_failure_after_action_is_not_retried(tmp_path):
    FakeAgent.instances = 0
    out = M.execute_request(
        req(),
        state_root=tmp_path,
        env={"TYPESAFE_API_KEY": "x"},
        agent_factory=factory(fail=True),
    )
    assert out["standing"] == "FAILED_AFTER_ACTIONS"
    assert out["actionCount"] == 1
    again = M.execute_request(
        req(),
        state_root=tmp_path,
        env={"TYPESAFE_API_KEY": "x"},
        agent_factory=factory(),
    )
    assert again["standing"] == "FAILED_AFTER_ACTIONS"
    assert again["replayed"] is True
    assert FakeAgent.instances == 1


def test_orphan_started_fails_closed_as_unknown(tmp_path):
    request = M.validate_request(req())
    started_path, _ = M._paths(tmp_path, request["requestId"])
    M._atomic_json(
        started_path,
        {
            "schemaVersion": 1,
            "requestId": request["requestId"],
            "requestDigest": M.digest(request),
            "startedAt": "2026-09-18T00:00:00Z",
        },
    )
    FakeAgent.instances = 0
    out = M.execute_request(
        req(),
        state_root=tmp_path,
        env={"TYPESAFE_API_KEY": "x"},
        agent_factory=factory(),
    )
    assert out["standing"] == "UNKNOWN_REQUIRES_RECONCILE"
    assert out["providerEffectMayHaveOccurred"] is True
    assert FakeAgent.instances == 0


def test_request_id_conflict_rejected(tmp_path):
    first = M.execute_request(
        req(),
        state_root=tmp_path,
        env={"TYPESAFE_API_KEY": "x"},
        agent_factory=factory(),
    )
    assert first["standing"] == "DONE_UNVERIFIED"
    with pytest.raises(RuntimeError, match="different request"):
        M.execute_request(
            req(goal="Different goal"),
            state_root=tmp_path,
            env={"TYPESAFE_API_KEY": "x"},
            agent_factory=factory(),
        )


def test_receipt_redacts_goal_and_text(tmp_path):
    secret = "private-value-123"
    out = M.execute_request(
        req(goal="Type " + secret),
        state_root=tmp_path,
        env={"TYPESAFE_API_KEY": "x"},
        agent_factory=factory(text=secret),
    )
    raw = json.dumps(out)
    assert "Type " + secret not in raw
    assert secret not in raw
    assert out["finalPage"]["textDigest"].startswith("sha256:")


def test_provider_readiness_distinguishes_cold_daemon_from_reachable_cdp(monkeypatch):
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self):
            return b'{"Browser":"Chrome/152","Protocol-Version":"1.3","webSocketDebuggerUrl":"ws://secret"}'

    monkeypatch.setattr(M, "urlopen", lambda *_args, **_kwargs: Response())
    out = M.provider_readiness(
        {"BU_CDP_URL": "http://127.0.0.1:9333", "TYPESAFE_API_KEY": "x"}
    )
    assert out["cdp"]["reachable"] is True
    assert out["cdp"]["browser"] == "Chrome/152"
    assert "webSocketDebuggerUrl" not in json.dumps(out)
    assert out["browserSubstrateReady"] is True


def test_request_file_accepts_windows_powershell_utf8_bom(tmp_path):
    path = tmp_path / "request.json"
    path.write_bytes(b"\xef\xbb\xbf" + b'{"requestId":"bom-r1","url":"https://example.test","goal":"Read"}')
    value = M._read_request(str(path))
    assert value["requestId"] == "bom-r1"


def test_missing_credentials_never_bootstrap_managed_chrome(tmp_path, monkeypatch):
    monkeypatch.setattr(
        M,
        "_launch_managed_chrome",
        lambda _env=None: (_ for _ in ()).throw(AssertionError("browser must not launch")),
    )
    out = M.execute_request(
        req(),
        state_root=tmp_path,
        env={
            "ORDIVON_JEV_CHROME_PATH": "C:/Chrome/chrome.exe",
            "ORDIVON_JEV_CHROME_PROFILE": "C:/profile",
        },
        agent_factory=None,
    )
    assert out["standing"] == "CREDENTIAL_MISSING"


def test_readiness_can_be_run_ready_from_managed_chrome_bootstrap(monkeypatch, tmp_path):
    chrome = tmp_path / "chrome.exe"
    chrome.write_bytes(b"x")
    monkeypatch.setattr(M, "_is_windows_native", lambda: True)
    monkeypatch.setattr(M, "_python_utf8_mode", lambda: True)
    monkeypatch.setattr(
        M.importlib.metadata,
        "version",
        lambda package: {"jev-ultrafast": "0.1.0", "browser-harness": "0.1.13"}[package],
    )
    monkeypatch.setattr(
        M,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("cold")),
    )
    out = M.provider_readiness(
        {
            "ORDIVON_JEV_CHROME_PATH": str(chrome),
            "ORDIVON_JEV_CHROME_PROFILE": str(tmp_path / "profile"),
            "ORDIVON_JEV_CDP_PORT": "9333",
            "TYPESAFE_API_KEY": "x",
        }
    )
    assert out["browserSubstrateReadyNow"] is False
    assert out["browserBootstrapAvailable"] is True
    assert out["readyForRun"] is True


def test_managed_chrome_rejects_ambiguous_live_port(monkeypatch, tmp_path):
    chrome = tmp_path / "chrome.exe"
    chrome.write_bytes(b"x")
    monkeypatch.setattr(M, "_is_windows_native", lambda: True)

    class Live:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(M, "urlopen", lambda *_args, **_kwargs: Live())
    with pytest.raises(RuntimeError, match="ambiguous browser reuse"):
        M._launch_managed_chrome(
            {
                "ORDIVON_JEV_CHROME_PATH": str(chrome),
                "ORDIVON_JEV_CHROME_PROFILE": str(tmp_path / "profile"),
                "ORDIVON_JEV_CDP_PORT": "9333",
            }
        )


def test_windows_utf8_mode_is_a_pre_effect_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "_is_windows_native", lambda: True)
    monkeypatch.setattr(M, "_python_utf8_mode", lambda: False)
    monkeypatch.setattr(
        M,
        "_launch_managed_chrome",
        lambda _env=None: (_ for _ in ()).throw(AssertionError("browser must not launch")),
    )
    out = M.execute_request(
        req(),
        state_root=tmp_path,
        env={"TYPESAFE_API_KEY": "x"},
        agent_factory=None,
    )
    assert out["standing"] == "PROVIDER_ENV_INVALID"
    assert out["providerEffectMayHaveOccurred"] is False
