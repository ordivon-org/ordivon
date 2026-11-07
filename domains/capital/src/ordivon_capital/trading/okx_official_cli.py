"""Exact-version official OKX Agent Trade Kit 1.5.0 transport for the Trading owner.

The upstream CLI supplies network, provider auth, signing and REST mechanics.
The existing Ordivon client supplies provider identity/effect semantics; the
Trading PostgreSQL intent/claim source remains the only order effect authority.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ordivon_capital.trading.okx_demo_execution import (
    OkxDemoEffectUnknown,
    OkxDemoError,
    OkxSpotDemoClient,
)
from ordivon_capital.trading.okx_readonly_client import OkxReadOnlyCredentials

_CLI_PROJECT = Path(__file__).resolve().parents[3] / "tools/okx_official_cli"
_CLI_VERSION = "1.5.0"


class OkxOfficialSpotDemoClient(OkxSpotDemoClient):
    """Thin upstream provider transport, preserving bounded Demo order semantics.

    No shell, no ad-hoc HMAC or HTTP implementation, no shared OKX profile,
    and no new OMS. CredentialAuthority supplies the one child process with
    ephemeral environment values (upstream CLI's supported native interface).
    Secrets are never serialized to TOML, argv or a persistent location.
    """

    def __init__(
        self,
        credentials: OkxReadOnlyCredentials,
        *,
        base_url: str = "https://www.okx.com",
        proxy_url: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        super().__init__(
            credentials, base_url=base_url, proxy_url=proxy_url,
            timeout_seconds=timeout_seconds,
        )
        package = _CLI_PROJECT / "node_modules/@okx_ai/okx-trade-cli/package.json"
        script = _CLI_PROJECT / "node_modules/@okx_ai/okx-trade-cli/dist/index.js"
        if not package.is_file() or not script.is_file():
            raise OkxDemoError("pinned OKX official CLI not installed (mise run provider:okx:install)")
        try:
            installed = json.loads(package.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OkxDemoError("unreadable upstream package identity") from exc
        if installed.get("name") != "@okx_ai/okx-trade-cli" or installed.get("version") != _CLI_VERSION:
            raise OkxDemoError("official CLI version differs from exact qualified 1.5.0")
        node = shutil.which("node")
        if node is None:
            raise OkxDemoError("Node.js runtime not available")
        self._node = node
        self._script = script
        self._official_proxy = proxy_url
        site = os.environ.get("ORDIVON_OKX_SITE", "global")
        official_origins = {
            "global": "https://www.okx.com",
            "eea": "https://eea.okx.com",
            "us": "https://us.okx.com",
            "tr": "https://tr.okx.com",
        }
        if site not in official_origins:
            raise OkxDemoError("OKX account site must be explicit supported site")
        official_origin = official_origins[site]
        if base_url != "https://www.okx.com" and base_url != official_origin:
            raise OkxDemoError("OKX account region and API origin mismatch")
        self._base_url = official_origin
        self._site = site

    @staticmethod
    def _route(
        method: str, path: str, query: dict[str, str] | None,
        body: dict[str, str] | None,
    ) -> list[str]:
        q, b = query or {}, body or {}
        if method == "GET" and path == "/api/v5/account/config" and not q:
            return ["account", "config"]
        if method == "GET" and path == "/api/v5/account/balance" and not q:
            return ["account", "balance"]
        if method == "GET" and path == "/api/v5/trade/order":
            if q.get("instId") and len(q) == 2 and bool(q.get("ordId")) != bool(q.get("clOrdId")):
                key = "ordId" if "ordId" in q else "clOrdId"
                return ["spot", "get", "--instId", q["instId"], "--" + key, q[key]]
        if method == "GET" and path == "/api/v5/trade/fills":
            if set(q) == {"instType", "instId", "ordId"} and q["instType"] == "SPOT":
                return ["spot", "fills", "--instId", q["instId"], "--ordId", q["ordId"]]
        if method == "POST" and path == "/api/v5/trade/order":
            if set(b) == {"instId", "tdMode", "side", "ordType", "sz", "px", "clOrdId"} and b["tdMode"] == "cash" and b["ordType"] == "limit":
                return [
                    "spot", "place", "--instId", b["instId"],
                    "--tdMode", "cash", "--side", b["side"], "--ordType", "limit",
                    "--sz", b["sz"], "--px", b["px"], "--clOrdId", b["clOrdId"],
                ]
        if method == "POST" and path == "/api/v5/trade/cancel-order":
            if set(b) == {"instId", "ordId"}:
                return ["spot", "cancel", b["instId"], "--ordId", b["ordId"]]
        raise ValueError("upstream CLI route outside admitted Demo order contract")

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        args = self._route(method, path, query, body)
        ram = "/dev/shm" if os.path.isdir("/dev/shm") and os.access("/dev/shm", os.W_OK) else None
        with tempfile.TemporaryDirectory(prefix="ordivon-okx-official-demo-", dir=ram) as home:
            if not all((
                self._credentials.api_key,
                self._credentials.secret_key,
                self._credentials.passphrase,
            )):
                raise OkxDemoError("Demo credentials missing")

            # The official upstream loader accepts an environment credential
            # tuple. Limit it to this subprocess: no TOML file, no mutation of
            # os.environ, no API secret in arguments or exception messages.
            env = {k: v for k, v in os.environ.items() if not k.startswith("OKX_")}
            env["HOME"] = home
            env["OKX_API_KEY"] = self._credentials.api_key
            env["OKX_SECRET_KEY"] = self._credentials.secret_key
            env["OKX_PASSPHRASE"] = self._credentials.passphrase
            env["OKX_DEMO"] = "1"
            env["OKX_SITE"] = self._site
            env["OKX_API_BASE_URL"] = self._base_url
            if self._official_proxy_url() is not None:
                # The official CLI uses Undici's standard proxy environment
                # support. Leave network-owned defaults in place otherwise.
                env["HTTPS_PROXY"] = self._official_proxy_url()
                env["https_proxy"] = self._official_proxy_url()
            command = [
                self._node, str(self._script), "--demo", "--json", "--env",
                "--profile", "ordivon-demo", *args,
            ]
            try:
                completed = subprocess.run(
                    command,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout_seconds + 10.0,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                if method == "POST":
                    raise OkxDemoEffectUnknown("official CLI POST effect UNKNOWN") from exc
                raise OkxDemoError("official CLI GET failed without provider observation") from exc

        try:
            payload = json.loads(completed.stdout)
        except (TypeError, ValueError):
            payload = None
        valid = (
            isinstance(payload, dict)
            and payload.get("env") == "demo"
            and payload.get("profile") == "ordivon-demo"
            and isinstance(payload.get("data"), list)
            and all(isinstance(x, dict) for x in payload["data"])
        )
        rows: list[dict[str, Any]] = payload["data"] if valid else []
        if completed.returncode != 0 or not valid:
            if method == "GET":
                if path == "/api/v5/trade/order" and "51603" in completed.stderr:
                    return []  # No immediate match is not proof of no effect.
                raise OkxDemoError("official CLI GET lacked verified Demo provider result")
            # A business sCode is explicit evidence of rejection; other failures
            # mean the request MAY HAVE reached the venue. Never retry a POST.
            if valid and len(rows) == 1 and rows[0].get("sCode") not in ("0", 0, None):
                raise OkxDemoError("official Demo provider rejected command")
            raise OkxDemoEffectUnknown("official CLI POST outcome UNKNOWN")
        return rows

    def _official_proxy_url(self) -> str | None:
        # The canonical parent validates this argument against HTTP(S) URLs.
        # Child subprocess has its own fresh profile and can consume the same
        # explicit Ordivon Network proxy if supplied by the caller.
        return getattr(self, "_official_proxy", None)
