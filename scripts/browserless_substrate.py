#!/usr/bin/env python3
"""Thin Browserless substrate binding for Agent Automation.

Browser process lifecycle, concurrency, queueing and browser health belong to Browserless. This
module only binds configured Browserless endpoints to the existing conversation effect fence. It
never persists token-bearing URLs and deliberately carries no Ordivon-specific browser state
machine.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
import subprocess
from dataclasses import dataclass
from pathlib import Path


class BrowserlessConfigError(ValueError):
    pass


class BrowserlessUnavailable(RuntimeError):
    pass


def _nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise BrowserlessConfigError(f"{label} must be a non-empty trimmed string")
    return value


def _token(path: Path) -> str:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise BrowserlessUnavailable(f"Browserless token file unavailable: {path}") from error
    if not value or any(ch.isspace() for ch in value):
        raise BrowserlessUnavailable("Browserless token file is empty or malformed")
    return value


def _append_query(url: str, values: dict[str, str]) -> str:
    parsed = urllib.parse.urlsplit(url)
    existing = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = urllib.parse.urlencode(existing + list(values.items()))
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment)
    )


@dataclass(frozen=True, slots=True)
class BrowserlessEndpoint:
    endpoint_id: str
    websocket_endpoint: str
    http_endpoint: str
    token_file: Path
    network_namespace: str | None = None
    user_data_dir: str | None = None
    launch_args: tuple[str, ...] = ()
    operator_http_endpoint: str | None = None
    headless: bool | None = None

    @classmethod
    def from_dict(cls, value: dict) -> "BrowserlessEndpoint":
        if not isinstance(value, dict):
            raise BrowserlessConfigError("Browserless endpoint must be an object")
        endpoint_id = _nonempty(value.get("id"), "browserless endpoint id")
        websocket = _nonempty(value.get("websocketEndpoint"), "browserless websocketEndpoint")
        http = _nonempty(value.get("httpEndpoint"), "browserless httpEndpoint")
        ws_scheme = urllib.parse.urlsplit(websocket).scheme
        http_scheme = urllib.parse.urlsplit(http).scheme
        if ws_scheme not in {"ws", "wss"}:
            raise BrowserlessConfigError("browserless websocketEndpoint must use ws/wss")
        if http_scheme not in {"http", "https"}:
            raise BrowserlessConfigError("browserless httpEndpoint must use http/https")
        token_file = Path(_nonempty(value.get("tokenFile"), "browserless tokenFile")).expanduser()
        network_namespace = value.get("networkNamespace")
        if network_namespace is not None:
            network_namespace = _nonempty(network_namespace, "browserless networkNamespace")
            if "/" in network_namespace or any(ch.isspace() for ch in network_namespace):
                raise BrowserlessConfigError(
                    "browserless networkNamespace must be one namespace name"
                )
        user_data_dir = value.get("userDataDir")
        if user_data_dir is not None:
            user_data_dir = _nonempty(user_data_dir, "browserless userDataDir")
            if not user_data_dir.startswith("/"):
                raise BrowserlessConfigError(
                    "browserless userDataDir must be an absolute server-side path"
                )
        raw_args = value.get("launchArgs", [])
        if not isinstance(raw_args, list) or any(not isinstance(x, str) or not x for x in raw_args):
            raise BrowserlessConfigError(
                "browserless launchArgs must be a list of non-empty strings"
            )
        operator_http = value.get("operatorHttpEndpoint")
        if operator_http is not None:
            operator_http = _nonempty(operator_http, "browserless operatorHttpEndpoint").rstrip("/")
            parsed_operator = urllib.parse.urlsplit(operator_http)
            if parsed_operator.scheme != "http" or parsed_operator.hostname not in {
                "127.0.0.1",
                "localhost",
            }:
                raise BrowserlessConfigError(
                    "browserless operatorHttpEndpoint must be a loopback http endpoint"
                )
        headless = value.get("headless")
        if headless is not None and not isinstance(headless, bool):
            raise BrowserlessConfigError("browserless headless must be boolean when present")
        return cls(
            endpoint_id=endpoint_id,
            websocket_endpoint=websocket,
            http_endpoint=http.rstrip("/"),
            token_file=token_file,
            network_namespace=network_namespace,
            user_data_dir=user_data_dir,
            launch_args=tuple(raw_args),
            operator_http_endpoint=operator_http,
            headless=headless,
        )

    @property
    def public_connection_endpoint(self) -> str:
        """Return a token-free connection URL carrying only public launch options."""
        if not self.launch_args and self.user_data_dir is None and self.headless is None:
            return self.websocket_endpoint
        launch_options: dict[str, object] = {}
        if self.launch_args:
            launch_options["args"] = list(self.launch_args)
        if self.user_data_dir is not None:
            launch_options["userDataDir"] = self.user_data_dir
        if self.headless is not None:
            launch_options["headless"] = self.headless
        launch = json.dumps(launch_options, separators=(",", ":"), sort_keys=True)
        return _append_query(self.websocket_endpoint, {"launch": launch})

    def connection_endpoint(self, *, timeout_ms: int | None = None) -> str:
        """Return a token-free Browserless connection URL with one request-scoped timeout.

        Browserless's global TIMEOUT is only a substrate default. Human-verification sessions need
        a lifecycle budget derived from the owning workflow, so the request explicitly overrides
        that default instead of relying on mutable container-wide configuration.
        """
        endpoint = self.public_connection_endpoint
        if timeout_ms is None:
            return endpoint
        if not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or timeout_ms <= 0:
            raise BrowserlessConfigError(
                "browserless connection timeout_ms must be a positive integer"
            )
        return _append_query(endpoint, {"timeout": str(timeout_ms)})

    @property
    def identity_digest(self) -> str:
        raw = json.dumps(
            {
                "id": self.endpoint_id,
                "websocketEndpoint": self.websocket_endpoint,
                "httpEndpoint": self.http_endpoint,
                "tokenFile": str(self.token_file),
                "networkNamespace": self.network_namespace,
                "userDataDir": self.user_data_dir,
                "launchArgs": list(self.launch_args),
                "headless": self.headless,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return "sha256:" + hashlib.sha256(raw).hexdigest()

    def authenticated_connection_endpoint(self, *, timeout_ms: int | None = None) -> str:
        """Construct an in-memory token-bearing URL. Callers must never persist or log it."""
        return _append_query(
            self.connection_endpoint(timeout_ms=timeout_ms), {"token": _token(self.token_file)}
        )

    def operator_connection_endpoint(self, *, timeout_ms: int | None = None) -> str:
        """Return a token-free WebSocket URL through the host-loopback operator bridge.

        This keeps callers that also need host control-plane authority out of the Browserless
        network namespace while the bridge itself enters the carrier namespace.
        """
        if self.operator_http_endpoint is None:
            raise BrowserlessConfigError(
                "browserless operatorHttpEndpoint is required for host control-plane access"
            )
        internal = urllib.parse.urlsplit(self.connection_endpoint(timeout_ms=timeout_ms))
        operator = urllib.parse.urlsplit(self.operator_http_endpoint)
        scheme = "wss" if operator.scheme == "https" else "ws"
        return urllib.parse.urlunsplit(
            (scheme, operator.netloc, internal.path, internal.query, internal.fragment)
        )

    def authenticated_operator_connection_endpoint(self, *, timeout_ms: int | None = None) -> str:
        """Construct an in-memory token-bearing operator-bridge URL. Never persist or log it."""
        return _append_query(
            self.operator_connection_endpoint(timeout_ms=timeout_ms),
            {"token": _token(self.token_file)},
        )

    def sessions(
        self, *, tracking_id: str | None = None, timeout_seconds: float = 3.0
    ) -> list[dict]:
        """Observe Browserless's current session projection without exposing credentials."""
        if tracking_id is not None:
            tracking_id = _nonempty(tracking_id, "browserless tracking_id")
        values = {"token": _token(self.token_file)}
        if tracking_id is not None:
            values["trackingId"] = tracking_id
        url = _append_query(self.http_endpoint + "/sessions", values)
        if self.network_namespace is not None:
            curl_config = f'url = "{url}"\nsilent\nshow-error\nfail\n'
            proc = subprocess.run(
                [
                    *self.exec_prefix,
                    "/usr/bin/curl",
                    "--max-time",
                    str(float(timeout_seconds)),
                    "--config",
                    "-",
                ],
                input=curl_config,
                capture_output=True,
                text=True,
                timeout=timeout_seconds + 1,
                check=False,
            )
            if proc.returncode != 0:
                raise BrowserlessUnavailable(
                    f"Browserless sessions observation failed: curl-rc-{proc.returncode}"
                )
            raw = proc.stdout
        else:
            try:
                with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
                    raw = response.read().decode("utf-8")
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                raise BrowserlessUnavailable("Browserless sessions observation failed") from error
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as error:
            raise BrowserlessUnavailable(
                "Browserless sessions observation returned invalid JSON"
            ) from error
        if not isinstance(value, list):
            raise BrowserlessUnavailable(
                "Browserless sessions observation returned a non-list result"
            )
        return [row for row in value if isinstance(row, dict)]

    def operator_url(self, internal_url: str) -> str:
        """Rebase one Browserless bearer URL onto the host-loopback operator bridge.

        DevTools inspector URLs contain a nested `ws=host/devtools/page/...` target; both the outer
        HTTP origin and that inner WebSocket authority must move together.
        """
        if self.operator_http_endpoint is None:
            return internal_url
        internal = urllib.parse.urlsplit(internal_url)
        substrate = urllib.parse.urlsplit(self.http_endpoint)
        operator = urllib.parse.urlsplit(self.operator_http_endpoint)
        if internal.scheme not in {"http", "https"} or internal.netloc != substrate.netloc:
            raise BrowserlessConfigError("operator URL source is not this Browserless endpoint")
        query = []
        for key, value in urllib.parse.parse_qsl(internal.query, keep_blank_values=True):
            if key in {"ws", "wss"} and value.startswith(substrate.netloc + "/"):
                value = operator.netloc + value[len(substrate.netloc) :]
            query.append((key, value))
        return urllib.parse.urlunsplit(
            (
                operator.scheme,
                operator.netloc,
                internal.path,
                urllib.parse.urlencode(query),
                internal.fragment,
            )
        )

    @property
    def exec_prefix(self) -> tuple[str, ...]:
        if self.network_namespace is None:
            return ()
        return ("/usr/bin/ip", "netns", "exec", self.network_namespace)

    def health(self, *, timeout_seconds: float = 3.0) -> dict:
        token = _token(self.token_file)
        if self.network_namespace is not None:
            url = _append_query(self.http_endpoint + "/active", {"token": token})
            curl_config = f'url = "{url}"\nsilent\nshow-error\nfail\noutput = "/dev/null"\nwrite-out = "%{{http_code}}"\n'
            proc = subprocess.run(
                [*self.exec_prefix, "/usr/bin/curl", "--config", "-"],
                input=curl_config,
                capture_output=True,
                text=True,
                timeout=timeout_seconds + 1,
                check=False,
            )
            try:
                status = int(proc.stdout.strip())
            except ValueError:
                status = 0
            if proc.returncode != 0 or status < 200 or status >= 300:
                return {
                    "id": self.endpoint_id,
                    "healthy": False,
                    "identityDigest": self.identity_digest,
                    "networkNamespace": self.network_namespace,
                    "detail": f"curl-rc-{proc.returncode}",
                }
            return {
                "id": self.endpoint_id,
                "healthy": True,
                "status": status,
                "identityDigest": self.identity_digest,
                "networkNamespace": self.network_namespace,
            }
        url = _append_query(self.http_endpoint + "/active", {"token": token})
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                status = int(response.status)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            return {
                "id": self.endpoint_id,
                "healthy": False,
                "identityDigest": self.identity_digest,
                "detail": type(error).__name__,
            }
        return {
            "id": self.endpoint_id,
            "healthy": 200 <= status < 300,
            "status": status,
            "identityDigest": self.identity_digest,
        }


