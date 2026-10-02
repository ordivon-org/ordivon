#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

EXPECTED_BINARY_SHA256 = "3b4e967ea8e156b57e684555bab8fc80f1f442fcbbf13a7864e633d5bddc37bf"
LOCAL_ACCESS_KEY = "ordivon-local-canary"
DEFAULT_BINARY = "/tmp/ordivon-cliproxyapi-v8.0.10-r1"
DEFAULT_NETWORK_PROXY = "http://127.0.0.1:19881"
DEFAULT_PORT = 18318
UPSTREAM_MODEL = "openrouter/free"
CLIENT_MODEL = "ordivon-canary"
MARKER = "ORDIVON_GATEWAY_CANARY_OK"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def http_json(
    url: str,
    *,
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 20.0,
) -> tuple[int, dict]:
    data = None
    request_headers = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            return int(response.status), json.loads(body)
    except urllib.error.HTTPError as error:
        # Never emit the upstream body: it may contain sensitive diagnostics.
        return int(error.code), {}
    except urllib.error.URLError:
        # Startup and bounded transport probes treat not-yet-listening / transient
        # connect failures as no response; the caller owns the retry bound.
        return 0, {}


def extract_upstream_key(raw: str) -> tuple[str, str]:
    text = raw.strip()
    try:
        value = json.loads(text)
    except Exception:
        return text, "raw"
    if isinstance(value, str):
        return value.strip(), "json-string"
    if isinstance(value, dict):
        for name in ("api_key", "apiKey", "OPENROUTER_API_KEY", "key", "token"):
            candidate = value.get(name)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip(), f"json-field:{name}"
    return text, "raw"


