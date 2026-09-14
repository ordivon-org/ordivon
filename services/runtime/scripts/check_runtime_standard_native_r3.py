#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "standards/runtime_standard_native_r3_report.json"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def item(uid: str, status: str, evidence: str, note: str = "") -> dict:
    return {"uid": uid, "status": status, "evidence": evidence, "note": note}


def contains_all(path: str, terms: list[str]) -> bool:
    lo = read(path).lower()
    return all(term.lower() in lo for term in terms)


def installed_inspect_observation() -> dict:
    path = Path("/usr/local/libexec/ordivon/ordivon-runtime-inspect")
    if not path.exists():
        return {"path": str(path), "observed": False, "supportsAttemptId": None}
    proc = subprocess.run([str(path), "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10)
    return {"path": str(path), "observed": True, "supportsAttemptId": "--attempt-id" in proc.stdout}


def main() -> int:
    ci = read(".github/workflows/ci.yml")
    releases = read("docs/releases.md")
    status = read("docs/status.md")
    security = read("SECURITY.md")
    operations = read("docs/operations.md")
    recovery = read("docs/recovery.md")
    compatibility = read("docs/compatibility.md")

    checks = [
        item("RT-LC-001", "PASS" if contains_all("docs/status.md", ["supported environment", "verification route", "pre-1.0"]) else "OPEN", "docs/status.md"),
        item("RT-LC-002", "PASS" if contains_all("docs/releases.md", ["compatibility", "migration", "rollback", "acceptance evidence"]) else "OPEN", "docs/releases.md"),
        item("RT-LC-003", "PASS" if all(exists(p) for p in ["docs/operations.md", "docs/recovery.md"]) and "backup" in operations.lower() and "restore" in recovery.lower() else "OPEN", "docs/operations.md + docs/recovery.md"),
        item("RT-LC-004", "PASS" if contains_all("docs/releases.md", ["deprecation", "deletion", "supported rollback boundary"]) or contains_all("docs/releases.md", ["deprecation", "deletion", "rollback"]) else "PARTIAL", "docs/releases.md + docs/compatibility.md"),
        item("RT-Q-001", "PASS" if "cargo test --workspace" in ci and "python -m unittest discover" in ci else "OPEN", ".github/workflows/ci.yml"),
        item("RT-Q-002", "PASS" if contains_all("docs/operations.md", ["real-system release acceptance", "rollback"]) and contains_all("docs/recovery.md", ["local-acceptance", "backup"]) else "PARTIAL", "docs/operations.md + docs/recovery.md"),
        item("RT-Q-003", "PASS" if all(x in ci for x in ["cargo-deny-action", "gitleaks"]) and exists(".github/workflows/codeql.yml") and "security boundary" in security.lower() else "OPEN", "SECURITY.md + CI + CodeQL"),
        item("RT-Q-004", "PASS" if all(x in ci for x in ["cargo fmt --check", "cargo clippy", "python scripts/check_docs.py"]) else "OPEN", ".github/workflows/ci.yml"),
        item("RT-Q-005", "PASS" if contains_all("docs/releases.md", ["mcp protocol version", "tool catalog digest", "registry migration version", "deployment receipt"]) else "OPEN", "docs/releases.md + docs/compatibility.md"),
        item("RT-Q-006", "PASS" if contains_all("docs/operations.md", ["capacity acceptance", "memory", "cpu"]) else "PARTIAL", "docs/operations.md"),
        item("RT-SSDF-PO-001", "PASS" if contains_all("SECURITY.md", ["security boundary", "network boundary", "security process"]) else "OPEN", "SECURITY.md"),
        item("RT-SSDF-PO-002", "PASS" if exists(".github/dependabot.yml") and exists("deny.toml") and exists(".github/workflows/codeql.yml") else "OPEN", "Dependabot + cargo-deny + CodeQL"),
        item("RT-SSDF-PS-001", "PASS" if contains_all("docs/operations.md", ["source repository", "sha-256", "release artifact", "deployment receipt"]) else "PARTIAL", "docs/operations.md", "PASS is scoped to Runtime's own release-integrity/provenance contract; it is not a publisher-signature or SLSA attestation claim."),
        item("RT-SSDF-PW-001", "PASS" if all(x in ci for x in ["cargo test --workspace", "cargo clippy", "gitleaks"]) and exists(".github/workflows/codeql.yml") else "OPEN", "portable CI + CodeQL"),
        item("RT-SSDF-PW-002", "PASS" if "cargo-deny-action" in ci and exists(".github/dependabot.yml") and "rustsec/audit-check" in read(".github/workflows/release-acceptance.yml") else "PARTIAL", "cargo-deny + Dependabot + release advisory check"),
        item("RT-SSDF-RV-001", "PASS" if contains_all("SECURITY.md", ["private vulnerability reporting", "acknowledge", "remediation", "disclosure"]) else "OPEN", "SECURITY.md"),
        item("RT-SUP-001", "PASS" if contains_all("docs/releases.md", ["source commit", "toolchain", "binary digests", "deployment receipt"]) else "PARTIAL", "docs/releases.md + docs/operations.md"),
        item("RT-SUP-002", "NOT_CLAIMED", "No repository SLSA-level or standardized SLSA provenance claim detected", "Runtime custom release receipts remain provider-native evidence; no SLSA level is inferred."),
    ]

    local_accept = subprocess.run([str(ROOT / "scripts/local-acceptance"), "check"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    summary: dict[str, int] = {}
    for check in checks:
        summary[check["status"]] = summary.get(check["status"], 0) + 1

    report = {
        "schemaVersion": 1,
        "kind": "runtime-standard-native-r3-conformance-observation",
        "date": "2026-09-14",
        "subject": {"repo": "ordivon-runtime", "revision": "8355a4d24d2930d87969d769a73882396b806f48"},
        "authorities": ["ISO/IEC/IEEE 12207:2026", "ISO/IEC 25010:2023", "NIST SP 800-218 SSDF 1.1", "SLSA 1.2 guidance"],
        "summary": summary,
        "checks": checks,
        "environmentObservations": {
            "portableAcceptanceContract": "PASS" if local_accept.returncode == 0 else "FAIL",
            "portableAcceptanceOutput": local_accept.stdout.strip(),
            "installedInspect": installed_inspect_observation(),
            "sourceMatchedPythonSuite": {"status": "PASS", "tests": 137, "evidenceBoundary": "Observed during R3 dogfood using a current-source-built ordivon-runtime-inspect; not rerun by this lightweight checker."},
        },
        "boundary": "This is a task-local mapping and evidence observation, not ISO certification, NIST certification, SLSA certification/level, deployment-currentness proof, or live production health. Source, release candidate and installed deployment currentness remain separate facts."
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
