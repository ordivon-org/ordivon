#!/usr/bin/env python3
"""Fixed-root OpenTofu controller for the Ordivon Gateway/Agent-Birth Cloudflare overlay."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any

TOFU_RELEASE_ROOT = pathlib.Path(
    "/usr/local/lib/ordivon-operations/cloudflare-provider/handoff-tofu"
)
TOFU_ROOT = TOFU_RELEASE_ROOT / "current"
CLOUDFLARE_CONFIG = pathlib.Path("/root/.config/ordivon/secrets/cloudflare.json")
OPERATIONS_ROOT = pathlib.Path("/var/lib/ordivon/operations-v2/tofu/agent-birth-handoff")
PLAN_DIR = OPERATIONS_ROOT / "plans"
RECEIPT_DIR = OPERATIONS_ROOT / "receipts"
TOFU = pathlib.Path("/usr/bin/tofu")
PLAN_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class HandoffTofuError(RuntimeError):
    pass


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _private_json(path: pathlib.Path) -> dict[str, Any]:
    metadata = path.lstat()
    source = path
    if stat.S_ISLNK(metadata.st_mode):
        parent = path.parent
        parent_mode = stat.S_IMODE(parent.stat().st_mode)
        raw_target = os.readlink(path)
        target_name = pathlib.Path(raw_target)
        if (
            target_name.is_absolute()
            or len(target_name.parts) != 1
            or parent_mode & 0o077
        ):
            raise HandoffTofuError(
                "Cloudflare credential alias must remain inside its private owner directory"
            )
        source = parent / target_name
        metadata = source.lstat()
        if source.is_symlink():
            raise HandoffTofuError("Cloudflare credential alias target must not be another symlink")
    if not stat.S_ISREG(metadata.st_mode):
        raise HandoffTofuError("Cloudflare credential owner must resolve to a regular file")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise HandoffTofuError("Cloudflare credential owner must not be group/world accessible")
    if metadata.st_size > 65536:
        raise HandoffTofuError("Cloudflare credential owner exceeds size bound")
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HandoffTofuError("Cannot read Cloudflare credential owner") from exc
    if not isinstance(value, dict):
        raise HandoffTofuError("Cloudflare credential owner must be a JSON object")
    return value


def cloudflare_environment() -> dict[str, str]:
    config = _private_json(CLOUDFLARE_CONFIG)
    token = config.get("api_token")
    account_id = config.get("account_id")
    if not isinstance(token, str) or not token:
        raise HandoffTofuError("Cloudflare API token is missing")
    if not isinstance(account_id, str) or not account_id:
        raise HandoffTofuError("Cloudflare account ID is missing")
    environment = os.environ.copy()
    environment.update(
        {
            "CLOUDFLARE_API_TOKEN": token,
            "CLOUDFLARE_ACCOUNT_ID": account_id,
            "TF_VAR_account_id": account_id,
            "TF_CLI_CONFIG_FILE": str(TOFU_ROOT / "tofurc"),
            "CI": "true",
        }
    )
    return environment


def _run(
    args: list[str],
    *,
    environment: dict[str, str],
    capture: bool = True,
    accepted: set[int] | None = None,
) -> subprocess.CompletedProcess[str]:
    allowed = accepted or {0}
    completed = subprocess.run(
        [str(TOFU), *args],
        cwd=TOFU_ROOT,
        env=environment,
        text=True,
        check=False,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if completed.returncode not in allowed:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise HandoffTofuError(
            f"OpenTofu failed ({completed.returncode}): {' '.join(args)}"
            + (f"\n{detail}" if detail else "")
        )
    return completed


def _source_identity() -> tuple[str, str]:
    try:
        resolved = TOFU_ROOT.resolve(strict=True)
        releases = (TOFU_RELEASE_ROOT / "releases").resolve(strict=True)
        relative = resolved.relative_to(releases)
    except (OSError, ValueError) as exc:
        raise HandoffTofuError("fixed OpenTofu root is outside the operation release owner") from exc
    if len(relative.parts) != 1 or re.fullmatch(r"[0-9a-f]{40}", relative.name) is None:
        raise HandoffTofuError("fixed OpenTofu release identity is invalid")

    source_files = sorted(TOFU_ROOT.glob("*.tf"), key=lambda path: path.name)
    source_files.extend([TOFU_ROOT / ".terraform.lock.hcl", TOFU_ROOT / "tofurc"])
    if not source_files or not any(path.suffix == ".tf" for path in source_files):
        raise HandoffTofuError("fixed OpenTofu release contains no configuration")

    digest = hashlib.sha256()
    seen: set[str] = set()
    for path in source_files:
        if path.name in seen:
            continue
        seen.add(path.name)
        metadata = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise HandoffTofuError(f"fixed OpenTofu source is not a regular file: {path.name}")
        if stat.S_IMODE(metadata.st_mode) & 0o022:
            raise HandoffTofuError(f"fixed OpenTofu source is group/world writable: {path.name}")
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return relative.name, "sha256:" + digest.hexdigest()


def _summarize_plan(plan: dict[str, Any]) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []
    dangerous: list[dict[str, Any]] = []
    counts = {"create": 0, "update": 0, "delete": 0, "replace": 0, "read": 0, "no_op": 0}
    for resource in plan.get("resource_changes", []):
        if not isinstance(resource, dict):
            continue
        change = resource.get("change")
        if not isinstance(change, dict):
            continue
        actions = [str(action) for action in change.get("actions", [])]
        address = str(resource.get("address", ""))
        item = {"address": address, "actions": actions}
        changes.append(item)
        action_set = set(actions)
        if "delete" in action_set and "create" in action_set:
            counts["replace"] += 1
            dangerous.append(item)
        elif "delete" in action_set:
            counts["delete"] += 1
            dangerous.append(item)
        elif actions == ["create"]:
            counts["create"] += 1
        elif actions == ["update"]:
            counts["update"] += 1
        elif actions == ["read"]:
            counts["read"] += 1
        elif actions == ["no-op"]:
            counts["no_op"] += 1
    output_changes = sorted(
        key for key, value in (plan.get("output_changes") or {}).items() if isinstance(value, dict)
    )
    return {
        "safe_no_delete_replace": not dangerous,
        "counts": counts,
        "changes": changes,
        "dangerous": dangerous,
        "output_changes": output_changes,
    }


def _write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
    os.chmod(path, 0o600)


def _plan_paths(digest: str) -> tuple[pathlib.Path, pathlib.Path]:
    if PLAN_DIGEST_RE.fullmatch(digest) is None:
        raise HandoffTofuError("plan SHA-256 must be 64 lowercase hexadecimal characters")
    return PLAN_DIR / f"{digest}.tfplan", RECEIPT_DIR / f"plan-{digest}.json"


def create_plan() -> dict[str, Any]:
    commit, source_digest = _source_identity()
    environment = cloudflare_environment()
    PLAN_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    _run(["init", "-backend=true", "-input=false", "-lockfile=readonly"], environment=environment)
    fd, temporary_name = tempfile.mkstemp(prefix=".candidate-", suffix=".tfplan", dir=PLAN_DIR)
    os.close(fd)
    temporary = pathlib.Path(temporary_name)
    try:
        completed = _run(
            ["plan", "-input=false", f"-out={temporary}", "-detailed-exitcode"],
            environment=environment,
            accepted={0, 2},
        )
        shown = _run(["show", "-json", str(temporary)], environment=environment)
        try:
            plan_json = json.loads(shown.stdout)
        except json.JSONDecodeError as exc:
            raise HandoffTofuError("OpenTofu show returned invalid JSON") from exc
        summary = _summarize_plan(plan_json)
        digest = _sha256(temporary)
        plan_path, receipt_path = _plan_paths(digest)
        if plan_path.exists():
            if _sha256(plan_path) != digest:
                raise HandoffTofuError("existing plan digest collision")
            temporary.unlink()
        else:
            os.replace(temporary, plan_path)
            os.chmod(plan_path, 0o600)
        receipt = {
            "schema_version": 1,
            "kind": "ordivon.cloudflare-handoff-tofu-plan",
            "created_at": dt.datetime.now(dt.UTC).isoformat(),
            "source_commit": commit,
            "source_digest": source_digest,
            "plan_sha256": digest,
            "plan_path": str(plan_path),
            "tofu_exit_code": completed.returncode,
            "eligible_for_apply": summary["safe_no_delete_replace"],
            "summary": summary,
        }
        _write_json(receipt_path, receipt)
        return receipt
    finally:
        if temporary.exists():
            temporary.unlink()


def load_plan_receipt(digest: str) -> dict[str, Any]:
    plan_path, receipt_path = _plan_paths(digest)
    if not plan_path.is_file() or not receipt_path.is_file():
        raise HandoffTofuError("reviewed plan or receipt does not exist")
    if _sha256(plan_path) != digest:
        raise HandoffTofuError("reviewed plan digest mismatch")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HandoffTofuError("cannot read reviewed plan receipt") from exc
    if not isinstance(receipt, dict) or receipt.get("plan_sha256") != digest:
        raise HandoffTofuError("reviewed plan receipt identity mismatch")
    return receipt


def show_plan(digest: str) -> dict[str, Any]:
    return load_plan_receipt(digest)


def _safe_output(environment: dict[str, str], name: str) -> str | None:
    completed = _run(["output", "-raw", name], environment=environment, accepted={0, 1})
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def apply_reviewed_plan(digest: str) -> dict[str, Any]:
    receipt = load_plan_receipt(digest)
    if receipt.get("eligible_for_apply") is not True:
        raise HandoffTofuError("reviewed plan is not eligible for apply")
    commit, source_digest = _source_identity()
    if receipt.get("source_commit") != commit or receipt.get("source_digest") != source_digest:
        raise HandoffTofuError("fixed OpenTofu source changed after plan")
    plan_path, _ = _plan_paths(digest)
    environment = cloudflare_environment()
    _run(["apply", "-input=false", "-auto-approve", str(plan_path)], environment=environment)
    drift = _run(
        ["plan", "-input=false", "-detailed-exitcode"],
        environment=environment,
        accepted={0, 2},
    )
    if drift.returncode != 0:
        raise HandoffTofuError("post-apply verification detected drift")
    result = {
        "schema_version": 1,
        "kind": "ordivon.cloudflare-handoff-tofu-apply",
        "completed_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_commit": commit,
        "source_digest": source_digest,
        "plan_sha256": digest,
        "status": "applied",
        "zero_drift": True,
        "gateway_mcp_hostname": _safe_output(environment, "gateway_mcp_hostname"),
        "gateway_mcp_audience": _safe_output(environment, "gateway_mcp_audience"),
    }
    _write_json(RECEIPT_DIR / f"apply-{digest}.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ordivon-cloudflare-handoff-tofu")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan")
    show = commands.add_parser("show")
    show.add_argument("--plan-sha256", required=True)
    apply = commands.add_parser("apply-reviewed-plan")
    apply.add_argument("--plan-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            result = create_plan()
        elif args.command == "show":
            result = show_plan(args.plan_sha256)
        elif args.command == "apply-reviewed-plan":
            result = apply_reviewed_plan(args.plan_sha256)
        else:
            raise HandoffTofuError("unsupported operation")
        print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
        return 0
    except HandoffTofuError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
