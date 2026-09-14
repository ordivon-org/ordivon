#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tomllib
from pathlib import Path

UID_RE = re.compile(r"^UID:\s*(\S+)\s*$", re.MULTILINE)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def file_identity(root: Path, rel: str) -> dict:
    path = root / rel
    return {
        "path": rel,
        "sha256": sha256(path),
        "lastCommit": git(root, "log", "-1", "--format=%H", "--", rel),
    }


def authority_decisions(profile: dict) -> list[dict]:
    result: list[dict] = []
    for row in profile.get("authority", []):
        result.append({
            "id": row["id"],
            "disposition": "BOUND",
            "role": row.get("role"),
            "source": row.get("source"),
            "currentnessChecked": row.get("currentness_checked"),
            "rationale": row.get("rationale"),
        })
    for row in profile.get("excluded_authority", []):
        result.append({
            "id": row["id"],
            "disposition": "EXCLUDED",
            "role": row.get("role"),
            "source": row.get("source"),
            "currentnessChecked": row.get("currentness_checked"),
            "rationale": row.get("reason") or row.get("rationale"),
        })
    for row in profile.get("deferred_authority", []):
        result.append({
            "id": row["id"],
            "disposition": "DEFERRED",
            "role": row.get("role"),
            "source": row.get("source"),
            "currentnessChecked": row.get("currentness_checked"),
            "rationale": row.get("reason") or row.get("rationale"),
        })
    return result


def currentness_signals(profile: dict) -> list[dict]:
    signals: list[dict] = []
    for row in profile.get("authority", []):
        signal = {k: row[k] for k in ("id", "local_pin", "current_stable_observed", "currentness_checked") if k in row}
        if len(signal) > 2 or "local_pin" in signal or "current_stable_observed" in signal:
            signals.append(signal)
    return signals


def non_claims(profile: dict) -> list[str]:
    rows: list[str] = []
    for key, value in profile.get("non_claims", {}).items():
        if value is False or value == "NONE_CLAIMED":
            rows.append(f"{key}={value}")
    return rows


def parse_case(spec: str) -> tuple[str, Path, str, str, str]:
    parts = spec.split("|", 4)
    if len(parts) != 5:
        raise SystemExit("--case must be NAME|ROOT|PROFILE|REPORT|REQUIREMENTS")
    name, root, profile, report, requirements = parts
    return name, Path(root), profile, report, requirements


def capture(spec: str) -> dict:
    name, root, profile_rel, report_rel, requirements_rel = parse_case(spec)
    profile_path = root / profile_rel
    report_path = root / report_rel
    requirements_path = root / requirements_rel
    profile = tomllib.loads(profile_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    uids = UID_RE.findall(requirements_path.read_text(encoding="utf-8"))
    if not uids:
        raise SystemExit(f"{name}: no requirement UIDs found in {requirements_rel}")
    if len(set(uids)) != len(uids):
        raise SystemExit(f"{name}: duplicate requirement UIDs")
    decisions = authority_decisions(profile)
    if not decisions:
        raise SystemExit(f"{name}: no authority decisions")
    boundary = report.get("boundary")
    summary = report.get("summary")
    if not isinstance(boundary, str) or not boundary.strip():
        raise SystemExit(f"{name}: report has no claim boundary")
    if not isinstance(summary, dict) or not summary:
        raise SystemExit(f"{name}: report has no domain verdict summary")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.standard-native.profile-projection",
        "caseId": name,
        "domain": name,
        "source": {
            "repo": str(root),
            "headRevision": git(root, "rev-parse", "HEAD"),
            "profile": file_identity(root, profile_rel),
            "report": file_identity(root, report_rel),
            "requirements": file_identity(root, requirements_rel),
        },
        "subject": profile.get("subject") or report.get("subject") or {},
        "profileModel": profile.get("model"),
        "authorityDecisions": decisions,
        "requirementIdentity": {"count": len(uids), "uids": uids},
        "verdict": {"owner": "domain", "summary": summary},
        "claimBoundary": boundary,
        "workSemantics": profile.get("work_semantics", {}),
        "currentnessSignals": currentness_signals(profile),
        "nonClaims": non_claims(profile),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append", required=True, help="NAME|ROOT|PROFILE|REPORT|REQUIREMENTS")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    cases = [capture(spec) for spec in args.case]
    vocab_sets = [set(case["verdict"]["summary"]) for case in cases]
    shared_statuses = sorted(set.intersection(*vocab_sets)) if vocab_sets else []
    union_statuses = sorted(set.union(*vocab_sets)) if vocab_sets else []
    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.standard-native.enterprise-r2-cross-domain-dogfood",
        "capturedAt": "2026-09-14",
        "cases": cases,
        "observations": {
            "caseCount": len(cases),
            "allHaveExternalAuthorityDecisions": all(bool(c["authorityDecisions"]) for c in cases),
            "allHaveStableRequirementIdentity": all(c["requirementIdentity"]["count"] > 0 for c in cases),
            "allHaveExplicitClaimBoundary": all(bool(c["claimBoundary"].strip()) for c in cases),
            "domainVerdictVocabulariesDistinct": len({tuple(sorted(v)) for v in vocab_sets}) == len(vocab_sets),
            "sharedVerdictStatuses": shared_statuses,
            "unionVerdictStatuses": union_statuses,
            "universalVerdictNormalizationApplied": False,
        },
        "boundary": "This receipt is a read-only projection over domain-owned source profiles and reports. It does not replace their semantics, certify conformance, or make their verdict vocabularies universal."
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
