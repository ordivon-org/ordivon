#!/usr/bin/env python3
"""Collect the Browserless carrier pool and classify drift against per-carrier LKGs.

Harness owns neutral browser observation. Security-v2 owns canonicalization and drift classification.
This runner does not visit ChatGPT, inspect a provider challenge, or cross SEND.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HARNESS_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SECURITY_ROOT = Path("/root/projects/ordivon-security-v2")
DEFAULT_POOL_INDEX = Path("fixtures/browser-security/harness-r2-live-lkg-pool-index.json")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_id(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise ValueError(f"{label} must match the bounded safe identifier syntax")
    return value


def _inside(root: Path, value: Path) -> Path:
    root = root.resolve()
    resolved = value.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"path escapes configured root: {value}") from error
    return resolved


def _load_pool_index(index_path: Path, security_root: Path) -> dict[str, Any]:
    value = json.loads(index_path.read_text(encoding="utf-8"))
    required = {"schemaVersion", "kind", "poolId", "standing", "comparisonLaw", "carriers"}
    if not isinstance(value, dict) or not required.issubset(value):
        raise ValueError("pool LKG index is missing required fields")
    if value["schemaVersion"] != 1 or value["kind"] != "ordivon.browser-security-pool-lkg-index":
        raise ValueError("unsupported pool LKG index")
    if value["standing"] != "LKG_PER_CARRIER":
        raise ValueError("pool index must be an LKG_PER_CARRIER baseline")
    law = value["comparisonLaw"]
    if not isinstance(law, dict) or law.get("sameCarrierCandidateVsSameCarrierLkg") != "ALLOWED":
        raise ValueError("pool index does not authorize same-carrier LKG comparison")
    rows = value["carriers"]
    if not isinstance(rows, list) or len(rows) < 2:
        raise ValueError("pool LKG index requires at least two carriers")

    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("pool carrier row must be an object")
        carrier_id = _safe_id(row.get("carrierId"), "carrierId")
        if carrier_id in seen:
            raise ValueError(f"duplicate carrierId in pool index: {carrier_id}")
        seen.add(carrier_id)
        bundle_ref = row.get("bundle")
        bundle_digest = row.get("bundleSha256")
        if not isinstance(bundle_ref, str) or not bundle_ref:
            raise ValueError(f"baseline bundle path missing for {carrier_id}")
        if not isinstance(bundle_digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", bundle_digest):
            raise ValueError(f"baseline bundle digest invalid for {carrier_id}")
        candidate = Path(bundle_ref)
        if not candidate.is_absolute():
            candidate = security_root / candidate
        baseline_bundle = _inside(security_root, candidate)
        if not baseline_bundle.is_file():
            raise ValueError(f"baseline bundle missing for {carrier_id}")
        actual = _sha256(baseline_bundle)
        if actual != bundle_digest:
            raise ValueError(f"baseline bundle digest mismatch for {carrier_id}")
        normalized.append(
            {
                "carrierId": carrier_id,
                "baselineBundle": baseline_bundle,
                "baselineBundleSha256": actual,
            }
        )
    return {
        "poolId": _safe_id(value["poolId"], "poolId"),
        "indexSha256": _sha256(index_path),
        "carriers": normalized,
    }


def _run_checked(args: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(args, check=True, env=env)


def _collect_carrier(
    *, carrier_id: str, witness_id: str, output: Path, python: str
) -> None:
    env = {**os.environ, "PYTHONPATH": str(HARNESS_ROOT)}
    _run_checked(
        [
            python,
            str(HARNESS_ROOT / "scripts/browser_security_witness_source.py"),
            "--endpoint-id",
            carrier_id,
            "--witness-id",
            witness_id,
            "--output",
            str(output),
        ],
        env=env,
    )


def _build_bundle(*, manifest: Path, output: Path, security_root: Path, python: str) -> None:
    env = {**os.environ, "PYTHONPATH": str(security_root / "src")}
    _run_checked(
        [
            python,
            str(security_root / "scripts/build_browser_security_witness.py"),
            str(manifest),
            "--output",
            str(output),
        ],
        env=env,
    )


def _compare_pool(*, manifest: Path, security_root: Path, python: str) -> dict[str, Any]:
    env = {**os.environ, "PYTHONPATH": str(security_root / "src")}
    proc = subprocess.run(
        [python, str(security_root / "scripts/compare_browser_security_pool.py"), str(manifest)],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )
    value = json.loads(proc.stdout)
    if not isinstance(value, dict) or value.get("rootCauseEstablished") is not False:
        raise RuntimeError("Security-v2 returned an invalid pool drift classification")
    return value


def _source_revision(root: Path) -> str:
    proc = subprocess.run(
        ["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    revision = proc.stdout.strip()
    if proc.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", revision):
        return revision
    marker = root / ".ordivon-agent-automation-release.json"
    try:
        value = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"source revision unavailable for {root}") from error
    commit = value.get("commit") if isinstance(value, dict) else None
    if (
        not isinstance(value, dict)
        or value.get("schemaVersion") != 1
        or not isinstance(commit, str)
        or not re.fullmatch(r"[0-9a-f]{40}", commit)
    ):
        raise RuntimeError(f"immutable release marker is invalid for {root}")
    return commit


def _run_into(
    *,
    run_root: Path,
    run_id: str,
    security_root: Path,
    pool_index: Path,
    python: str,
) -> dict[str, Any]:
    baseline = _load_pool_index(pool_index, security_root)
    rows: list[dict[str, str]] = []
    evidence: list[dict[str, str]] = []

    for row in baseline["carriers"]:
        carrier_id = row["carrierId"]
        source = run_root / f"{carrier_id}-candidate-manifest.json"
        bundle = run_root / f"{carrier_id}-candidate-bundle.json"
        witness_id = f"{carrier_id}-{run_id}"
        _collect_carrier(
            carrier_id=carrier_id,
            witness_id=witness_id,
            output=source,
            python=python,
        )
        _build_bundle(manifest=source, output=bundle, security_root=security_root, python=python)
        rows.append(
            {
                "carrierId": carrier_id,
                "baselineBundle": str(row["baselineBundle"]),
                "candidateBundle": str(bundle),
            }
        )
        evidence.append(
            {
                "carrierId": carrier_id,
                "baselineBundleSha256": row["baselineBundleSha256"],
                "candidateManifestSha256": _sha256(source),
                "candidateBundleSha256": _sha256(bundle),
            }
        )

    comparison_manifest = run_root / "pool-comparison-manifest.json"
    comparison_manifest.write_text(
        json.dumps({"schemaVersion": 1, "carriers": rows}, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    classification = _compare_pool(
        manifest=comparison_manifest,
        security_root=security_root,
        python=python,
    )
    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-security-pool-run",
        "runId": run_id,
        "poolId": baseline["poolId"],
        "poolIndexSha256": baseline["indexSha256"],
        "harnessRevision": _source_revision(HARNESS_ROOT),
        "securityRevision": _source_revision(security_root),
        "carrierEvidence": evidence,
        "classification": classification,
        "providerChallengeVisited": False,
        "providerSendAttempted": False,
    }
    (run_root / "pool-run-receipt.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def run_pool(
    *,
    run_id: str,
    security_root: Path,
    pool_index: Path,
    python: str,
    artifact_dir: Path | None,
) -> dict[str, Any]:
    run_id = _safe_id(run_id, "runId")
    security_root = security_root.resolve()
    if artifact_dir is None:
        with tempfile.TemporaryDirectory(prefix="ordivon-browser-security-pool-") as tmp:
            return _run_into(
                run_root=Path(tmp),
                run_id=run_id,
                security_root=security_root,
                pool_index=pool_index,
                python=python,
            )

    run_root = artifact_dir.resolve() / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    try:
        return _run_into(
            run_root=run_root,
            run_id=run_id,
            security_root=security_root,
            pool_index=pool_index,
            python=python,
        )
    except Exception:
        shutil.rmtree(run_root, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--security-root", type=Path, default=DEFAULT_SECURITY_ROOT)
    parser.add_argument("--pool-index", type=Path)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    security_root = args.security_root.resolve()
    pool_index = (
        args.pool_index.resolve()
        if args.pool_index is not None
        else security_root / DEFAULT_POOL_INDEX
    )
    receipt = run_pool(
        run_id=args.run_id,
        security_root=security_root,
        pool_index=pool_index,
        python=args.python,
        artifact_dir=args.artifact_dir,
    )
    text = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    if args.output is None:
        print(text, end="")
    else:
        args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