def external_auth_status(key: str, proxy: str) -> int:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({"https": proxy}))
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/auth/key",
        headers={"Authorization": f"Bearer {key}"},
    )
    try:
        with opener.open(request, timeout=20.0) as response:
            response.read()
            return int(response.status)
    except urllib.error.HTTPError as error:
        return int(error.code)
    except urllib.error.URLError:
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", default=DEFAULT_BINARY)
    parser.add_argument("--network-proxy", default=DEFAULT_NETWORK_PROXY)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    binary = Path(args.binary)
    if not binary.is_file():
        raise SystemExit("CLIProxyAPI binary missing")
    actual_binary_sha = sha256_file(binary)
    if actual_binary_sha != EXPECTED_BINARY_SHA256:
        raise SystemExit("CLIProxyAPI binary digest mismatch")

    credential_dir_raw = os.environ.get("CREDENTIALS_DIRECTORY", "")
    if not credential_dir_raw:
        raise SystemExit("CREDENTIALS_DIRECTORY missing")
    credential_file = Path(credential_dir_raw) / "api_key"
    if not credential_file.is_file():
        raise SystemExit("Runtime-delivered api_key missing")

    # Credential bytes are consumed only to build the process-local temporary
    # gateway config. They are never printed, hashed, returned, or persisted.
    upstream_key, credential_encoding = extract_upstream_key(
        credential_file.read_text(encoding="utf-8")
    )
    if not upstream_key:
        raise SystemExit("Runtime-delivered api_key empty")
    direct_auth_status = external_auth_status(upstream_key, args.network_proxy)

    temp_root = Path(tempfile.mkdtemp(prefix="ordivon-cpa-openrouter-canary-"))
    proc: subprocess.Popen[bytes] | None = None
    standing = "FAIL"
    http_status = 0
    response_model = None
    marker_match = False
    content_length = 0
    prompt_tokens = None
    completion_tokens = None
    failure_class = None

    try:
        auth_dir = temp_root / "auth"
        auth_dir.mkdir(mode=0o700)
        config_path = temp_root / "config.yaml"
        server_out = (temp_root / "server.out").open("wb")
        server_err = (temp_root / "server.err").open("wb")
        key_yaml = json.dumps(upstream_key)
        config = f"""server:
  host: "127.0.0.1"
  port: {args.port}
management:
  allow-remote: false
  secret-key: ""
  disable-control-panel: true
access:
  api-keys:
    - "{LOCAL_ACCESS_KEY}"
routing:
  strategy: "fill-first"
  session-affinity: false
  retry:
    request-retry: 0
    max-retry-credentials: 1
    max-retry-interval: 0
  cooldown:
    disable-cooling: true
    save-cooldown-status: false
requests:
  proxy-url: "{args.network_proxy}"
  passthrough-headers: false
api-keys:
  openai-compatibility:
    - name: "openrouter"
      prefix: "or"
      base-url: "https://openrouter.ai/api/v1"
      request-retry: 0
      keys:
        - api-key: {key_yaml}
          proxy-url: "{args.network_proxy}"
      models:
        - name: "{UPSTREAM_MODEL}"
          alias: "{CLIENT_MODEL}"
          input-modalities: [text]
          output-modalities: [text]
oauth:
  auth-dir: "{auth_dir}"
observability:
  logs:
    debug: false
"""
        config_path.write_text(config, encoding="utf-8")
        config_path.chmod(0o600)

        proc = subprocess.Popen(
            [str(binary), "-config", str(config_path), "-local-model"],
            stdout=server_out,
            stderr=server_err,
            start_new_session=True,
        )

        models_url = f"http://127.0.0.1:{args.port}/v1/models"
        client_headers = {"Authorization": f"Bearer {LOCAL_ACCESS_KEY}"}
        ready = False
        for _ in range(100):
            if proc.poll() is not None:
                break
            status, models = http_json(models_url, headers=client_headers, timeout=1.0)
            if status == 200:
                ids = [
                    item.get("id")
                    for item in models.get("data", [])
                    if isinstance(item, dict)
                ]
                if CLIENT_MODEL in ids or f"or/{CLIENT_MODEL}" in ids:
                    ready = True
                    break
            time.sleep(0.1)
        if not ready:
            failure_class = "gateway_not_ready"
        else:
            chat_url = f"http://127.0.0.1:{args.port}/v1/chat/completions"
            http_status, response = http_json(
                chat_url,
                headers=client_headers,
                payload={
                    "model": CLIENT_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Reply with exactly {MARKER}.",
                        }
                    ],
                    "temperature": 0,
                    "max_tokens": 32,
                    "stream": False,
                },
                timeout=60.0,
            )
            if http_status == 200:
                response_model = response.get("model")
                choices = response.get("choices") or []
                content = ""
                if choices and isinstance(choices[0], dict):
                    message = choices[0].get("message") or {}
                    if isinstance(message, dict):
                        content = str(message.get("content") or "")
                content_length = len(content)
                marker_match = content.strip() == MARKER
                usage = response.get("usage") or {}
                if isinstance(usage, dict):
                    prompt_tokens = usage.get("prompt_tokens")
                    completion_tokens = usage.get("completion_tokens")
                standing = "PASS" if content_length > 0 else "FAIL"
                if standing != "PASS":
                    failure_class = "empty_completion"
            else:
                failure_class = f"gateway_http_{http_status}"
    except Exception as error:
        failure_class = type(error).__name__
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        try:
            server_out.close()
            server_err.close()
        except Exception:
            pass
        upstream_key = ""
        shutil.rmtree(temp_root, ignore_errors=True)

    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.research.gateway-live-canary",
        "standing": standing,
        "gateway": {
            "implementation": "CLIProxyAPI",
            "sourceRevision": "6fecc6e5567912661654a4eaf9b8f5436facd1c2",
            "tag": "v8.0.10",
            "binarySha256": f"sha256:{actual_binary_sha}",
            "endpoint": f"http://127.0.0.1:{args.port}",
            "retryRounds": 0,
        },
        "runtimeCredential": {
            "authority": "openrouter-provider",
            "name": "api_key",
            "encodingClass": credential_encoding,
            "directAuthPreflightStatus": direct_auth_status,
            "plaintextExposedInReceipt": False,
            "gatewayDurableSecretPersistence": False,
        },
        "network": {
            "authority": "network-v2:model-provider",
            "proxy": args.network_proxy,
            "directFallback": False,
        },
        "request": {
            "provider": "openrouter",
            "clientModel": CLIENT_MODEL,
            "upstreamModel": UPSTREAM_MODEL,
            "stream": False,
        },
        "observation": {
            "httpStatus": http_status,
            "effectiveModel": response_model,
            "assistantContentLength": content_length,
            "markerMatch": marker_match,
            "promptTokens": prompt_tokens,
            "completionTokens": completion_tokens,
            "failureClass": failure_class,
        },
        "cleanup": {
            "temporaryDirectoryRemoved": not temp_root.exists(),
        },
    }
    print(json.dumps(receipt, sort_keys=True))
    return 0 if standing == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
