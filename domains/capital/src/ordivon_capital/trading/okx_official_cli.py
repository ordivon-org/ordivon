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
    and no new OMS. Credentials are projected only into a private ephemeral
    config file under tmpfs for the child process, never into argv or env.
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
        if site not in ("global", "eea", "us", "tr"):
            raise OkxDemoError("OKX account site must be explicit supported site")
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
            root = Path(home)
            directory = root / ".okx"
            directory.mkdir(mode=0o700)
            # TOML basic quoted strings accept JSON escapes; secrets are never echoed.
            config = (
                "default_profile = \"ordivon-demo\"\n"
                "[profiles.ordivon-demo]\n"
                "demo = true\n"
                f"site = {json.dumps(self._site)}\n"
                f"api_key = {json.dumps(self._credentials.api_key)}\n"
                f"secret_key = {json.dumps(self._credentials.secret_key)}\n"
                f"passphrase = {json.dumps(self._credentials.passphrase)}\n"
            )
            if self._credentials.api_key == "" or self._credentials.secret_key == "" or self._credentials.passphrase == "":
                raise OkxDemoError("Demo credentials missing")
            cfg = directory / "config.toml"
            cfg.write_text(config, encoding="utf-8")
            cfg.chmod(0o600)

            env = {k: v for k, v in os.environ.items() if not k.startswith("OKX_")}
            env["HOME"] = home
            env["OKX_DEMO"] = "1"
            env["OKX_SITE"] = self._site
            env["OKX_API_BASE_URL"] = self._base_url
            # Upstream respects standard HTTPS_PROXY/ALL_PROXY from Ordivon Network.
            # Its own TOML profile owns optional explicit proxy_url, not secrets.
            if self._official_proxy_url():
                cfg.write_text(config + f"proxy_url = {json.dumps(self._official_proxy_url())}\n", encoding="utf-8")
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
