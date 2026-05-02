"""ADP-2: Detector tests — safe/unsafe fixtures, rule validation, determinism."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DETECTOR = ROOT / "scripts" / "detect_agentic_patterns.py"
SAFE_DIR = ROOT / "tests" / "fixtures" / "adp_detector" / "safe"
UNSAFE_DIR = ROOT / "tests" / "fixtures" / "adp_detector" / "unsafe"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(DETECTOR)] + list(args),
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(ROOT),
    )


def _findings(r: subprocess.CompletedProcess) -> list[dict]:
    if r.returncode == 0 and "findings" not in r.stdout:
        _run(str(SAFE_DIR), "--json")
    return []


def _json_findings(path: str) -> list[dict]:
    r = _run(path, "--json")
    data = json.loads(r.stdout)
    return data.get("findings", [])


class TestSafeFixturesNoFalsePositives:
    """Safe fixtures should produce zero blocking/degraded findings."""

    def test_safe_ready_not_flagged(self):
        f = _json_findings(str(SAFE_DIR / "safe-ready.md"))
        assert len(f) == 0, f"Safe READY flagged: {f}"

    def test_safe_capability_not_flagged(self):
        f = _json_findings(str(SAFE_DIR / "safe-capability.md"))
        assert len(f) == 0, f"Safe capability flagged: {f}"

    def test_safe_credential_not_flagged(self):
        f = _json_findings(str(SAFE_DIR / "safe-credential.md"))
        assert len(f) == 0, f"Safe credential flagged: {f}"

    def test_safe_external_benchmark_not_flagged(self):
        f = _json_findings(str(SAFE_DIR / "safe-external-benchmark.md"))
        assert len(f) == 0, f"Safe benchmark flagged: {f}"

    def test_safe_candidate_rule_not_flagged(self):
        f = _json_findings(str(SAFE_DIR / "safe-candidate-rule.md"))
        assert len(f) == 0, f"Safe CandidateRule flagged: {f}"

    def test_safe_baseline_not_flagged(self):
        f = _json_findings(str(SAFE_DIR / "safe-baseline.md"))
        # May produce warning, but should not produce blocking/degraded
        blocking = [x for x in f if x["severity"] in ("blocking", "degraded")]
        assert len(blocking) == 0, f"Safe baseline has blocking/degraded: {blocking}"

    def test_safe_mcp_not_flagged(self):
        f = _json_findings(str(SAFE_DIR / "safe-mcp.md"))
        blocking = [x for x in f if x["severity"] in ("blocking", "degraded")]
        assert len(blocking) == 0, f"Safe MCP has blocking/degraded: {blocking}"

    def test_safe_protected_path_not_flagged(self):
        f = _json_findings(str(SAFE_DIR / "safe-protected-path.md"))
        blocking = [x for x in f if x["severity"] in ("blocking", "degraded")]
        assert len(blocking) == 0, f"Safe protected path has blocking/degraded: {blocking}"


class TestUnsafeFixturesAreFlagged:
    """Unsafe fixtures should produce findings."""

    def test_unsafe_ready_overclaim_flagged(self):
        f = _json_findings(str(UNSAFE_DIR / "unsafe-ready-overclaim.md"))
        assert len(f) > 0, "Unsafe READY not flagged"
        assert any(x["pattern_id"] == "AP-RDY" for x in f)

    def test_unsafe_capability_collapse_flagged(self):
        f = _json_findings(str(UNSAFE_DIR / "unsafe-capability-collapse.md"))
        assert len(f) > 0, "Unsafe capability not flagged"
        assert any(x["pattern_id"] == "AP-COL" for x in f)

    def test_unsafe_credential_access_flagged(self):
        f = _json_findings(str(UNSAFE_DIR / "unsafe-credential-access.md"))
        assert len(f) > 0, "Unsafe credential not flagged"
        assert any(x["pattern_id"] == "AP-CRED" for x in f)

    def test_unsafe_external_side_effect_flagged(self):
        f = _json_findings(str(UNSAFE_DIR / "unsafe-external-side-effect.md"))
        assert len(f) > 0, "Unsafe external not flagged"
        assert any(x["pattern_id"] == "AP-EXT" for x in f)

    def test_unsafe_mcp_approval_flagged(self):
        f = _json_findings(str(UNSAFE_DIR / "unsafe-mcp-approval.md"))
        assert len(f) > 0, "Unsafe MCP not flagged"
        assert any(x["pattern_id"] == "AP-MCP" for x in f)

    def test_unsafe_benchmark_overclaim_flagged(self):
        f = _json_findings(str(UNSAFE_DIR / "unsafe-benchmark-overclaim.md"))
        assert len(f) > 0, "Unsafe benchmark not flagged"
        assert any(x["pattern_id"] == "AP-EBO" for x in f)

    def test_unsafe_candidate_rule_policy_flagged(self):
        f = _json_findings(str(UNSAFE_DIR / "unsafe-candidate-rule-policy.md"))
        assert len(f) > 0, "Unsafe CandidateRule not flagged"
        assert any(x["pattern_id"] == "AP-CRP" for x in f)

    def test_unsafe_evidence_laundering_flagged(self):
        f = _json_findings(str(UNSAFE_DIR / "unsafe-evidence-laundering.md"))
        assert len(f) > 0, "Unsafe evidence not flagged"
        assert any(x["pattern_id"] == "AP-EVL" for x in f)

    def test_unsafe_baseline_masking_flagged(self):
        f = _json_findings(str(UNSAFE_DIR / "unsafe-baseline-masking.md"))
        assert len(f) > 0, "Unsafe baseline not flagged"
        assert any(x["pattern_id"] == "AP-BDM" for x in f)

    def test_unsafe_protected_path_flagged(self):
        f = _json_findings(str(UNSAFE_DIR / "unsafe-protected-path.md"))
        assert len(f) > 0, "Unsafe protected path not flagged"
        assert any(x["pattern_id"] == "AP-PPV" for x in f)

    def test_unsafe_shell_gate_flagged(self):
        f = _json_findings(str(UNSAFE_DIR / "unsafe-shell-gate.md"))
        assert len(f) > 0, "Unsafe shell gate not flagged"
        assert any(x["pattern_id"] == "AP-SHE" for x in f)

    def test_unsafe_c4_c5_gate_flagged(self):
        f = _json_findings(str(UNSAFE_DIR / "unsafe-c4-c5-gate.md"))
        assert len(f) > 0, "Unsafe C4/C5 not flagged"
        assert any("GATE" in x["pattern_id"] for x in f)


class TestDetectorDeterminism:
    def test_detector_output_deterministic(self):
        r1 = _run(str(UNSAFE_DIR), "--json")
        r2 = _run(str(UNSAFE_DIR), "--json")
        assert r1.stdout == r2.stdout, "Detector output is not deterministic"

    def test_detector_json_is_valid(self):
        r = _run(str(UNSAFE_DIR), "--json")
        data = json.loads(r.stdout)
        assert "findings" in data
        assert "stats" in data
        for f in data["findings"]:
            for key in ["finding_id", "pattern_id", "severity", "file", "line", "explanation", "blocks_closure"]:
                assert key in f, f"Missing key {key} in finding"


class TestDetectorNoCanAccessSecrets:
    def test_detector_source_has_no_can_access_secrets(self):
        content = DETECTOR.read_text()
        assert "can_access_secrets" not in content, "Detector source contains forbidden can_access_secrets"


class TestDetectorCLI:
    def test_help_runs(self):
        r = _run("--help")
        assert r.returncode == 0

    def test_fail_on_blocking_exits_nonzero(self):
        r = _run(str(UNSAFE_DIR), "--fail-on-blocking")
        assert r.returncode != 0, "Should exit non-zero with blocking findings"

    def test_json_output_schema(self):
        r = _run(str(SAFE_DIR), "--json")
        data = json.loads(r.stdout)
        assert data["stats"]["total_files_scanned"] > 0
        assert isinstance(data["findings"], list)


# ── ADP-2R: Red-team regression tests ─────────────────────────

REDTEAM_DIR = ROOT / "tests" / "fixtures" / "adp_detector" / "redteam"


class TestRedTeamP01SafeNegationSuppressor:
    """P0-1: Safe negation poisoning must not suppress violations on same line."""

    def test_safe_negation_does_not_suppress_violation(self):
        f = _json_findings(str(REDTEAM_DIR / "p0-1-safe-negation-suppressor.md"))
        # The exploit line: capability + blocked + authorized to proceed
        blocking = [x for x in f if x["severity"] == "blocking"]
        assert len(blocking) >= 2, (
            f"Expected >=2 blocking findings for P0-1 exploit, got {len(blocking)}: {[x['pattern_id'] for x in blocking]}"
        )
        assert any(x["pattern_id"] == "AP-COL" and x["line"] == 6 for x in f), (
            "P0-1 exploit line 6 not flagged as AP-COL"
        )

    def test_safe_lines_still_safe(self):
        f = _json_findings(str(REDTEAM_DIR / "p0-1-safe-negation-suppressor.md"))
        # Lines 16, 18, 20 are safe lines
        safe_line_blocking = [x for x in f if x["severity"] == "blocking" and x["line"] in (16, 18, 20)]
        assert len(safe_line_blocking) == 0, f"Safe lines incorrectly flagged: {safe_line_blocking}"


class TestRedTeamP02MultilineSeparation:
    """P0-2: Multi-line capability + authorization must be detected."""

    def test_multiline_exploit_flagged(self):
        f = _json_findings(str(REDTEAM_DIR / "p0-2-multiline-separation.md"))
        ml_findings = [x for x in f if x["pattern_id"] == "AP-COL-ML"]
        assert len(ml_findings) >= 2, f"Expected >=2 multi-line findings, got {len(ml_findings)}"

    def test_multiline_safe_not_flagged(self):
        f = _json_findings(str(REDTEAM_DIR / "p0-2-multiline-separation.md"))
        blocking_safe = [x for x in f if x["severity"] == "blocking" and 16 <= x["line"] <= 20]
        # Lines 16-20 are safe — may have ML false positive but should have no single-line blocking
        single_line_blocking = [x for x in blocking_safe if x["pattern_id"] != "AP-COL-ML"]
        assert len(single_line_blocking) == 0, f"Safe lines flagged: {single_line_blocking}"


class TestRedTeamP11LowercaseReady:
    """P1-1: Lowercase 'ready' must be detected."""

    def test_lowercase_ready_flagged(self):
        f = _json_findings(str(REDTEAM_DIR / "p1-1-lowercase-ready.md"))
        ready_findings = [x for x in f if x["pattern_id"] == "AP-RDY"]
        assert len(ready_findings) >= 1, f"Expected >=1 AP-RDY for lowercase ready, got {len(ready_findings)}"

    def test_safe_ready_not_flagged(self):
        f = _json_findings(str(REDTEAM_DIR / "p1-1-lowercase-ready.md"))
        # Lines 9-10 are safe variants
        safe_blocking = [x for x in f if x["severity"] == "blocking" and x["line"] in (9, 10)]
        assert len(safe_blocking) == 0, f"Safe ready lines flagged: {safe_blocking}"
