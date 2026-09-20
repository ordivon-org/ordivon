#!/usr/bin/env python3
"""Digest-fenced Browserless image promotion transaction.

`plan` is read-only. `apply` is an explicit production mutation boundary and requires a canary PASS
receipt, the exact current installed Quadlet digest, exact source Quadlet digest, and Network-v2
generation. Apply closes Agent Automation admission, requires Temporal/browser quiescence, snapshots
the installed Quadlet, performs staged carrier replacement, and rolls back on any failed health or
post-change Browser Security check.

This tool never pulls images, never visits a protected challenge, and never crosses provider SEND.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SOURCE_REPO = Path("/root/projects/ordivon-harness")
SOURCE_QUADLET = ROOT / "containers/ordivon-browserless@.container"
INSTALLED_QUADLET = Path("/etc/containers/systemd/ordivon-browserless@.container")
AUTOMATION_CONFIG = Path("/etc/ordivon/agent-automation-browserless.json")
SECURITY_ROOT = Path("/root/projects/ordivon-security-v2")
STATE_ROOT = Path("/root/.local/state/ordivon-workstation/agent-automation/state")
PROMOTION_ROOT = STATE_ROOT / "browserless-image-promotions"
PLAYWRIGHT_PYTHON = Path(
    "/root/.local/share/ordivon-workstation/conversation-relay-playwright-r4/.venv/bin/python"
)
INSTANCES = (11, 12, 13)
IMAGE_RE = re.compile(r"^ghcr\.io/browserless/chromium@sha256:[0-9a-f]{64}$")
SHA_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class PromotionError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_digest(value: object, label: str) -> str:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise PromotionError(f"{label} must be one sha256 digest")
    return value


def _image(value: object, label: str = "candidateImage") -> str:
    if not isinstance(value, str) or IMAGE_RE.fullmatch(value) is None:
        raise PromotionError(f"{label} must be exact Browserless OCI digest reference")
    return value


def _source_revision(root: Path = ROOT) -> str:
    proc = subprocess.run(
        ["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    revision = proc.stdout.strip()
    if proc.returncode == 0 and COMMIT_RE.fullmatch(revision):
        return revision
    marker = root / ".ordivon-agent-automation-release.json"
    value = _load_json(marker, "immutable Agent Automation release marker")
    commit = value.get("commit")
    if (
        value.get("schemaVersion") != 1
        or not isinstance(commit, str)
        or COMMIT_RE.fullmatch(commit) is None
    ):
        raise PromotionError("immutable Agent Automation release marker has invalid commit")
    return commit


def _require_canonical_commit(commit: str) -> None:
    proc = subprocess.run(
        [
            "/usr/bin/git",
            "-C",
            str(CANONICAL_SOURCE_REPO),
            "cat-file",
            "-e",
            f"{commit}^{{commit}}",
        ],
        check=False,
        capture_output=True,
        timeout=10,
    )
    if proc.returncode != 0:
        raise PromotionError("promotion source commit is absent from canonical Harness repository")


def _quadlet_non_image_shape(raw: bytes) -> bytes:
    text = raw.decode("utf-8")
    rows = text.splitlines(keepends=True)
    image_rows = [idx for idx, line in enumerate(rows) if line.startswith("Image=")]
    if len(image_rows) != 1:
        raise PromotionError("Quadlet must contain exactly one Image= line")
    idx = image_rows[0]
    newline = "\n" if rows[idx].endswith("\n") else ""
    rows[idx] = "Image=<candidate-image>" + newline
    return "".join(rows).encode("utf-8")


def _quadlet_image(raw: bytes) -> str:
    text = raw.decode("utf-8")
    rows = [line.removeprefix("Image=") for line in text.splitlines() if line.startswith("Image=")]
    if len(rows) != 1:
        raise PromotionError("Quadlet must contain exactly one Image= line")
    return _image(rows[0], "quadlet image")


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PromotionError(f"{label} unavailable: {path}") from error
    if not isinstance(value, dict):
        raise PromotionError(f"{label} must be one JSON object")
    return value


def _render_source_quadlet() -> tuple[bytes, dict[str, Any]]:
    sys.path.insert(0, str(ROOT / "scripts"))
    import browserless_podman_deploy as deploy

    binding = deploy.resolve_network_binding()
    rendered = deploy.render_quadlet(binding).encode("utf-8")
    return rendered, binding


def _load_request(path: Path) -> dict[str, Any]:
    value = _load_json(path, "promotion request")
    expected = {
        "schemaVersion",
        "kind",
        "candidateImage",
        "canaryReceipt",
        "canaryReceiptSha256",
        "expectedInstalledQuadletSha256",
        "expectedSourceQuadletSha256",
        "expectedNetworkGenerationDigest",
        "expectedHarnessCommit",
    }
    if set(value) != expected or value.get("schemaVersion") != 1:
        raise PromotionError("promotion request has unexpected fields/schema")
    if value.get("kind") != "ordivon.browserless-image-promotion-request-r1":
        raise PromotionError("promotion request kind mismatch")
    value["candidateImage"] = _image(value["candidateImage"])
    commit = value.get("expectedHarnessCommit")
    if not isinstance(commit, str) or COMMIT_RE.fullmatch(commit) is None:
        raise PromotionError("expectedHarnessCommit must be one exact Git commit")
    for key in (
        "canaryReceiptSha256",
        "expectedInstalledQuadletSha256",
        "expectedSourceQuadletSha256",
        "expectedNetworkGenerationDigest",
    ):
        value[key] = _safe_digest(value[key], key)
    receipt = value["canaryReceipt"]
    if not isinstance(receipt, str) or not receipt.startswith("/"):
        raise PromotionError("canaryReceipt must be an absolute path")
    return value


def _validate_canary(path: Path, digest: str, candidate: str, control: str) -> dict[str, Any]:
    if not path.is_file() or sha256_file(path) != digest:
        raise PromotionError("canary receipt digest mismatch")
    value = _load_json(path, "canary receipt")
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.browser-security-browserless-canary-r1":
        raise PromotionError("canary receipt kind/schema mismatch")
    if value.get("pass") is not True:
        raise PromotionError("canary receipt is not PASS")
    expected_standing = (
        "PASS_CONTROL_REPRODUCIBLE" if candidate == control else "PASS_EXPECTED_INFRASTRUCTURE_CHANGE"
    )
    if value.get("standing") != expected_standing:
        raise PromotionError("canary standing is incompatible with requested image transition")
    if value.get("candidateImage") != candidate or value.get("controlImage") != control:
        raise PromotionError("canary receipt image binding mismatch")
    if value.get("providerChallengeVisited") is not False or value.get("providerSendAttempted") is not False:
        raise PromotionError("canary receipt crossed forbidden provider boundary")
    if value.get("productionMutationAttempted") is not False or value.get("rootCauseEstablished") is not False:
        raise PromotionError("canary receipt violates qualification boundary")
    return value


def _require_local_image(image: str) -> None:
    if subprocess.run(["/usr/bin/podman", "image", "exists", image], check=False).returncode != 0:
        raise PromotionError("candidate image is not present locally; promotion never pulls")


def _carrier_service_active(instance: int) -> bool:
    return (
        subprocess.run(
            [
                "/usr/bin/systemctl",
                "is-active",
                "--quiet",
                f"ordivon-browserless@{instance}.service",
            ],
            check=False,
        ).returncode
        == 0
    )


def _carrier_container_exists(instance: int) -> bool:
    return (
        subprocess.run(
            [
                "/usr/bin/podman",
                "container",
                "exists",
                f"ordivon-browserless-{instance}",
            ],
            check=False,
        ).returncode
        == 0
    )


def _production_carrier_state() -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for instance in INSTANCES:
        active = _carrier_service_active(instance)
        exists = _carrier_container_exists(instance)
        if active and not exists:
            raise PromotionError(f"active Browserless carrier {instance} has no Podman container")
        if not active and exists:
            raise PromotionError(
                f"inactive Browserless carrier {instance} retains a container; lifecycle state is ambiguous"
            )
        image = _carrier_image(instance) if active else None
        result[instance] = {"active": active, "image": image}
    return result


def _active_instances(state: dict[int, dict[str, Any]]) -> set[int]:
    return {instance for instance, row in state.items() if row.get("active") is True}


def _validate_active_control(
    state: dict[int, dict[str, Any]], expected_image: str, *, label: str
) -> None:
    bad = {
        instance: row.get("image")
        for instance, row in state.items()
        if row.get("active") is True and row.get("image") != expected_image
    }
    if bad:
        raise PromotionError(f"{label} active Browserless carrier image mismatch: {bad}")


def _restore_carrier_topology(
    active_instances: set[int], *, image: str, restart_active: bool
) -> None:
    if not active_instances.issubset(INSTANCES):
        raise PromotionError("saved Browserless lifecycle topology contains an unknown instance")
    for instance in INSTANCES:
        unit = f"ordivon-browserless@{instance}.service"
        if instance in active_instances:
            action = "restart" if restart_active else "start"
            subprocess.run(
                ["/usr/bin/systemctl", action, unit], check=True, timeout=60
            )
            _wait_carrier(instance, image)
        else:
            subprocess.run(
                ["/usr/bin/systemctl", "stop", unit], check=False, timeout=60
            )
    restored = _production_carrier_state()
    if _active_instances(restored) != active_instances:
        raise PromotionError("Browserless lifecycle topology failed to restore")
    _validate_active_control(restored, image, label="restored")


def build_plan(request_path: Path) -> dict[str, Any]:
    request = _load_request(request_path)
    harness_commit = _source_revision(ROOT)
    if harness_commit != request["expectedHarnessCommit"]:
        raise PromotionError("promotion Harness commit changed")
    _require_canonical_commit(harness_commit)
    if not SOURCE_QUADLET.is_file() or not INSTALLED_QUADLET.is_file():
        raise PromotionError("source/installed Browserless Quadlet is unavailable")
    source_digest = sha256_file(SOURCE_QUADLET)
    installed_digest = sha256_file(INSTALLED_QUADLET)
    if source_digest != request["expectedSourceQuadletSha256"]:
        raise PromotionError("source Quadlet digest changed")
    if installed_digest != request["expectedInstalledQuadletSha256"]:
        raise PromotionError("installed Quadlet digest changed")
    source_raw = SOURCE_QUADLET.read_bytes()
    rendered_source_raw, binding = _render_source_quadlet()
    installed_raw = INSTALLED_QUADLET.read_bytes()
    source_image = _quadlet_image(source_raw)
    rendered_source_image = _quadlet_image(rendered_source_raw)
    installed_image = _quadlet_image(installed_raw)
    if source_image != rendered_source_image:
        raise PromotionError("rendered Quadlet changed candidate image identity")
    if _quadlet_non_image_shape(rendered_source_raw) != _quadlet_non_image_shape(installed_raw):
        raise PromotionError(
            "rendered source/installed Quadlet differ outside Image=; image-only promotion refused"
        )
    carrier_state = _production_carrier_state()
    _validate_active_control(carrier_state, installed_image, label="planned")
    active_instances = _active_instances(carrier_state)
    candidate = request["candidateImage"]
    if source_image != candidate:
        raise PromotionError("source Quadlet is not pinned to candidate image")
    generation = binding.get("generationDigest")
    service = binding.get("serviceUnit")
    if generation != request["expectedNetworkGenerationDigest"]:
        raise PromotionError("Network-v2 generation changed")
    if not isinstance(service, str) or not service.endswith((".service", ".target")):
        raise PromotionError("rendered Quadlet has invalid Network-v2 authority service")
    _require_local_image(candidate)
    canary = _validate_canary(
        Path(request["canaryReceipt"]),
        request["canaryReceiptSha256"],
        candidate,
        installed_image,
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browserless-image-promotion-plan-r1",
        "standing": "NOOP_ALREADY_CURRENT" if candidate == installed_image else "READY_TO_APPLY",
        "candidateImage": candidate,
        "controlImage": installed_image,
        "harnessCommit": harness_commit,
        "activeCarrierImages": {
            str(instance): carrier_state[instance]["image"]
            for instance in sorted(active_instances)
        },
        "inactiveCarrierInstances": sorted(set(INSTANCES) - active_instances),
        "sourceQuadletSha256": source_digest,
        "renderedSourceQuadletSha256": "sha256:"
        + hashlib.sha256(rendered_source_raw).hexdigest(),
        "installedQuadletSha256": installed_digest,
        "networkGenerationDigest": generation,
        "networkAuthorityService": service,
        "canaryReceiptSha256": request["canaryReceiptSha256"],
        "canaryStanding": canary["standing"],
        "productionMutationAttempted": False,
        "providerChallengeVisited": False,
        "providerSendAttempted": False,
        "rootCauseEstablished": False,
    }


def _browserless_endpoints() -> list[Any]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from browserless_substrate import BrowserlessPool

    config = _load_json(AUTOMATION_CONFIG, "Browserless config")
    endpoints = BrowserlessPool.from_dict(config.get("browserSubstrate")).endpoints
    by_id = {row.endpoint_id: row for row in endpoints}
    expected = [f"chatgpt-carrier-{n}" for n in INSTANCES]
    if any(key not in by_id for key in expected):
        raise PromotionError("production Browserless endpoint set is incomplete")
    return [by_id[key] for key in expected]


def _require_browser_quiescent(active_instances: set[int] | None = None) -> None:
    if active_instances is None:
        active_instances = _active_instances(_production_carrier_state())
    endpoints = {endpoint.endpoint_id: endpoint for endpoint in _browserless_endpoints()}
    for instance in sorted(active_instances):
        endpoint = endpoints[f"chatgpt-carrier-{instance}"]
        sessions = endpoint.sessions(timeout_seconds=3.0)
        if sessions:
            raise PromotionError(f"Browserless carrier busy: {endpoint.endpoint_id}")


def _carrier_image(instance: int) -> str:
    value = subprocess.run(
        [
            "/usr/bin/podman",
            "inspect",
            f"ordivon-browserless-{instance}",
            "--format",
            "{{.ImageName}}",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    ).stdout.strip()
    return _image(value, f"carrier-{instance} image")


def _wait_carrier(instance: int, candidate: str, timeout_seconds: float = 45.0) -> None:
    endpoint = _browserless_endpoints()[INSTANCES.index(instance)]
    deadline = time.monotonic() + timeout_seconds
    last: Any = None
    while time.monotonic() < deadline:
        active = subprocess.run(
            ["/usr/bin/systemctl", "is-active", "--quiet", f"ordivon-browserless@{instance}.service"],
            check=False,
        ).returncode == 0
        if active:
            try:
                last = endpoint.health(timeout_seconds=2.0)
                if last.get("healthy") is True and _carrier_image(instance) == candidate:
                    return
            except Exception as error:
                last = type(error).__name__
        time.sleep(0.5)
    raise PromotionError(f"carrier {instance} failed candidate health: {last}")


def _atomic_write(path: Path, raw: bytes, mode: int = 0o644) -> None:
    tmp = path.with_name(path.name + ".promotion-tmp")
    tmp.write_bytes(raw)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def validate_post_change_pool(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PromotionError("post-change pool receipt must be one object")
    classification = value.get("classification")
    if not isinstance(classification, dict):
        raise PromotionError("post-change pool receipt lacks classification")
    allowed_infra = {"browserBinary", "controlLayer"}
    shared_infra = set(classification.get("sharedInfrastructureChanges") or [])
    if (
        classification.get("detectorDriftCarriers")
        or classification.get("sharedChangedFamilies")
        or classification.get("carrierLocalChangedFamilies")
        or classification.get("carrierLocalInfrastructureChanges")
        or not shared_infra.issubset(allowed_infra)
        or classification.get("challengeStandingChangedCarriers")
        or classification.get("rootCauseEstablished") is not False
        or value.get("providerChallengeVisited") is not False
        or value.get("providerSendAttempted") is not False
    ):
        raise PromotionError("post-change Browser Security observation exceeded allowed candidate drift")
    return classification


def _transaction_root(candidate: str) -> Path:
    return PROMOTION_ROOT / candidate.rsplit(":", 1)[-1]


def _run_pool_observation(*, candidate: str, phase: str) -> tuple[dict[str, Any], Path]:
    if phase not in {"post-change", "finalize"}:
        raise PromotionError("unsupported promotion pool observation phase")
    transaction_root = _transaction_root(candidate)
    artifact_root = transaction_root / phase
    base = f"browserless-{phase}-{candidate.rsplit(':', 1)[-1][:12]}"
    run_id = base
    generation = 1
    while (artifact_root / run_id).exists():
        generation += 1
        run_id = f"{base}-r{generation}"
    run_root = artifact_root / run_id
    artifact_root.mkdir(parents=True, exist_ok=True)
    os.chmod(transaction_root, 0o700)
    os.chmod(artifact_root, 0o700)
    proc = subprocess.run(
        [
            str(PLAYWRIGHT_PYTHON),
            str(ROOT / "scripts/browser_security_pool_runner.py"),
            "--run-id",
            run_id,
            "--security-root",
            str(SECURITY_ROOT),
            "--artifact-dir",
            str(artifact_root),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=240,
    )
    value = json.loads(proc.stdout)
    if not isinstance(value, dict):
        raise PromotionError(f"promotion {phase} pool runner returned non-object")
    receipt_path = run_root / "pool-run-receipt.json"
    if not receipt_path.is_file():
        raise PromotionError(f"promotion {phase} pool runner did not retain receipt")
    return value, receipt_path


def _post_change_pool_check(candidate: str) -> tuple[dict[str, Any], Path]:
    value, receipt_path = _run_pool_observation(candidate=candidate, phase="post-change")
    validate_post_change_pool(value)
    return value, receipt_path


def _receipt_path(candidate: str) -> Path:
    return _transaction_root(candidate) / "promotion-receipt.json"


def _persist_receipt(candidate: str, value: dict[str, Any]) -> None:
    transaction_root = _transaction_root(candidate)
    transaction_root.mkdir(parents=True, exist_ok=True)
    os.chmod(transaction_root, 0o700)
    raw = json.dumps(value, sort_keys=True, indent=2).encode() + b"\n"
    path = _receipt_path(candidate)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(raw)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _security_clean_revision() -> str:
    status = subprocess.run(
        ["/usr/bin/git", "-C", str(SECURITY_ROOT), "status", "--porcelain=v1"],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    ).stdout
    if status.strip():
        raise PromotionError("Security-v2 repository must be clean before promotion finalize")
    revision = subprocess.run(
        ["/usr/bin/git", "-C", str(SECURITY_ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    ).stdout.strip()
    if COMMIT_RE.fullmatch(revision) is None:
        raise PromotionError("Security-v2 repository has invalid HEAD revision")
    return revision


def validate_finalize_pool(
    value: dict[str, Any],
    *,
    harness_commit: str,
    security_revision: str,
    previous_security_revision: str,
    previous_pool_index_sha256: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PromotionError("finalize pool receipt must be one object")
    classification = value.get("classification")
    if not isinstance(classification, dict):
        raise PromotionError("finalize pool receipt lacks classification")
    if (
        classification.get("standing") != "NO_OBSERVED_DRIFT"
        or classification.get("detectorDriftCarriers")
        or classification.get("sharedChangedFamilies")
        or classification.get("carrierLocalChangedFamilies")
        or classification.get("sharedInfrastructureChanges")
        or classification.get("carrierLocalInfrastructureChanges")
        or classification.get("challengeStandingChangedCarriers")
        or classification.get("rootCauseEstablished") is not False
        or value.get("providerChallengeVisited") is not False
        or value.get("providerSendAttempted") is not False
    ):
        raise PromotionError("finalize requires NO_OBSERVED_DRIFT against resealed Security-v2 LKG")
    if value.get("harnessRevision") != harness_commit:
        raise PromotionError("finalize pool receipt Harness revision mismatch")
    if value.get("securityRevision") != security_revision:
        raise PromotionError("finalize pool receipt Security-v2 revision mismatch")
    if security_revision == previous_security_revision:
        raise PromotionError("Security-v2 revision did not advance for LKG reseal")
    index_sha = value.get("poolIndexSha256")
    if not isinstance(index_sha, str) or SHA_RE.fullmatch(index_sha) is None:
        raise PromotionError("finalize pool receipt lacks valid pool-index digest")
    if index_sha == previous_pool_index_sha256:
        raise PromotionError("Security-v2 pool index did not change for LKG reseal")
    return classification


def _load_applied_receipt(candidate: str, request: dict[str, Any]) -> dict[str, Any]:
    path = _receipt_path(candidate)
    value = _load_json(path, "Browserless image promotion receipt")
    if (
        value.get("schemaVersion") != 1
        or value.get("kind") != "ordivon.browserless-image-promotion-receipt-r1"
        or value.get("standing") != "APPLIED_LKG_RESEAL_REQUIRED"
        or value.get("candidateImage") != candidate
        or value.get("harnessCommit") != request["expectedHarnessCommit"]
        or value.get("productionMutationAttempted") is not True
        or value.get("lkgResealRequired") is not True
    ):
        raise PromotionError("promotion receipt is not awaiting Security-v2 LKG reseal")
    previous_security = value.get("preResealSecurityRevision")
    previous_index = value.get("preResealPoolIndexSha256")
    if not isinstance(previous_security, str) or COMMIT_RE.fullmatch(previous_security) is None:
        raise PromotionError("promotion receipt lacks pre-reseal Security-v2 revision")
    if not isinstance(previous_index, str) or SHA_RE.fullmatch(previous_index) is None:
        raise PromotionError("promotion receipt lacks pre-reseal pool-index digest")
    return value


def apply(request_path: Path) -> dict[str, Any]:
    plan = build_plan(request_path)
    if plan["standing"] == "NOOP_ALREADY_CURRENT":
        value = dict(plan)
        value["kind"] = "ordivon.browserless-image-promotion-receipt-r1"
        value["standing"] = "NOOP_ALREADY_CURRENT"
        _persist_receipt(plan["candidateImage"], value)
        return value

    sys.path.insert(0, str(ROOT / "scripts"))
    import agent_automation_release as release

    candidate = plan["candidateImage"]
    commit = plan["harnessCommit"]
    installed_before = INSTALLED_QUADLET.read_bytes()
    installed_before_digest = sha256_file(INSTALLED_QUADLET)
    rendered_source_raw, current_binding = _render_source_quadlet()
    rendered_digest = "sha256:" + hashlib.sha256(rendered_source_raw).hexdigest()
    if rendered_digest != plan["renderedSourceQuadletSha256"]:
        raise PromotionError("rendered source Quadlet changed after promotion planning")
    if current_binding.get("generationDigest") != plan["networkGenerationDigest"]:
        raise PromotionError("Network-v2 generation changed after promotion planning")
    backup_path = _transaction_root(candidate) / "rollback.quadlet"
    mutation_started = False
    restarted: list[int] = []

    with release.release_admission_fence(commit) as admission_was_closed:
        mcp_was_active = release.active(release.MCP_UNIT)
        if not admission_was_closed and not mcp_was_active:
            release._restore_admission_gate(admission_was_closed)
            raise PromotionError("Agent Automation MCP must be active before a new promotion transaction")
        try:
            if mcp_was_active:
                release.run(["/usr/bin/systemctl", "stop", release.MCP_UNIT], timeout=30)
            running = release.running_workflows()
            if running:
                value = dict(plan)
                value.update(
                    {
                        "kind": "ordivon.browserless-image-promotion-receipt-r1",
                        "standing": "HOLD_DRAINING",
                        "runningWorkflowCount": len(running),
                        "mcpAdmissionClosed": True,
                        "cliAdmissionClosed": True,
                        "productionMutationAttempted": False,
                    }
                )
                _persist_receipt(candidate, value)
                return value

            pre_state = _production_carrier_state()
            _validate_active_control(pre_state, plan["controlImage"], label="pre-apply")
            pre_active_instances = _active_instances(pre_state)
            _require_browser_quiescent(pre_active_instances)

            transaction_root = _transaction_root(candidate)
            transaction_root.mkdir(parents=True, exist_ok=True)
            os.chmod(transaction_root, 0o700)
            backup_path.write_bytes(installed_before)
            os.chmod(backup_path, 0o600)
            _atomic_write(INSTALLED_QUADLET, rendered_source_raw)
            mutation_started = True
            subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=True, timeout=30)
            for instance in INSTANCES:
                subprocess.run(
                    ["/usr/bin/systemctl", "restart", f"ordivon-browserless@{instance}.service"],
                    check=True,
                    timeout=60,
                )
                restarted.append(instance)
                _wait_carrier(instance, candidate)
            post, post_receipt_path = _post_change_pool_check(candidate)
            classification = validate_post_change_pool(post)
            value = dict(plan)
            value.update(
                {
                    "kind": "ordivon.browserless-image-promotion-receipt-r1",
                    "standing": "APPLIED_LKG_RESEAL_REQUIRED",
                    "productionMutationAttempted": True,
                    "restartedInstances": restarted,
                    "prePromotionActiveInstances": sorted(pre_active_instances),
                    "prePromotionInactiveInstances": sorted(set(INSTANCES) - pre_active_instances),
                    "installedQuadletBeforeSha256": installed_before_digest,
                    "installedQuadletAfterSha256": sha256_file(INSTALLED_QUADLET),
                    "rollbackSnapshot": str(backup_path),
                    "postChangePoolStanding": classification["standing"],
                    "postChangeSharedInfrastructureChanges": classification.get(
                        "sharedInfrastructureChanges", []
                    ),
                    "postChangeArtifactRoot": str(post_receipt_path.parent),
                    "postChangePoolReceiptSha256": sha256_file(post_receipt_path),
                    "preResealSecurityRevision": post.get("securityRevision"),
                    "preResealPoolIndexSha256": post.get("poolIndexSha256"),
                    "lkgResealRequired": True,
                    "mcpAdmissionClosed": True,
                    "cliAdmissionClosed": True,
                }
            )
            _persist_receipt(candidate, value)
            return value
        except Exception as error:
            if mutation_started:
                _atomic_write(INSTALLED_QUADLET, installed_before)
                subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=False, timeout=30)
                try:
                    _restore_carrier_topology(
                        pre_active_instances,
                        image=plan["controlImage"],
                        restart_active=True,
                    )
                except Exception:
                    # Preserve the original promotion failure while keeping admission fail-closed.
                    pass
            value = dict(plan)
            value.update(
                {
                    "kind": "ordivon.browserless-image-promotion-receipt-r1",
                    "standing": "ROLLED_BACK" if mutation_started else "HOLD_PRE_MUTATION",
                    "productionMutationAttempted": mutation_started,
                    "rollbackRestored": mutation_started,
                    "detail": f"{type(error).__name__}: {error}",
                }
            )
            _persist_receipt(candidate, value)
            if mcp_was_active and not release.active(release.MCP_UNIT):
                release.run(
                    ["/usr/bin/systemctl", "start", release.MCP_UNIT],
                    check=False,
                    timeout=30,
                )
            release._restore_admission_gate(admission_was_closed)
            raise


def finalize(request_path: Path) -> dict[str, Any]:
    request = _load_request(request_path)
    candidate = request["candidateImage"]
    commit = _source_revision(ROOT)
    if commit != request["expectedHarnessCommit"]:
        raise PromotionError("promotion Harness commit changed before finalize")
    _require_canonical_commit(commit)
    applied = _load_applied_receipt(candidate, request)

    rendered_source_raw, binding = _render_source_quadlet()
    if _quadlet_image(rendered_source_raw) != candidate:
        raise PromotionError("rendered source Quadlet no longer pins finalized candidate")
    if not INSTALLED_QUADLET.is_file() or INSTALLED_QUADLET.read_bytes() != rendered_source_raw:
        raise PromotionError("installed Quadlet does not equal rendered candidate before finalize")
    if binding.get("generationDigest") != request["expectedNetworkGenerationDigest"]:
        raise PromotionError("Network-v2 generation changed before finalize")
    finalize_state = _production_carrier_state()
    if _active_instances(finalize_state) != set(INSTANCES):
        raise PromotionError("promotion finalize requires all candidate carriers retained active")
    _validate_active_control(finalize_state, candidate, label="finalize")

    security_revision = _security_clean_revision()
    previous_security = applied["preResealSecurityRevision"]
    previous_index = applied["preResealPoolIndexSha256"]
    if security_revision == previous_security:
        raise PromotionError("Security-v2 LKG reseal has not advanced repository revision")

    sys.path.insert(0, str(ROOT / "scripts"))
    import agent_automation_release as release

    with release.release_admission_fence(commit) as admission_was_closed:
        if not admission_was_closed:
            release._restore_admission_gate(False)
            raise PromotionError("finalize requires the admission gate retained by promotion apply")
        if release.active(release.MCP_UNIT):
            raise PromotionError("Agent Automation MCP must remain stopped until promotion finalize")
        if not release.active(release.WORKER_UNIT):
            raise PromotionError("Agent Automation worker must remain active for drain continuity")
        if release.running_workflows():
            raise PromotionError("Temporal workflows remain active during promotion finalize")
        _require_browser_quiescent(set(INSTANCES))

        final_pool, final_receipt_path = _run_pool_observation(
            candidate=candidate, phase="finalize"
        )
        classification = validate_finalize_pool(
            final_pool,
            harness_commit=commit,
            security_revision=security_revision,
            previous_security_revision=previous_security,
            previous_pool_index_sha256=previous_index,
        )

        saved_active_raw = applied.get("prePromotionActiveInstances")
        if (
            not isinstance(saved_active_raw, list)
            or any(not isinstance(value, int) for value in saved_active_raw)
            or not set(saved_active_raw).issubset(INSTANCES)
        ):
            raise PromotionError("promotion receipt lacks valid pre-promotion lifecycle topology")
        saved_active = set(saved_active_raw)

        started_mcp = False
        try:
            _restore_carrier_topology(saved_active, image=candidate, restart_active=False)
            release.run(["/usr/bin/systemctl", "start", release.MCP_UNIT], timeout=30)
            started_mcp = True
            if not release.active(release.MCP_UNIT):
                raise PromotionError("Agent Automation MCP failed to become active during finalize")
            if release.running_workflows():
                raise PromotionError("new Workflow appeared while admission gate remained closed")
            value = dict(applied)
            value.update(
                {
                    "standing": "ACTIVE",
                    "lkgResealRequired": False,
                    "finalSecurityRevision": security_revision,
                    "finalPoolIndexSha256": final_pool["poolIndexSha256"],
                    "finalPoolStanding": classification["standing"],
                    "finalizeArtifactRoot": str(final_receipt_path.parent),
                    "finalizePoolReceiptSha256": sha256_file(final_receipt_path),
                    "restoredActiveInstances": sorted(saved_active),
                    "restoredInactiveInstances": sorted(set(INSTANCES) - saved_active),
                    "mcpAdmissionClosed": False,
                    "cliAdmissionClosed": False,
                }
            )
            _persist_receipt(candidate, value)
            release.ADMISSION_CLOSED.unlink(missing_ok=True)
            return value
        except Exception:
            if started_mcp and release.active(release.MCP_UNIT):
                release.run(
                    ["/usr/bin/systemctl", "stop", release.MCP_UNIT],
                    check=False,
                    timeout=30,
                )
            raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--apply", action="store_true")
    actions.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    result = (
        finalize(args.request)
        if args.finalize
        else (apply(args.request) if args.apply else build_plan(args.request))
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
