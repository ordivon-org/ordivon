#!/usr/bin/env python3
"""Read one already authorized browser turn through an existing Browser Harness daemon.

This is an operator-local observation primitive, not a public browser-control
tool. Its daemon name/environment must come from the authorized Workstation
binding. It does not start, repair, discover, navigate or close browsers.
The caller must bind the target and prompt digest to its own durable effect.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import importlib.metadata
import json
from pathlib import Path
import re
from typing import Protocol

try:
    from chatgpt_provider_resource import (
        canonical_chatgpt_resource,
        chatgpt_resource_from_page_url,
    )
    from conversation_output_evidence import (
        DOM_SNAPSHOT_ARGS,
        DOM_SNAPSHOT_EXPRESSION,
        qualify_snapshot_by_digest,
        sha256_bytes,
        validate_prompt_digest,
    )
except ModuleNotFoundError:
    from scripts.chatgpt_provider_resource import (
        canonical_chatgpt_resource,
        chatgpt_resource_from_page_url,
    )
    from scripts.conversation_output_evidence import (
        DOM_SNAPSHOT_ARGS,
        DOM_SNAPSHOT_EXPRESSION,
        qualify_snapshot_by_digest,
        sha256_bytes,
        validate_prompt_digest,
    )


# This private SDK seam is qualified against the installed package's exact
# version. Do not infer semantic compatibility of another version from import.
QUALIFIED_BROWSER_HARNESS_VERSION = "0.1.13"


class ObservationTransport(Protocol):
    def ping(self) -> bool: ...

    def call(
        self, method: str, params: dict, session_id: str | None = None
    ) -> dict: ...


class ExistingDaemonTransport:
    """Reuse the SDK's authenticated IPC only; do not import its CLI/helpers."""

    def __init__(self, daemon_name: str) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", daemon_name):
            raise ValueError("invalid configured daemon name")
        self.daemon_name = daemon_name
        self._ipc = None
        try:
            if importlib.metadata.version("browser-harness") != QUALIFIED_BROWSER_HARNESS_VERSION:
                return
            from browser_harness import _ipc

            self._ipc = _ipc
        except (ImportError, importlib.metadata.PackageNotFoundError):
            return

    def ping(self) -> bool:
        return self._ipc is not None and self._ipc.ping(self.daemon_name, timeout=1.0) is True

    def call(self, method: str, params: dict, session_id: str | None = None) -> dict:
        if self._ipc is None:
            raise RuntimeError("qualified existing daemon transport unavailable")
        # The SDK owns local IPC authentication. Never print the token, raw
        # transport error, response, or an unrelated conversation snapshot.
        connection, token = self._ipc.connect(self.daemon_name, timeout=5.0)
        with closing(connection):
            result = self._ipc.request(
                connection, token,
                {"method": method, "params": params, "session_id": session_id},
            )
        if (
            not isinstance(result, dict)
            or "error" in result
            or not isinstance(result.get("result"), dict)
        ):
            raise RuntimeError("CDP observation command not confirmed")
        return result["result"]


def _matching_targets(response: object, resource: str) -> list[tuple[str, str]]:
    if not isinstance(response, dict) or not isinstance(response.get("targetInfos"), list):
        raise ValueError("invalid target observation")
    matches = []
    for row in response["targetInfos"]:
        if not isinstance(row, dict) or not isinstance(row.get("type"), str):
            raise ValueError("invalid target observation")
        if row["type"] != "page":
            continue
        target, url = row.get("targetId"), row.get("url")
        if not isinstance(target, str) or not target or not isinstance(url, str):
            raise ValueError("invalid target observation")
        if chatgpt_resource_from_page_url(url) == resource:
            matches.append((target, url))
    return matches


