#!/usr/bin/env python3
"""Promote one validated post-change Browser Security pool run into per-carrier LKG fixtures.

Security-v2 owns LKG semantics. The input is a durable Harness pool-run directory produced after a
Browserless candidate was staged. This command does not trust Harness drift classification: it
rebuilds every candidate bundle from its manifest, re-compares old LKG vs candidate with the
Security-v2 pool comparator, and accepts only no subject/detector/network drift with optional shared
browserBinary/controlLayer infrastructure change.

The command mutates only Security-v2 fixture/index files in the current checkout. It does not commit,
deploy, restart services, visit a provider challenge, or cross SEND.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from ordivon_security_v2 import (
    BrowserSecurityWitnessBundle,
    build_browser_security_witness_bundle,
    compare_browser_security_pool,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures/browser-security"
POOL_INDEX = FIXTURE_ROOT / "harness-r2-live-lkg-pool-index.json"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
CARRIER_RE = re.compile(r"^chatgpt-carrier-(11|12|13)$")
ALLOWED_SHARED_INFRASTRUCTURE = frozenset({"browserBinary", "controlLayer"})
MANIFEST_FIELDS = {
    "schemaVersion",
    "witnessId",
    "browserBinaryDigest",
    "controlLayer",
    "networkAuthority",
    "readings",
    "challengeStanding",
}


class ResealError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ResealError(f"{label} unavailable: {path}") from error
    if not isinstance(value, dict):
        raise ResealError(f"{label} must be one JSON object")
    return value


def _current_revision(root: Path = ROOT) -> str:
    proc = subprocess.run(
        ["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    revision = proc.stdout.strip()
    if COMMIT_RE.fullmatch(revision) is None:
        raise ResealError("Security-v2 checkout has invalid HEAD revision")
    return revision


def _safe_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise ResealError(f"{label} must be one sha256 digest")
    return value


def _safe_commit(value: object, label: str) -> str:
    if not isinstance(value, str) or COMMIT_RE.fullmatch(value) is None:
        raise ResealError(f"{label} must be one exact Git commit")
    return value


def _inside(root: Path, value: Path, label: str) -> Path:
    resolved_root = root.resolve()
    resolved = value.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise ResealError(f"{label} escapes its authority root: {value}") from error
    return resolved


def _load_index(index_path: Path, fixture_root: Path) -> dict[str, Any]:
    value = _load_json(index_path, "Browser Security pool LKG index")
    required = {"schemaVersion", "kind", "poolId", "standing", "comparisonLaw", "carriers"}
    if not required.issubset(value):
        raise ResealError("pool LKG index is missing required fields")
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.browser-security-pool-lkg-index":
        raise ResealError("unsupported pool LKG index")
    if value.get("standing") != "LKG_PER_CARRIER":
        raise ResealError("pool LKG index must be LKG_PER_CARRIER")
    law = value.get("comparisonLaw")
    if not isinstance(law, dict) or law.get("sameCarrierCandidateVsSameCarrierLkg") != "ALLOWED":
        raise ResealError("pool LKG index comparison law is not eligible")
    rows = value.get("carriers")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ResealError("pool LKG index must contain exactly three production carriers")
    carriers: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ResealError("pool carrier row must be one object")
        carrier = row.get("carrierId")
        if not isinstance(carrier, str) or CARRIER_RE.fullmatch(carrier) is None or carrier in carriers:
            raise ResealError("pool index has invalid or duplicate carrierId")
        bundle_ref = row.get("bundle")
        manifest_ref = row.get("manifest")
        if not isinstance(bundle_ref, str) or not isinstance(manifest_ref, str):
            raise ResealError(f"pool index paths missing for {carrier}")
        bundle_path = _inside(ROOT, ROOT / bundle_ref, f"baseline bundle for {carrier}")
        manifest_path = _inside(ROOT, ROOT / manifest_ref, f"baseline manifest for {carrier}")
        if not bundle_path.is_file() or not manifest_path.is_file():
            raise ResealError(f"pool baseline artifact missing for {carrier}")
        if sha256_file(bundle_path) != _safe_sha(row.get("bundleSha256"), "bundleSha256"):
            raise ResealError(f"baseline bundle digest mismatch for {carrier}")
        if sha256_file(manifest_path) != _safe_sha(row.get("manifestSha256"), "manifestSha256"):
            raise ResealError(f"baseline manifest digest mismatch for {carrier}")
        carriers[carrier] = {**row, "bundlePath": bundle_path, "manifestPath": manifest_path}
    if set(carriers) != {"chatgpt-carrier-11", "chatgpt-carrier-12", "chatgpt-carrier-13"}:
        raise ResealError("pool index carrier set is not the production 11/12/13 set")
    return {**value, "carrierMap": carriers, "fixtureRoot": fixture_root}


def _validate_reseal_classification(value: dict[str, Any]) -> None:
    if value.get("rootCauseEstablished") is not False:
        raise ResealError("pool classification must preserve rootCauseEstablished=false")
    if value.get("detectorDriftCarriers"):
        raise ResealError("detector drift cannot be promoted into an LKG")
    if value.get("sharedChangedFamilies") or value.get("carrierLocalChangedFamilies"):
        raise ResealError("CF02-CF07 subject drift cannot be promoted into an LKG")
    if value.get("carrierLocalInfrastructureChanges"):
        raise ResealError("carrier-local infrastructure drift cannot be promoted into an LKG")
    if value.get("challengeStandingChangedCarriers"):
        raise ResealError("challenge metadata drift cannot be promoted into an LKG")
    shared = set(value.get("sharedInfrastructureChanges") or [])
    if not shared.issubset(ALLOWED_SHARED_INFRASTRUCTURE):
        raise ResealError("only shared browserBinary/controlLayer infrastructure drift is reseal-eligible")
    expected_standing = "GLOBAL_DRIFT" if shared else "NO_OBSERVED_DRIFT"
    if value.get("standing") != expected_standing:
        raise ResealError("pool standing is inconsistent with reseal-eligible drift")


def _canonical_bundle_from_manifest(manifest: dict[str, Any]) -> BrowserSecurityWitnessBundle:
    if set(manifest) != MANIFEST_FIELDS or manifest.get("schemaVersion") != 1:
        raise ResealError("candidate manifest is not canonical Browser Security collector shape")
    try:
        return build_browser_security_witness_bundle(
            witness_id=manifest["witnessId"],
            browser_binary_digest=manifest["browserBinaryDigest"],
            control_layer=manifest["controlLayer"],
            network_authority=manifest["networkAuthority"],
            readings=manifest["readings"],
            challenge_standing=manifest["challengeStanding"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ResealError(f"candidate manifest failed Security-v2 canonicalization: {error}") from error


def _detector_version(manifest: dict[str, Any]) -> str:
    readings = manifest.get("readings")
    if not isinstance(readings, list) or not readings:
        raise ResealError("candidate manifest has no detector readings")
    versions = {row.get("detectorVersion") for row in readings if isinstance(row, dict)}
    if len(versions) != 1:
        raise ResealError("candidate manifest must use one detector version across the pool witness")
    version = next(iter(versions))
    if not isinstance(version, str) or not version:
        raise ResealError("candidate detectorVersion is invalid")
    return version


def _candidate_artifacts(
    *, run_root: Path, receipt: dict[str, Any], old_index: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, tuple[BrowserSecurityWitnessBundle, BrowserSecurityWitnessBundle]]]:
    evidence = receipt.get("carrierEvidence")
    if not isinstance(evidence, list) or len(evidence) != 3:
        raise ResealError("pool run receipt must contain three carrier evidence rows")
    evidence_map: dict[str, dict[str, Any]] = {}
    for row in evidence:
        if not isinstance(row, dict):
            raise ResealError("carrier evidence row must be one object")
        carrier = row.get("carrierId")
        if not isinstance(carrier, str) or CARRIER_RE.fullmatch(carrier) is None or carrier in evidence_map:
            raise ResealError("pool run receipt has invalid or duplicate carrier evidence")
        evidence_map[carrier] = row
    if set(evidence_map) != set(old_index["carrierMap"]):
        raise ResealError("candidate carrier set differs from current LKG pool")

    candidates: dict[str, dict[str, Any]] = {}
    pairs: dict[str, tuple[BrowserSecurityWitnessBundle, BrowserSecurityWitnessBundle]] = {}
    for carrier in sorted(evidence_map):
        source_manifest = _inside(
            run_root,
            run_root / f"{carrier}-candidate-manifest.json",
            f"candidate manifest for {carrier}",
        )
        source_bundle = _inside(
            run_root,
            run_root / f"{carrier}-candidate-bundle.json",
            f"candidate bundle for {carrier}",
        )
        if not source_manifest.is_file() or not source_bundle.is_file():
            raise ResealError(f"candidate artifacts missing for {carrier}")
        row = evidence_map[carrier]
        if sha256_file(source_manifest) != _safe_sha(
            row.get("candidateManifestSha256"), "candidateManifestSha256"
        ):
            raise ResealError(f"candidate manifest digest mismatch for {carrier}")
        if sha256_file(source_bundle) != _safe_sha(
            row.get("candidateBundleSha256"), "candidateBundleSha256"
        ):
            raise ResealError(f"candidate bundle digest mismatch for {carrier}")

        manifest = _load_json(source_manifest, f"candidate manifest for {carrier}")
        control = manifest.get("controlLayer")
        if not isinstance(control, dict) or control.get("endpointId") != carrier:
            raise ResealError(f"candidate endpoint identity mismatch for {carrier}")
        rebuilt = _canonical_bundle_from_manifest(manifest)
        bundle_value = _load_json(source_bundle, f"candidate bundle for {carrier}")
        try:
            parsed_bundle = BrowserSecurityWitnessBundle.from_dict(bundle_value)
        except ValueError as error:
            raise ResealError(f"candidate bundle invalid for {carrier}: {error}") from error
        if parsed_bundle.to_dict() != rebuilt.to_dict():
            raise ResealError(f"candidate bundle does not equal Security-v2 rebuild for {carrier}")

        baseline_value = _load_json(
            old_index["carrierMap"][carrier]["bundlePath"], f"baseline bundle for {carrier}"
        )
        try:
            baseline_bundle = BrowserSecurityWitnessBundle.from_dict(baseline_value)
        except ValueError as error:
            raise ResealError(f"current LKG bundle invalid for {carrier}: {error}") from error
        pairs[carrier] = (baseline_bundle, parsed_bundle)
        candidates[carrier] = {
            "manifest": manifest,
            "bundle": parsed_bundle.to_dict(),
            "sourceManifest": source_manifest,
            "sourceBundle": source_bundle,
        }
    return candidates, pairs


def _atomic_write_batch(values: dict[Path, bytes]) -> None:
    originals: dict[Path, bytes | None] = {
        path: path.read_bytes() if path.exists() else None for path in values
    }
    staged: dict[Path, Path] = {}
    try:
        for path, raw in values.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".reseal-tmp")
            tmp.write_bytes(raw)
            staged[path] = tmp
        for path, tmp in staged.items():
            os.replace(tmp, path)
    except Exception:
        for tmp in staged.values():
            tmp.unlink(missing_ok=True)
        for path, raw in originals.items():
            if raw is None:
                path.unlink(missing_ok=True)
            else:
                restore = path.with_name(path.name + ".reseal-restore")
                restore.write_bytes(raw)
                os.replace(restore, path)
        raise


def reseal(
    run_root: Path,
    *,
    expected_harness_revision: str,
    expected_old_index_sha256: str,
    fixture_root: Path = FIXTURE_ROOT,
    index_path: Path = POOL_INDEX,
) -> dict[str, Any]:
    run_root = run_root.resolve()
    fixture_root = fixture_root.resolve()
    index_path = index_path.resolve()
    expected_harness_revision = _safe_commit(
        expected_harness_revision, "expectedHarnessRevision"
    )
    expected_old_index_sha256 = _safe_sha(
        expected_old_index_sha256, "expectedOldIndexSha256"
    )
    security_revision = _current_revision(ROOT)
    old_index_digest = sha256_file(index_path)
    if old_index_digest != expected_old_index_sha256:
        raise ResealError("current pool-index digest differs from expected old index")
    old_index = _load_index(index_path, fixture_root)

    receipt_path = _inside(run_root, run_root / "pool-run-receipt.json", "pool run receipt")
    receipt = _load_json(receipt_path, "pool run receipt")
    if receipt.get("schemaVersion") != 1 or receipt.get("kind") != "ordivon.browser-security-pool-run":
        raise ResealError("unsupported pool run receipt")
    if receipt.get("providerChallengeVisited") is not False or receipt.get("providerSendAttempted") is not False:
        raise ResealError("pool run receipt crossed forbidden provider boundary")
    if receipt.get("harnessRevision") != expected_harness_revision:
        raise ResealError("pool run receipt Harness revision mismatch")
    if receipt.get("securityRevision") != security_revision:
        raise ResealError("pool run receipt Security-v2 revision mismatch")
    if receipt.get("poolIndexSha256") != old_index_digest:
        raise ResealError("pool run receipt pool-index digest mismatch")

    candidates, pairs = _candidate_artifacts(
        run_root=run_root, receipt=receipt, old_index=old_index
    )
    recomputed = compare_browser_security_pool(pairs)
    if receipt.get("classification") != recomputed:
        raise ResealError("Harness pool classification disagrees with Security-v2 recomputation")
    _validate_reseal_classification(recomputed)

    writes: dict[Path, bytes] = {}
    new_rows: list[dict[str, Any]] = []
    for carrier in sorted(candidates):
        suffix = carrier.rsplit("-", 1)[-1]
        manifest_name = f"harness-r2-live-lkg-carrier{suffix}-manifest.json"
        bundle_name = f"harness-r2-live-lkg-carrier{suffix}-bundle.json"
        manifest_path = fixture_root / manifest_name
        bundle_path = fixture_root / bundle_name
        manifest_raw = _canonical_bytes(candidates[carrier]["manifest"])
        bundle_raw = _canonical_bytes(candidates[carrier]["bundle"])
        writes[manifest_path] = manifest_raw
        writes[bundle_path] = bundle_raw
        manifest = candidates[carrier]["manifest"]
        control = manifest["controlLayer"]
        new_rows.append(
            {
                "browserBinaryDigest": manifest["browserBinaryDigest"],
                "bundle": str(bundle_path.relative_to(ROOT.resolve())),
                "bundleSha256": "sha256:" + hashlib.sha256(bundle_raw).hexdigest(),
                "carrierId": carrier,
                "challengeStanding": manifest["challengeStanding"],
                "controlLayerEndpointId": control["endpointId"],
                "detectorVersion": _detector_version(manifest),
                "manifest": str(manifest_path.relative_to(ROOT.resolve())),
                "manifestSha256": "sha256:" + hashlib.sha256(manifest_raw).hexdigest(),
                "networkAuthority": manifest["networkAuthority"],
                "witnessId": manifest["witnessId"],
            }
        )

    new_index = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-security-pool-lkg-index",
        "poolId": old_index["poolId"],
        "standing": "LKG_PER_CARRIER",
        "comparisonLaw": old_index["comparisonLaw"],
        "carriers": new_rows,
        "reseal": {
            "schemaVersion": 1,
            "previousPoolIndexSha256": old_index_digest,
            "sourcePoolRunReceiptSha256": sha256_file(receipt_path),
            "sourceHarnessRevision": expected_harness_revision,
            "sourceSecurityRevision": security_revision,
            "allowedSharedInfrastructureChanges": sorted(ALLOWED_SHARED_INFRASTRUCTURE),
            "observedStanding": recomputed["standing"],
            "observedSharedInfrastructureChanges": recomputed[
                "sharedInfrastructureChanges"
            ],
            "providerChallengeVisited": False,
            "providerSendAttempted": False,
            "rootCauseEstablished": False,
        },
    }
    index_raw = _canonical_bytes(new_index)
    new_index_digest = "sha256:" + hashlib.sha256(index_raw).hexdigest()
    if new_index_digest == old_index_digest:
        raise ResealError("reseal produced no pool-index identity change")
    writes[index_path] = index_raw
    _atomic_write_batch(writes)

    return {
        "schemaVersion": 1,
        "kind": "ordivon.browser-security-pool-lkg-reseal-r1",
        "standing": "LKG_RESEALED_PENDING_COMMIT",
        "securityRevisionBeforeCommit": security_revision,
        "sourceHarnessRevision": expected_harness_revision,
        "sourcePoolRunReceiptSha256": sha256_file(receipt_path),
        "previousPoolIndexSha256": old_index_digest,
        "newPoolIndexSha256": new_index_digest,
        "carrierIds": sorted(candidates),
        "observedStanding": recomputed["standing"],
        "observedSharedInfrastructureChanges": recomputed[
            "sharedInfrastructureChanges"
        ],
        "modifiedFiles": [
            str(path.resolve().relative_to(ROOT.resolve())) for path in sorted(writes)
        ],
        "providerChallengeVisited": False,
        "providerSendAttempted": False,
        "rootCauseEstablished": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--expected-harness-revision", required=True)
    parser.add_argument("--expected-old-index-sha256", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    value = reseal(
        args.run_root,
        expected_harness_revision=args.expected_harness_revision,
        expected_old_index_sha256=args.expected_old_index_sha256,
    )
    text = json.dumps(value, sort_keys=True, indent=2) + "\n"
    if args.output is None:
        print(text, end="")
    else:
        args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