@dataclass(frozen=True, slots=True)
class BrowserlessPool:
    endpoints: tuple[BrowserlessEndpoint, ...]

    @classmethod
    def from_dict(cls, value: object) -> "BrowserlessPool":
        if not isinstance(value, dict):
            raise BrowserlessConfigError("browserSubstrate must be an object")
        if value.get("kind") != "browserless":
            raise BrowserlessConfigError("browserSubstrate.kind must be browserless")
        raw = value.get("endpoints")
        if not isinstance(raw, list) or not raw:
            raise BrowserlessConfigError("browserSubstrate.endpoints must be non-empty")
        endpoints = tuple(BrowserlessEndpoint.from_dict(row) for row in raw)
        ids = [row.endpoint_id for row in endpoints]
        if len(ids) != len(set(ids)):
            raise BrowserlessConfigError("duplicate Browserless endpoint id")
        return cls(endpoints)

    def candidates(self, stable_key: str) -> tuple[BrowserlessEndpoint, ...]:
        if not stable_key:
            raise BrowserlessConfigError("stable selection key is required")
        seed = int(hashlib.sha256(stable_key.encode()).hexdigest()[:16], 16)
        start = seed % len(self.endpoints)
        return self.endpoints[start:] + self.endpoints[:start]

    def select(self, stable_key: str) -> BrowserlessEndpoint:
        return self.candidates(stable_key)[0]

    def health(self) -> dict:
        rows = [endpoint.health() for endpoint in self.endpoints]
        return {
            "kind": "browserless",
            "healthy": bool(rows) and any(row["healthy"] for row in rows),
            "endpoints": rows,
        }
