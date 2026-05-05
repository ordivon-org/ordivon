#!/usr/bin/env python3
"""Stage Runner — Ordivon governance pipeline executor.

Ordivon-CATLASS: loads a stage template and enforces its governance pipeline —
pre-flight checks, boundary enforcement, verification gates, receipt generation,
registry updates, and AI onboarding handoff.

Usage:
    python scripts/run_stage.py --template stage-templates/doc-governance.yaml --stage-id <id>
    python scripts/run_stage.py --template stage-templates/doc-governance.yaml --stage-id <id> --dry-run

Adding a template: create stage-templates/<name>.yaml with template_id,
pre_flight, allowed_paths, forbidden_boundaries, verification, receipt,
registry, and ai_onboarding sections.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE_TEMPLATES_DIR = ROOT / "stage-templates"
RECEIPT_DIR = ROOT / "docs" / "runtime"

# ── Data types ──────────────────────────────────────────────────────


@dataclass
class CheckResult:
    check_id: str
    description: str
    passed: bool
    output: str = ""
    exit_code: int = 0


@dataclass
class StageReceipt:
    stage_id: str
    stage_type: str
    template_id: str
    timestamp: str
    freeze_protocol: dict = field(default_factory=dict)
    files_changed: list[str] = field(default_factory=list)
    pre_flight: list[dict] = field(default_factory=list)
    verification: list[dict] = field(default_factory=list)
    boundary_violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    overall: str = "READY"  # READY | DEGRADED | BLOCKED


# ── YAML loader ─────────────────────────────────────────────────────


def _load_yaml(path: Path) -> dict:
    """Load YAML using PyYAML (installed via uv add pyyaml)."""
    import yaml as _pyyaml

    loader = getattr(_pyyaml, "CSafeLoader", None) or _pyyaml.SafeLoader
    with open(path) as f:
        return _pyyaml.load(f, Loader=loader) or {}


def _resolve_list_of_dicts(raw: list) -> list:
    """Normalize mixed list items to dicts for pre_flight/verification sections."""
    result = []
    for item in raw:
        if isinstance(item, str) and ":" in item:
            key, _, val = item.partition(":")
            result.append({key.strip(): val.strip().strip('"').strip("'")})
        else:
            result.append(item)
    return result


# ── Template loader ─────────────────────────────────────────────────


def load_template(template_path: str) -> dict:
    """Load and validate a stage template."""
    path = Path(template_path)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        print(f"❌ Template not found: {path}")
        sys.exit(1)

    template = _load_yaml(path)

    # Validate required sections
    required = ["template_id", "allowed_paths", "forbidden_boundaries", "verification", "receipt", "ai_onboarding"]
    missing = [k for k in required if k not in template]
    if missing:
        print(f"❌ Template missing required sections: {missing}")
        sys.exit(1)

    return template


# ── Checks ──────────────────────────────────────────────────────────


def _run_command(cmd: str, timeout: int = 300) -> tuple[str, int]:
    """Run a shell command, return (stdout+stderr, exit_code)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (result.stdout + result.stderr).strip(), result.returncode
    except subprocess.TimeoutExpired:
        return f"TIMEOUT ({timeout}s)", -1
    except Exception as e:
        return str(e), -1


def run_pre_flight(template: dict) -> list[CheckResult]:
    """Run pre-flight checks. Returns results; caller decides if any blocked."""
    results = []
    for check in template.get("pre_flight", []):
        if isinstance(check, dict):
            cmd = check.get("command", "")
            check_id = check.get("id", cmd[:40])
            desc = check.get("description", cmd)
            timeout = check.get("timeout", 120)
            output, rc = _run_command(cmd, timeout)
            results.append(
                CheckResult(
                    check_id=check_id,
                    description=desc,
                    passed=(rc == 0),
                    output=output,
                    exit_code=rc,
                )
            )
        elif isinstance(check, str):
            output, rc = _run_command(check)
            results.append(
                CheckResult(
                    check_id=check[:60],
                    description=check,
                    passed=(rc == 0),
                    output=output,
                    exit_code=rc,
                )
            )
    return results


def run_verification(verification_gates: list) -> list[CheckResult]:
    """Run verification gates. Returns results with pass/fail."""
    results = []
    for gate in verification_gates:
        if isinstance(gate, dict):
            cmd = gate.get("command", "")
            gate_id = gate.get("id", "")
            desc = gate.get("description", "")
            timeout = gate.get("timeout", 300)
        elif isinstance(gate, str):
            cmd = gate
            gate_id = cmd[:60]
            desc = cmd
            timeout = 300
        else:
            continue

        print(f"  Running: {gate_id}...")
        output, rc = _run_command(cmd, timeout)
        passed = rc == 0

        results.append(
            CheckResult(
                check_id=gate_id,
                description=desc,
                passed=passed,
                output=output[:500],
                exit_code=rc,
            )
        )
    return results


