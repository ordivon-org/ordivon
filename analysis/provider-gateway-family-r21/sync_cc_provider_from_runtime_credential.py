#!/usr/bin/env python3
"""Synchronize one Runtime-owned Provider credential into a CC Switch projection.

Run only through workspace.execCredentialBoundTrusted. Runtime remains credential
authority; CC Switch is a rebuildable projection explicitly requested by the operator.

Secret hygiene:
- plaintext is read only from systemd's CREDENTIALS_DIRECTORY;
- plaintext is written only to one mode-0600 temporary settings_config file;
- plaintext is never placed in process argv, stdout, stderr, Harness state, or Host evidence;
- the temporary file is removed before the Runtime Job returns.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def credential(name: str) -> str:
    directory = os.environ.get("CREDENTIALS_DIRECTORY", "")
    if not directory:
        raise SystemExit("CREDENTIALS_DIRECTORY missing")
    path = Path(directory) / name
    if not path.is_file():
        raise SystemExit("bound credential missing")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise SystemExit("bound credential empty")
    return value


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def toml_string(value: str) -> str:
    # JSON quoted strings are valid TOML basic strings for the values admitted here.
    return json.dumps(value, ensure_ascii=False)


def settings_config(
    *,
    api_key: str,
    provider_name: str,
    base_url: str,
    model: str,
) -> dict[str, object]:
    config = (
        'model_provider = "custom"\n'
        f"model = {toml_string(model)}\n\n"
        "[model_providers.custom]\n"
        f"name = {toml_string(provider_name)}\n"
        f"base_url = {toml_string(base_url)}\n"
        'wire_api = "responses"\n'
    )
    return {
        "auth": {"OPENAI_API_KEY": api_key},
        "config": config,
    }


def add_projection(
    args: argparse.Namespace,
    *,
    provider_id: str,
    api_key: str,
    temporary_root: Path,
) -> None:
    config_path = temporary_root / f"{provider_id}.settings.json"
    config_path.write_text(
        json.dumps(
            settings_config(
                api_key=api_key,
                provider_name=args.name,
                base_url=args.base_url,
                model=args.model,
            ),
            separators=(",", ":"),
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    config_path.chmod(0o600)
    command = [
        args.cc_switch,
        "--app",
        args.app,
        "provider",
        "add",
        "--template",
        "custom",
        "--id",
        provider_id,
        "--name",
        args.name,
        "--config-file",
        str(config_path),
        "--api-format",
        args.api_format,
        "--notes",
        (
            f"Ordivon rebuildable projection; Runtime authority={args.authority_ref}; "
            f"credential={args.credential_name}; no implicit switch."
        ),
    ]
    if api_key in command:
        raise AssertionError("Provider secret must never enter CC Switch argv")
    added = run(command)
    if added.returncode != 0:
        raise SystemExit("CC provider registration failed")


def provider_ids(cc_switch: str, app: str) -> tuple[str | None, str]:
    current = run([cc_switch, "--app", app, "provider", "current"])
    current_id = None
    if current.returncode == 0:
        match = re.search(r"(?m)^\s*ID:\s*(\S+)\s*$", current.stdout)
        current_id = match.group(1) if match else None
    listed = run([cc_switch, "--app", app, "provider", "list"])
    if listed.returncode != 0:
        raise SystemExit("unable to list CC providers")
    return current_id, listed.stdout


def self_test() -> None:
    secret = "self-test-secret-must-not-enter-argv"
    value = settings_config(
        api_key=secret,
        provider_name="Self Test",
        base_url="https://example.invalid/v1",
        model="self-test-model",
    )
    assert value["auth"] == {"OPENAI_API_KEY": secret}
    config = value["config"]
    assert isinstance(config, str)
    assert 'base_url = "https://example.invalid/v1"' in config
    assert 'model = "self-test-model"' in config
    assert secret not in config
    print('{"status":"PASS","kind":"ordivon.cc-provider-secure-sync-self-test"}')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cc-switch", default="/opt/ordivon/native-tools/bin/cc-switch")
    parser.add_argument("--app", default="codex")
    parser.add_argument("--provider-id")
    parser.add_argument("--name")
    parser.add_argument("--base-url")
    parser.add_argument("--model")
    parser.add_argument("--api-format", default="chat")
    parser.add_argument("--authority-ref")
    parser.add_argument("--credential-name", default="api_key")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    required = {
        "--provider-id": args.provider_id,
        "--name": args.name,
        "--base-url": args.base_url,
        "--model": args.model,
        "--authority-ref": args.authority_ref,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        parser.error("missing required arguments: " + ", ".join(missing))
    assert isinstance(args.provider_id, str)
    assert isinstance(args.name, str)
    assert isinstance(args.base_url, str)
    assert isinstance(args.model, str)
    assert isinstance(args.authority_ref, str)

    _current_id, listing = provider_ids(args.cc_switch, args.app)
    if args.provider_id in listing:
        print(
            f"registration=ALREADY_PRESENT providerId={args.provider_id} "
            "credentialRead=false"
        )
        return 0

    key = credential(args.credential_name)
    with tempfile.TemporaryDirectory(prefix="ordivon-cc-provider-sync-") as directory:
        temporary_root = Path(directory)
        temporary_root.chmod(0o700)
        add_projection(
            args,
            provider_id=args.provider_id,
            api_key=key,
            temporary_root=temporary_root,
        )

    key = ""
    print(
        f"registration=CREATED providerId={args.provider_id} "
        f"authority={args.authority_ref} credential={args.credential_name} "
        "secretInArgv=false tempConfigRemoved=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