def read_existing_turn(
    transport: ObservationTransport, *, target_resource: str,
    expected_prompt_digest: str, observation_id: str, expected_prompt: str | None = None,
) -> dict:
    if not isinstance(target_resource, str) or canonical_chatgpt_resource(target_resource) != target_resource:
        raise ValueError("target must be one canonical conversation resource")
    validate_prompt_digest(expected_prompt_digest)
    if expected_prompt is not None and (
        not isinstance(expected_prompt, str) or not expected_prompt
        or expected_prompt != expected_prompt.strip()
        or sha256_bytes(expected_prompt.encode("utf-8")) != expected_prompt_digest
    ):
        raise ValueError("exact prompt bytes must agree with the durable digest")
    if not isinstance(observation_id, str) or not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", observation_id):
        raise ValueError("invalid observation ID")

    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-harness-conversation-output-observation",
        "observationId": observation_id,
        "targetResource": target_resource,
        "expectedPromptDigest": expected_prompt_digest,
        "observationSource": "EXISTING_DAEMON_EXPLICIT_SESSION",
        "evidenceScope": "OBSERVED_ROLE_PAIR_ONLY",
        "targetId": None,
        "standing": "DAEMON_UNAVAILABLE",
        "sessionDetached": None,
        "assistantOutput": None,
        "assistantOutputDigest": None,
        "providerEffectAttempted": False,
        "composerFilled": False,
        "sendAttempted": False,
        "releaseAttempted": False,
    }
    try:
        if transport.ping() is not True:
            return receipt
        before = _matching_targets(transport.call("Target.getTargets", {}), target_resource)
    except ValueError:
        return {**receipt, "standing": "OBSERVATION_INVALID"}
    except Exception:
        return {**receipt, "standing": "TRANSPORT_ERROR"}
    if not before:
        return {**receipt, "standing": "TARGET_NOT_VISIBLE"}
    if len(before) != 1:
        return {**receipt, "standing": "TARGET_AMBIGUOUS"}

    target_id, _ = before[0]
    receipt["targetId"] = target_id
    try:
        attached = transport.call(
            "Target.attachToTarget", {"targetId": target_id, "flatten": True}
        )
        session_id = attached.get("sessionId") if isinstance(attached, dict) else None
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("attachment identity unavailable")
    except Exception:
        # A lost attachment reply is uncertain, not a reason to attach again.
        return {**receipt, "standing": "SESSION_ATTACHMENT_UNKNOWN"}

    observation = None
    standing = "TRANSPORT_ERROR"
    try:
        result = transport.call(
            "Runtime.evaluate",
            {
                "expression": f"({DOM_SNAPSHOT_EXPRESSION})({json.dumps(DOM_SNAPSHOT_ARGS)})",
                "returnByValue": True,
                "awaitPromise": False,
            },
            session_id=session_id,
        )
        remote = result.get("result") if isinstance(result, dict) else None
        if (
            not isinstance(result, dict) or "exceptionDetails" in result
            or not isinstance(remote, dict) or remote.get("type") != "object"
            or not isinstance(remote.get("value"), dict)
        ):
            standing = "OBSERVATION_INVALID"
        else:
            after = _matching_targets(transport.call("Target.getTargets", {}), target_resource)
            if len(after) != 1 or after[0][0] != target_id:
                standing = "TARGET_RESOURCE_DRIFTED"
            else:
                observation = qualify_snapshot_by_digest(
                    remote["value"], target_resource, expected_prompt_digest, after[0][1]
                )
                standing = observation["standing"]
    except ValueError:
        standing = "OBSERVATION_INVALID"
    except Exception:
        standing = "TRANSPORT_ERROR"
    finally:
        try:
            detached = transport.call("Target.detachFromTarget", {"sessionId": session_id})
            if not isinstance(detached, dict):
                raise RuntimeError("attachment cleanup not confirmed")
            receipt["sessionDetached"] = True
        except Exception:
            receipt["sessionDetached"] = False
            standing = "SESSION_DETACH_UNCONFIRMED"

    receipt["standing"] = standing
    if standing == "CAPTURED" and observation is not None:
        # Do not return the raw DOM, other messages, error text, or session ID.
        receipt["assistantOutput"] = observation["assistantOutput"]
        receipt["assistantOutputDigest"] = observation["assistantOutputDigest"]
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daemon-name", required=True)
    parser.add_argument("--target-resource", required=True)
    parser.add_argument("--expected-user-prompt-file", type=Path)
    parser.add_argument("--expected-prompt-digest", required=True)
    parser.add_argument("--observation-id", required=True)
    args = parser.parse_args()
    try:
        prompt = (args.expected_user_prompt_file.read_bytes().decode("utf-8")
                  if args.expected_user_prompt_file is not None else None)
        receipt = read_existing_turn(
            ExistingDaemonTransport(args.daemon_name),
            target_resource=args.target_resource, expected_prompt=prompt,
            expected_prompt_digest=args.expected_prompt_digest,
            observation_id=args.observation_id,
        )
    except (OSError, UnicodeError, ValueError):
        # Do not include potentially private prompt bytes, filenames or SDK
        # diagnostics in durable stdout/stderr on invalid observation inputs.
        parser.error("invalid observation identity or prompt file")
    print(json.dumps(receipt, ensure_ascii=True, sort_keys=True))
    return 0 if receipt["standing"] == "CAPTURED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