def check_boundaries(template: dict) -> list[str]:
    """Check modified files against forbidden boundaries."""
    modified = _get_modified_files()
    violations = []

    forbidden = template.get("forbidden_boundaries", [])
    if not forbidden:
        return violations

    for f in modified:
        for pattern in forbidden:
            # Support glob patterns
            if Path(f).match(pattern) or _glob_match(f, pattern):
                violations.append(f"{f}  (matches forbidden: {pattern})")
                break

    return violations


def _get_modified_files() -> list[str]:
    """Get list of modified/new files relative to HEAD."""
    # Staged + unstaged modifications
    result = subprocess.run(
        "git diff --name-only HEAD",
        shell=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    modified = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

    # Untracked files (not in .gitignore)
    result2 = subprocess.run(
        "git ls-files --others --exclude-standard",
        shell=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    untracked = [f.strip() for f in result2.stdout.strip().split("\n") if f.strip()]
    modified.extend(untracked)

    return sorted(set(modified))


def _glob_match(filepath: str, pattern: str) -> bool:
    """Simple glob matching for boundary patterns."""
    from fnmatch import fnmatch

    return fnmatch(filepath, pattern)


# ── Receipt generation ─────────────────────────────────────────────


def generate_receipt(
    stage_id: str,
    template: dict,
    pre_flight_results: list[CheckResult],
    verification_results: list[CheckResult],
    boundary_violations: list[str],
) -> StageReceipt:
    """Generate structured receipt from execution results."""
    modified = _get_modified_files()

    # Determine overall status
    blocked = False
    degraded = False

    for r in verification_results:
        if not r.passed:
            # Check if this gate is BLOCKED on failure
            gate = _find_gate(template.get("verification", []), r.check_id)
            failure_mode = gate.get("on_failure", "BLOCKED") if gate else "BLOCKED"
            if failure_mode == "BLOCKED":
                blocked = True
            elif failure_mode == "DEGRADED":
                degraded = True

    if boundary_violations:
        blocked = True

    overall = "BLOCKED" if blocked else ("DEGRADED" if degraded else "READY")

    return StageReceipt(
        stage_id=stage_id,
        stage_type="doc-governance",
        template_id=template.get("template_id", "unknown"),
        timestamp=datetime.now(timezone.utc).isoformat(),
        freeze_protocol=dict(template.get("freeze_protocol", {})),
        files_changed=modified,
        pre_flight=[{"id": r.check_id, "passed": r.passed, "output": r.output[:200]} for r in pre_flight_results],
        verification=[
            {
                "id": r.check_id,
                "desc": r.description,
                "passed": r.passed,
                "exit_code": r.exit_code,
                "output": r.output[:200],
            }
            for r in verification_results
        ],
        boundary_violations=boundary_violations,
        overall=overall,
    )


def _find_gate(gates: list, check_id: str) -> dict | None:
    """Find a gate definition by id."""
    for g in gates:
        if isinstance(g, dict) and g.get("id") == check_id:
            return g
    return None


# ── Output ──────────────────────────────────────────────────────────


def write_receipt(receipt: StageReceipt, template: dict) -> Path:
    """Write receipt as JSON to runtime directory."""
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    filename = template.get("receipt", {}).get("filename_pattern", "{stage_id}-receipt.json")
    filename = filename.replace("{stage_id}", receipt.stage_id)
    path = RECEIPT_DIR / filename

    data = {
        "stage_id": receipt.stage_id,
        "stage_type": receipt.stage_type,
        "template_id": receipt.template_id,
        "timestamp": receipt.timestamp,
        "freeze_protocol": receipt.freeze_protocol,
        "files_changed": receipt.files_changed,
        "pre_flight": receipt.pre_flight,
        "verification": receipt.verification,
        "boundary_violations": receipt.boundary_violations,
        "warnings": receipt.warnings,
        "overall": receipt.overall,
    }

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return path


def print_results(receipt: StageReceipt, template: dict) -> None:
    """Print human-readable stage results."""
    print()
    print("=" * 60)
    print(f"STAGE: {receipt.stage_id}")
    print(f"Template: {template.get('template_id')} v{template.get('template_version', '?')}")
    print(f"Overall: {receipt.overall}")
    print("=" * 60)

    # Freeze protocol
    if receipt.freeze_protocol:
        state = receipt.freeze_protocol.get("state", "unknown")
        enforcement = receipt.freeze_protocol.get("enforcement", "record_only")
        print("\n── Freeze Protocol ──")
        print(f"  State: {state}")
        print(f"  Enforcement: {enforcement}")

    # Pre-flight
    if receipt.pre_flight:
        print("\n── Pre-flight ──")
        for r in receipt.pre_flight:
            s = "✅" if r["passed"] else "❌"
            print(f"  {s} {r['id']}")

    # Verification
    print("\n── Verification ──")
    for r in receipt.verification:
        s = "✅" if r["passed"] else "❌"
        print(f"  {s} {r['id']:35s} (exit={r['exit_code']})")
        if not r["passed"]:
            preview = r["output"][:200].replace("\n", " | ")
            print(f"     {'':35s} → {preview}")

    # Boundaries
    print("\n── Boundaries ──")
    if receipt.boundary_violations:
        print(f"  ❌ {len(receipt.boundary_violations)} violation(s):")
        for v in receipt.boundary_violations:
            print(f"     {v}")
    else:
        print("  ✅ No boundary violations")

    # Files
    print(f"\n── Files Changed ({len(receipt.files_changed)}) ──")
    for f in receipt.files_changed[:30]:
        print(f"  {f}")
    if len(receipt.files_changed) > 30:
        print(f"  ... and {len(receipt.files_changed) - 30} more")

    # Post-flight prompts
    print("\n── Post-flight ──")
    for action in template.get("registry", []):
        print(f"  [ ] {action.get('description', action.get('action', ''))}")
    for target in template.get("ai_onboarding", []):
        print(f"  [ ] Check {target.get('file', target)} — {target.get('update_condition', '')}")
    print("  [ ] Commit with stage receipt reference")
    print()


# ── Main ────────────────────────────────────────────────────────────


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Ordivon Stage Runner — governance pipeline executor")
    parser.add_argument("--template", required=True, help="Path to stage template YAML")
    parser.add_argument("--stage-id", required=True, help="Unique stage identifier")
    parser.add_argument(
        "--dry-run", action="store_true", help="Load template and show what would run, but don't execute"
    )
    parser.add_argument(
        "--non-interactive", action="store_true", help="Skip agent execution prompt — run verification directly"
    )
    args = parser.parse_args()

    # 1. Load template
    template = load_template(args.template)
    print(f"Template: {template['template_id']} v{template.get('template_version', '?')}")
    print(f"Description: {template.get('description', 'N/A')}")
    print()

    if args.dry_run:
        print("── Dry Run (no execution) ──")
        print(f"Allowed paths ({len(template.get('allowed_paths', []))}):")
        for p in template.get("allowed_paths", [])[:10]:
            print(f"  {p}")
        print(f"Forbidden boundaries ({len(template.get('forbidden_boundaries', []))}):")
        for p in template.get("forbidden_boundaries", []):
            print(f"  {p}")
        print(f"Verification gates ({len(template.get('verification', []))}):")
        for g in template.get("verification", []):
            if isinstance(g, dict):
                print(f"  {g.get('id')}: {g.get('command')} (on_failure={g.get('on_failure')})")
            else:
                print(f"  {g}")
        freeze = template.get("freeze_protocol", {})
        if freeze:
            print(
                f"Freeze state: {freeze.get('state', 'unknown')} "
                f"(enforcement={freeze.get('enforcement', 'record_only')})"
            )
        return 0

    # 2. Pre-flight
    print("── Pre-flight ──")
    pre_results = run_pre_flight(template)
    blocked_pre = False
    for r in pre_results:
        s = "✅" if r.passed else "❌"
        print(f"  {s} {r.check_id[:70]}")
        if not r.passed and r.output:
            print(f"     {r.output[:200]}")
        # Check if pre-flight failure is blocking
        check_def = None
        for c in template.get("pre_flight", []):
            if isinstance(c, dict) and c.get("id") == r.check_id:
                check_def = c
                break
        if check_def and check_def.get("on_failure") == "BLOCKED" and not r.passed:
            blocked_pre = True

    if blocked_pre:
        print("\n❌ BLOCKED: pre-flight check(s) failed.")
        return 1

    # 3. Agent execution phase
    print()
    print("── Execution ──")
    print(f"Allowed paths: {len(template.get('allowed_paths', []))} patterns")
    print(f"Forbidden: {len(template.get('forbidden_boundaries', []))} patterns")
    if not args.non_interactive:
        print()
        print("Agent: perform the stage work within the boundaries above.")
        print("When done, press Enter to run verification gates...")
        input()
    else:
        print("(non-interactive — running verification directly)")
    print()

    # 4. Verification
    print("\n── Verification ──")
    ver_results = run_verification(template.get("verification", []))
    print()

    # 5. Boundary check
    print("── Boundary Check ──")
    violations = check_boundaries(template)
    if violations:
        print(f"  ❌ {len(violations)} violation(s) found:")
        for v in violations:
            print(f"     {v}")
    else:
        print("  ✅ No boundary violations")
    print()

    # 6. Generate receipt
    receipt = generate_receipt(
        args.stage_id,
        template,
        pre_results,
        ver_results,
        violations,
    )
    receipt_path = write_receipt(receipt, template)

    # 7. Print results
    print_results(receipt, template)
    print(f"Receipt written: {receipt_path}")

    if receipt.overall == "BLOCKED":
        return 1
    elif receipt.overall == "DEGRADED":
        print("⚠ Stage complete with degradations — review before proceeding.")
        return 0
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
