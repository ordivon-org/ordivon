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
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Callable, Mapping
from urllib.parse import urlparse

REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
ALLOWED_SCHEMES = {"http", "https", "file"}
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


def credential_readiness(env: Mapping[str, str] | None = None, *, require_text: bool = False) -> dict[str, Any]:
    env = env or os.environ
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
    credentials = credential_readiness(env, require_text=require_text)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.jev-fastpath-readiness",
        "packages": packages,
        "browserHarness": daemon,
        "explicitCdpConfigured": bool(env.get("BU_CDP_URL") or env.get("BU_CDP_WS")),
        "credentials": credentials,
        "readyForRun": bool(packages["jev-ultrafast"] and packages["browser-harness"] and credentials["ready"]),
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
    credentials = credential_readiness(env, require_text=request["requireText"])
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

    if agent_factory is None:
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
        value = json.loads(Path(path).read_text(encoding="utf-8"))
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
