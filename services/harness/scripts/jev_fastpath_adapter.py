#!/usr/bin/env python3
"""Thin Ordivon adapter for the externally maintained Jev Ultrafast provider.

Ownership boundary:
- Jev owns browser perception/decision/execution.
- Browser Harness owns CDP attachment.
- This adapter owns only readiness, durable request fencing, bounded receipt
  projection, and simple code-owned outcome witnesses.
- Runtime owns physical execution truth. A Jev DONE is never promoted to
  semantic success without an explicit witness.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Mapping
from urllib.parse import urlparse
from urllib.request import urlopen

REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
ALLOWED_SCHEMES = {"http", "https", "file", "data"}
WITNESS_KEYS = {"urlEquals", "urlPrefix", "titleContains", "textContains"}
DEFAULT_STATE_ROOT = Path(
    os.environ.get(
        "ORDIVON_JEV_FASTPATH_STATE_ROOT",
        str(Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/state")) / "Ordivon/AgentAutomation/jev-fastpath"),
    )
)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def text_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(raw, path)
    finally:
        try:
            os.unlink(raw)
        except FileNotFoundError:
            pass


def validate_request(raw: Mapping[str, Any]) -> dict[str, Any]:
    request_id = str(raw.get("requestId") or "")
    if not REQUEST_ID.fullmatch(request_id):
        raise ValueError("requestId must be a bounded stable identifier")
    url = str(raw.get("url") or "")
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError("url scheme is not admitted")
    if parsed.scheme == "data":
        lowered = url.lower()
        if not (
            lowered.startswith("data:text/html,")
            or lowered.startswith("data:text/html;charset=utf-8,")
        ):
            raise ValueError("data URL must be bounded text/html")
        if len(url.encode("utf-8")) > 65536:
            raise ValueError("data URL exceeds 65536 UTF-8 bytes")
    goal = str(raw.get("goal") or "").strip()
    if not goal:
        raise ValueError("goal is required")
    witness_raw = raw.get("witness")
    if witness_raw is not None:
        if not isinstance(witness_raw, Mapping) or not witness_raw:
            raise ValueError("witness must be a non-empty object")
        unknown = set(witness_raw) - WITNESS_KEYS
        if unknown:
            raise ValueError(f"unsupported witness keys: {sorted(unknown)}")
        witness = {}
        for key, value in witness_raw.items():
            if not isinstance(value, str) or not value:
                raise ValueError(f"witness {key} must be a non-empty string")
            witness[key] = value
    else:
        witness = None
    return {
        "schemaVersion": 1,
        "requestId": request_id,
        "url": url,
        "goal": goal,
        "requireText": bool(raw.get("requireText", False)),
        "witness": witness,
    }


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.c_ulong),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def _dpapi_unprotect(path_text: str) -> str:
    if os.name != "nt":
        raise RuntimeError("DPAPI credential binding requires native Windows")
    path = Path(path_text)
    raw = path.read_bytes()
    if not raw:
        raise RuntimeError("DPAPI credential blob is empty")
    source = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    incoming = _DataBlob(
        len(raw), ctypes.cast(source, ctypes.POINTER(ctypes.c_ubyte))
    )
    outgoing = _DataBlob()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(incoming), None, None, None, None, 0, ctypes.byref(outgoing)
    )
    if not ok:
        raise OSError(ctypes.get_last_error(), "CryptUnprotectData failed")
    try:
        value = ctypes.string_at(outgoing.pbData, outgoing.cbData).decode("utf-8").strip()
    finally:
        kernel32.LocalFree(outgoing.pbData)
    if not value or any(ch.isspace() for ch in value):
        raise RuntimeError("decrypted provider credential is empty or malformed")
    return value


def _provider_environment(
    env: Mapping[str, str] | None = None, *, require_text: bool = False
) -> dict[str, str]:
    resolved = dict(env or os.environ)
    bindings = (
        ("TYPESAFE_API_KEY", "ORDIVON_JEV_TYPESAFE_DPAPI_FILE"),
        ("TEXT_MODEL_API_KEY", "ORDIVON_JEV_TEXT_MODEL_DPAPI_FILE"),
    )
    for secret_name, binding_name in bindings:
        if resolved.get(secret_name):
            continue
        path = str(resolved.get(binding_name) or "")
        if path:
            resolved[secret_name] = _dpapi_unprotect(path)
    return resolved


@contextlib.contextmanager
def _temporary_provider_secrets(provider_env: Mapping[str, str]):
    names = ("TYPESAFE_API_KEY", "TEXT_MODEL_API_KEY")
    previous = {name: os.environ.get(name) for name in names}
    try:
        for name in names:
            value = provider_env.get(name)
            if value:
                os.environ[name] = value
            else:
                os.environ.pop(name, None)
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def credential_readiness(env: Mapping[str, str] | None = None, *, require_text: bool = False) -> dict[str, Any]:
    env = _provider_environment(env, require_text=require_text)
    typesafe = bool(env.get("TYPESAFE_API_KEY"))
    text = bool(env.get("TEXT_MODEL_API_KEY"))
    missing = []
    if not typesafe:
        missing.append("TYPESAFE_API_KEY")
    if require_text and not text:
        missing.append("TEXT_MODEL_API_KEY")
    return {
        "typesafePresent": typesafe,
        "textModelPresent": text,
        "requireText": require_text,
        "missing": missing,
        "ready": not missing,
    }



def _is_windows_native() -> bool:
    return os.name == "nt"


def _python_utf8_mode() -> bool:
    return bool(sys.flags.utf8_mode)


def managed_chrome_readiness(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = env or os.environ
    path = str(env.get("ORDIVON_JEV_CHROME_PATH") or "")
    profile = str(env.get("ORDIVON_JEV_CHROME_PROFILE") or "")
    raw_port = str(env.get("ORDIVON_JEV_CDP_PORT") or "9333")
    try:
        port = int(raw_port)
    except ValueError:
        port = -1
    configured = bool(path and profile and 1024 <= port <= 65535)
    return {
        "configured": configured,
        "executablePresent": bool(path and Path(path).is_file()),
        "profileConfigured": bool(profile),
        "port": port if 1024 <= port <= 65535 else None,
        "available": bool(configured and Path(path).is_file() and _is_windows_native()),
    }


def _launch_managed_chrome(env: Mapping[str, str] | None = None) -> dict[str, Any] | None:
    """Launch a dedicated Windows Chrome only when explicitly bound by Workstation.

    This runs after credential admission and before the durable browser-action fence.
    The regular user Chrome profile is never inspected or reused.
    """
    env = env or os.environ
    if env.get("BU_CDP_URL") or env.get("BU_CDP_WS"):
        return None
    ready = managed_chrome_readiness(env)
    if not ready["available"]:
        return None
    path = Path(str(env["ORDIVON_JEV_CHROME_PATH"]))
    profile = Path(str(env["ORDIVON_JEV_CHROME_PROFILE"]))
    port = int(ready["port"])
    endpoint = f"http://127.0.0.1:{port}"
    try:
        with urlopen(endpoint + "/json/version", timeout=0.5):
            raise RuntimeError("managed Jev CDP port is already live; refusing ambiguous browser reuse")
    except RuntimeError:
        raise
    except Exception:
        pass
    profile.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(
        [
            str(path),
            "--remote-debugging-address=127.0.0.1",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 15
    version: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        try:
            with urlopen(endpoint + "/json/version", timeout=1) as response:
                candidate = json.loads(response.read())
            if isinstance(candidate, dict) and candidate.get("webSocketDebuggerUrl"):
                version = candidate
                break
        except Exception:
            time.sleep(0.2)
    if version is None:
        try:
            process.terminate()
        except Exception:
            pass
        raise RuntimeError("managed Jev Chrome did not reach CDP readiness")
    os.environ["BU_CDP_URL"] = endpoint
    os.environ.setdefault("BU_NAME", "ordivon-jev")
    os.environ.setdefault("BH_TAB_MARKER", "0")
    os.environ.setdefault("BH_UPDATE_CHECK", "0")
    return {
        "process": process,
        "endpoint": endpoint,
        "browser": version.get("Browser"),
        "protocolVersion": version.get("Protocol-Version"),
        "profile": str(profile),
    }


def _cleanup_managed_chrome(launch: Mapping[str, Any] | None) -> None:
    if not launch:
        return
    process = launch.get("process")
    if process is None:
        return
    try:
        if process.poll() is None:
            if _is_windows_native():
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                    check=False,
                )
            else:
                process.terminate()
    except Exception:
        pass


def provider_readiness(env: Mapping[str, str] | None = None, *, require_text: bool = False) -> dict[str, Any]:
    env = env or os.environ
    packages: dict[str, str | None] = {}
    for package in ("jev-ultrafast", "browser-harness"):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    daemon = {"alive": False, "browserReady": False, "browserKind": None}
    try:
        from browser_harness.admin import daemon_alive, daemon_browser_kind, daemon_browser_ready

        daemon = {
            "alive": bool(daemon_alive()),
            "browserReady": bool(daemon_browser_ready()),
            "browserKind": daemon_browser_kind(),
        }
    except Exception:
        pass

    cdp = {"configured": False, "reachable": False, "browser": None, "protocolVersion": None}
    if env.get("BU_CDP_URL"):
        cdp["configured"] = True
        try:
            base = str(env["BU_CDP_URL"]).rstrip("/")
            with urlopen(base + "/json/version", timeout=1.5) as response:
                value = json.loads(response.read())
            cdp.update(
                reachable=True,
                browser=value.get("Browser"),
                protocolVersion=value.get("Protocol-Version"),
                webSocketPresent=bool(value.get("webSocketDebuggerUrl")),
            )
        except Exception:
            pass
    elif env.get("BU_CDP_WS"):
        cdp["configured"] = True
        cdp["webSocketConfigured"] = True

    credentials = credential_readiness(env, require_text=require_text)
    managed_chrome = managed_chrome_readiness(env)
    browser_substrate_ready_now = bool(daemon["browserReady"] or cdp["reachable"])
    browser_bootstrap_available = bool(managed_chrome["available"])
    python_utf8_ready = bool(not _is_windows_native() or _python_utf8_mode())
    return {
        "schemaVersion": 1,
        "kind": "ordivon.jev-fastpath-readiness",
        "packages": packages,
        "browserHarness": daemon,
        "cdp": cdp,
        "managedChrome": managed_chrome,
        "browserSubstrateReadyNow": browser_substrate_ready_now,
        "browserSubstrateReady": browser_substrate_ready_now,
        "browserBootstrapAvailable": browser_bootstrap_available,
        "pythonUtf8Mode": _python_utf8_mode(),
        "pythonUtf8Ready": python_utf8_ready,
        "credentials": credentials,
        "readyForRun": bool(
            packages["jev-ultrafast"]
            and packages["browser-harness"]
            and (browser_substrate_ready_now or browser_bootstrap_available)
            and python_utf8_ready
            and credentials["ready"]
        ),
        "nonClaims": ["browser_semantic_success", "provider_network_serviceable", "task_authorized"],
    }


def evaluate_witness(page: Mapping[str, Any], witness: Mapping[str, str] | None) -> dict[str, Any]:
    if witness is None:
        return {"standing": "UNVERIFIED", "checks": []}
    url = str(page.get("url") or "")
    title = str(page.get("title") or "")
    text = str(page.get("text") or "")
    checks = []
    for key, expected in witness.items():
        if key == "urlEquals":
            observed, passed = url, url == expected
        elif key == "urlPrefix":
            observed, passed = url, url.startswith(expected)
        elif key == "titleContains":
            observed, passed = title, expected in title
        elif key == "textContains":
            observed, passed = f"sha256:{hashlib.sha256(text.encode()).hexdigest()}", expected in text
        else:  # validate_request already rejects this
            raise ValueError(f"unsupported witness key: {key}")
        checks.append(
            {
                "kind": key,
                "expected": expected,
                "passed": bool(passed),
                "observed": observed if key != "textContains" else None,
                "observedTextDigest": observed if key == "textContains" else None,
            }
        )
    return {"standing": "PASS" if all(row["passed"] for row in checks) else "FAIL", "checks": checks}


def _safe_history(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        text = row.get("text")
        out.append(
            {
                "step": row.get("step"),
                "kind": row.get("kind"),
                "operation": row.get("operation"),
                "action": row.get("action"),
                "choice": row.get("choice"),
                "pageChanged": row.get("page_changed"),
                "url": row.get("url"),
                "textPresent": isinstance(text, str) and bool(text),
                "textDigest": text_digest(text) if isinstance(text, str) and text else None,
            }
        )
    return out


def _safe_page(page: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(page, Mapping):
        return None
    text = str(page.get("text") or "")
    return {
        "url": str(page.get("url") or ""),
        "title": str(page.get("title") or ""),
        "textLength": len(text),
        "textDigest": text_digest(text),
        "fingerprint": page.get("fingerprint"),
    }


def _paths(state_root: Path, request_id: str) -> tuple[Path, Path]:
    key = hashlib.sha256(request_id.encode()).hexdigest()[:32]
    root = state_root / key
    return root / "started.json", root / "receipt.json"


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid state object: {path}")
    return value


def _replay_or_unknown(
    request: Mapping[str, Any], state_root: Path
) -> dict[str, Any] | None:
    request_digest = digest(request)
    started_path, receipt_path = _paths(state_root, str(request["requestId"]))
    receipt = _load_json(receipt_path)
    if receipt is not None:
        if receipt.get("requestDigest") != request_digest:
            raise RuntimeError("requestId already belongs to a different request")
        return {**receipt, "replayed": True}
    started = _load_json(started_path)
    if started is not None:
        if started.get("requestDigest") != request_digest:
            raise RuntimeError("requestId already belongs to a different request")
        return {
            "schemaVersion": 1,
            "kind": "ordivon.jev-fastpath-receipt",
            "requestId": request["requestId"],
            "requestDigest": request_digest,
            "standing": "UNKNOWN_REQUIRES_RECONCILE",
            "startedAt": started.get("startedAt"),
            "replayed": True,
            "providerEffectMayHaveOccurred": True,
            "outcomeWitness": {"standing": "UNVERIFIED", "checks": []},
        }
    return None


def execute_request(
    raw: Mapping[str, Any],
    *,
    state_root: Path = DEFAULT_STATE_ROOT,
    env: Mapping[str, str] | None = None,
    agent_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    request = validate_request(raw)
    env = env or os.environ
    replay = _replay_or_unknown(request, state_root)
    if replay is not None:
        return replay
    try:
        provider_env = _provider_environment(env, require_text=request["requireText"])
        credentials = credential_readiness(provider_env, require_text=request["requireText"])
    except Exception as exc:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.jev-fastpath-receipt",
            "requestId": request["requestId"],
            "requestDigest": digest(request),
            "standing": "CREDENTIAL_MISSING",
            "missingCredentials": ["TYPESAFE_API_KEY"],
            "credentialBindingError": f"{type(exc).__name__}: {str(exc)[:400]}",
            "replayed": False,
            "providerEffectMayHaveOccurred": False,
            "outcomeWitness": {"standing": "UNVERIFIED", "checks": []},
        }
    if not credentials["ready"]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.jev-fastpath-receipt",
            "requestId": request["requestId"],
            "requestDigest": digest(request),
            "standing": "CREDENTIAL_MISSING",
            "missingCredentials": credentials["missing"],
            "replayed": False,
            "providerEffectMayHaveOccurred": False,
            "outcomeWitness": {"standing": "UNVERIFIED", "checks": []},
        }
    if _is_windows_native() and not _python_utf8_mode():
        return {
            "schemaVersion": 1,
            "kind": "ordivon.jev-fastpath-receipt",
            "requestId": request["requestId"],
            "requestDigest": digest(request),
            "standing": "PROVIDER_ENV_INVALID",
            "detail": "Windows Jev requires Python UTF-8 mode (PYTHONUTF8=1)",
            "replayed": False,
            "providerEffectMayHaveOccurred": False,
            "outcomeWitness": {"standing": "UNVERIFIED", "checks": []},
        }

    managed_launch = None
    if agent_factory is None:
        managed_launch = _launch_managed_chrome(provider_env)
        with _temporary_provider_secrets(provider_env):
            from jev_ultrafast import Agent

        agent_factory = Agent

    started_path, receipt_path = _paths(state_root, request["requestId"])
    request_digest = digest(request)
    started = {
        "schemaVersion": 1,
        "kind": "ordivon.jev-fastpath-started",
        "requestId": request["requestId"],
        "requestDigest": request_digest,
        "startedAt": utc_now(),
    }
    _atomic_json(started_path, started)

    final: dict[str, Any] | None = None
    history: list[Mapping[str, Any]] = []
    error: Exception | None = None
    try:
        with _temporary_provider_secrets(provider_env):
            with agent_factory(request["url"], request["goal"], screenshots=False) as agent:
                for snapshot in agent.run():
                    final = snapshot
                if final is None:
                    final = agent.snapshot()
                history = list(final.get("history") or [])
    except Exception as exc:
        error = exc
        try:
            state = getattr(locals().get("agent"), "state", None)
            if isinstance(state, Mapping):
                history = list(state.get("history") or [])
                final = {
                    "status": state.get("status"),
                    "page": state.get("page"),
                    "history": history,
                    "elapsed_ms": state.get("elapsed_ms"),
                }
        except Exception:
            pass
    finally:
        _cleanup_managed_chrome(managed_launch)

    if error is not None:
        standing = "FAILED_AFTER_ACTIONS" if history else "FAILED_BEFORE_ACTION"
        witness = {"standing": "UNVERIFIED", "checks": []}
    else:
        upstream = str((final or {}).get("status") or "unknown")
        witness = evaluate_witness((final or {}).get("page") or {}, request["witness"])
        if upstream == "done" and witness["standing"] == "PASS":
            standing = "PASS"
        elif upstream == "done" and witness["standing"] == "UNVERIFIED":
            standing = "DONE_UNVERIFIED"
        elif upstream == "done":
            standing = "DONE_WITNESS_FAILED"
        elif upstream == "blocked":
            standing = "BLOCKED"
        else:
            standing = "INCOMPLETE"

    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.jev-fastpath-receipt",
        "requestId": request["requestId"],
        "requestDigest": request_digest,
        "standing": standing,
        "replayed": False,
        "startedAt": started["startedAt"],
        "finishedAt": utc_now(),
        "upstreamStatus": (final or {}).get("status"),
        "providerEffectMayHaveOccurred": bool(history),
        "actionCount": len(history),
        "actions": _safe_history(history),
        "finalPage": _safe_page((final or {}).get("page")),
        "outcomeWitness": witness,
        "error": (
            {"type": type(error).__name__, "message": str(error)[:1000]} if error is not None else None
        ),
        "nonClaims": [
            "model_done_is_not_semantic_success",
            "runtime_execution_truth",
            "task_authorization",
        ],
    }
    _atomic_json(receipt_path, receipt)
    return receipt


def _read_request(path: str) -> dict[str, Any]:
    if path == "-":
        import sys

        value = json.load(sys.stdin)
    else:
        # Windows PowerShell 5.1 emits a UTF-8 BOM for Set-Content -Encoding UTF8.
        # utf-8-sig accepts both BOM and ordinary UTF-8 without weakening JSON parsing.
        value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("request must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Ordivon thin adapter for Jev Ultrafast")
    parser.add_argument("--state-root", type=Path, default=DEFAULT_STATE_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status")
    status.add_argument("--require-text", action="store_true")
    run = sub.add_parser("run")
    run.add_argument("--request-file", required=True)
    args = parser.parse_args()
    if args.command == "status":
        value = provider_readiness(require_text=args.require_text)
    else:
        value = execute_request(_read_request(args.request_file), state_root=args.state_root)
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
