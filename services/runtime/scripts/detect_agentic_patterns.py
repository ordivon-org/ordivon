#!/usr/bin/env python3
"""ADP-2: Agentic Pattern Detector — local static detection only.

Scans docs, fixtures, receipts for ADP-1 agentic pattern risks using
GOV-X gate semantics. Non-executing, no network, no credentials.

Usage:
    python scripts/detect_agentic_patterns.py <path> [path...]
    python scripts/detect_agentic_patterns.py docs examples/hap
    python scripts/detect_agentic_patterns.py --json <path>
    python scripts/detect_agentic_patterns.py --fail-on-blocking <path>

Detector PASS is not authorization. Absence of findings is not safety proof.
Findings are review evidence, not automatic approval.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ── Finding dataclass ──────────────────────────────────────────────────

@dataclass
class Finding:
    finding_id: str
    pattern_id: str
    severity: str  # info | warning | degraded | blocking
    risk_level: str
    capability_class: str
    authority_impact: str
    gate_expected: str
    gate_observed: str
    file: str
    line: int
    evidence_snippet: str
    explanation: str
    recommended_fix: str
    blocks_closure: bool

    def to_dict(self) -> dict:
        return self.__dict__


# ── Safe context patterns (negation allowlist) ─────────────────────────

SAFE_NEGATIONS = [
    r"not\s+authori[zs]ed?\b",
    r"does\s+not\s+authori[zs]e?\b",
    r"no\s+action\s+authori[zs]ation\b",
    r"not\s+created\b",
    r"forbidden\b",
    r"NO-GO\b",
    r"blocked\b",
    r"does\s+not\s+imply\b",
    r"not\s+.*approval\b",
    r"never\s+.*authori[zs]",
    r"remains?\s+non-binding\b",
    r"NON-BINDING\b",
    r"reference\s+only\b",
    r"not\s+claimed\b",
    r"not\s+granted\b",
    r"cannot\s+lower\s+risk\b",
    r"does\s+not\s+grant\b",
    r"not\s+.*execution\b",
]

def _is_safe_context(line: str) -> bool:
    return any(re.search(p, line, re.IGNORECASE) for p in SAFE_NEGATIONS)


# ── Detector rules ─────────────────────────────────────────────────────

def _find_text_files(root: Path) -> list[Path]:
    """Find text files to scan."""
    extensions = {".md", ".json", ".py", ".jsonl", ".txt", ".yaml", ".yml"}
    files = []
    for f in root.rglob("*"):
        if f.is_file() and f.suffix in extensions and ".git/" not in str(f):
            files.append(f)
    return files


def detect(input_paths: list[Path]) -> tuple[list[Finding], dict]:
    """Run all detector rules against input paths. Returns (findings, stats)."""
    findings: list[Finding] = []
    files_scanned = 0

    for path in input_paths:
        if not path.exists():
            continue
        if path.is_file():
            files = [path]
        else:
            files = _find_text_files(path)

        for f in files:
            files_scanned += 1
            try:
                lines = f.read_text(encoding="utf-8", errors="replace").split("\n")
            except Exception:
                continue

            for i, line in enumerate(lines, 1):
                findings.extend(_check_line(f, i, line))

            # ADP-3: Structure-aware
            if f.suffix == ".json":
                try:
                    findings.extend(_check_json_objects(f, f.read_text(encoding="utf-8", errors="replace")))
                except Exception:
                    pass

            # ADP-3: Registry-aware
            if f.suffix == ".jsonl" and "registry" in f.name.lower():
                findings.extend(_check_registry(f))

            # ADP-3: PV public-surface
            if f.suffix == ".md" and ("ordivon-verify" in str(f) or "ordivon_verify" in str(f) or "public_surface" in str(f)):
                try:
                    findings.extend(_check_public_surface(f, lines))
                except Exception:
                    pass

    stats = {
        "scanned_paths": [str(p) for p in input_paths],
        "total_files_scanned": files_scanned,
        "total_findings": len(findings),
        "info": sum(1 for x in findings if x.severity == "info"),
        "warning": sum(1 for x in findings if x.severity == "warning"),
        "degraded": sum(1 for x in findings if x.severity == "degraded"),
        "blocking": sum(1 for x in findings if x.severity == "blocking"),
        "blocks_closure": sum(1 for x in findings if x.blocks_closure),
    }
    return findings, stats


def _check_line(filepath: Path, lineno: int, line: str) -> list[Finding]:
    results = []
    rel = str(filepath.relative_to(ROOT)) if str(filepath).startswith(str(ROOT)) else str(filepath)

    # Skip lines in safe negation context
    if _is_safe_context(line):
        return results

    def add(pid, sev, risk, cap, ai, gate_exp, gate_obs, snippet, expl, fix, blocks):
        results.append(Finding(
            finding_id=f"ADP2-{pid}-{lineno:04d}",
            pattern_id=pid, severity=sev, risk_level=risk,
            capability_class=cap, authority_impact=ai,
            gate_expected=gate_exp, gate_observed=gate_obs,
            file=rel, line=lineno, evidence_snippet=snippet[:200],
            explanation=expl, recommended_fix=fix, blocks_closure=blocks,
        ))

    # ── Rule 1: READY overclaim ──
    if re.search(r"\bREADY\b(?!_WITHOUT_AUTHORIZATION)", line) and \
       not re.search(r"READY_WITHOUT_AUTHORIZATION", line):
        if re.search(r"(?:authori[zs]e[sd]?\s+(?:execution|merge|deploy|action|production)|approved\s+for\s+(?:merge|deploy|execution))", line, re.IGNORECASE):
            add("AP-RDY", "blocking", "AP-R4", "C4", "AI-3",
                "READY_WITHOUT_AUTHORIZATION", "READY",
                line.strip(), "READY overclaim: READY used as execution authorization.",
                "Change to READY_WITHOUT_AUTHORIZATION or add disclaimer.",
                True)

    # ── Rule 2: Capability authorization collapse ──
    cap_fields = r"(?:can_read_files|can_write_files|can_run_shell|can_use_mcp|can_call_external_api|can_read_credentials|can_apply_patch|can_use_browser)"
    if re.search(cap_fields, line):
        if re.search(rf"{cap_fields}.*(?:authori[zs]ed?|approved?|granted|permitted|allowed)\s+to", line, re.IGNORECASE):
            add("AP-COL", "blocking", "AP-R4", "C4", "AI-3",
                "BLOCKED", "READY/approved",
                line.strip(), "Capability-to-authorization collapse: capability treated as permission.",
                "Add authority denial: can_X does not imply may_X.",
                True)

    # ── Rule 3: Credential access confusion ──
    if re.search(r"can_read_credentials", line):
        if re.search(r"(?:credential\s+access\s+(?:granted|approved|authori[zs]ed)|secret\s+access|\.env\s+access)", line, re.IGNORECASE):
            add("AP-CRED", "blocking", "AP-R4", "C4", "AI-5",
                "BLOCKED", "access granted",
                line.strip(), "Credential capability confused with credential access permission.",
                "can_read_credentials is a declaration, not access. Block credential access at boundary.",
                True)

    # ── Rule 4: External side-effect authorization ──
    ext_terms = r"(?:external\s+API|network\s+call|browser\s+action|MCP\s+tool\s+execut|webhook|cloud\s+API|remote\s+tool)"
    if re.search(ext_terms, line, re.IGNORECASE):
        if re.search(r"(?:authori[zs]ed?|approved?|executed?|invoked?|called?)\b(?!.*(?:not|blocked|forbidden|NO-GO))", line, re.IGNORECASE):
            add("AP-EXT", "blocking", "AP-R4", "C4", "AI-5",
                "BLOCKED", "authorized/executed",
                line.strip(), "External side-effect drift: external call treated as authorized.",
                "External side-effect capability defaults to BLOCKED.",
                True)

    # ── Rule 5: MCP confused deputy ──
    if re.search(r"MCP\s+(?:server|tool|authori[zs]ation)", line, re.IGNORECASE):
        if re.search(r"(?:MCP|tool|server).*?(?:approves?|authori[zs]es?|grants?\s+permission|Ordivon\s+approv)", line, re.IGNORECASE):
            add("AP-MCP", "blocking", "AP-R4", "C4", "AI-5",
                "BLOCKED", "MCP approval claimed",
                line.strip(), "MCP authorization is transport security, not Ordivon governance approval.",
                "MCP auth != Ordivon approval. Add disclaimer.",
                True)

    # ── Rule 6: External benchmark overclaim ──
    bench_orgs = r"(?:OpenAI|Anthropic|DeepMind|Google\s*DeepMind|NIST|ISO\s*(?:/IEC)?\s*42001)"
    if re.search(bench_orgs, line):
        if re.search(rf"(?:{bench_orgs}).*?(?:compliant|certified|endorsed|partnered|equivalent\s+to|official\s+alignment)", line):
            add("AP-EBO", "blocking", "AP-R1", "C1", "AI-0",
                "BLOCKED", "compliance claimed",
                line.strip(), "External benchmark overclaim: compliance/certification/endorsement claimed.",
                "Add safe-language: reference only, no compliance claimed.",
                True)

    # ── Rule 7: CandidateRule premature promotion ──
    if re.search(r"CandidateRule|CR-ADP|CR-\d", line):
        if re.search(r"(?:binding\s+policy|promoted\s+to\s+policy|active\s+policy|enforced\s+policy|automatic\s+policy|policy\s+activated)", line, re.IGNORECASE):
            add("AP-CRP", "blocking", "AP-R5", "C5", "AI-6",
                "BLOCKED/NO-GO", "binding policy claimed",
                line.strip(), "CandidateRule premature promotion: advisory rule treated as binding policy.",
                "CandidateRule remains NON-BINDING until review phase.",
                True)

    # ── Rule 8: Evidence laundering ──
    ev_terms = r"(?:evidence|logs?|screenshots?|receipt|validation|report)"
    if re.search(ev_terms, line, re.IGNORECASE):
        if re.search(rf"{ev_terms}.*?(?:approves?|authori[zs]es?|confirms?\s+completion|proves?\s+(?:correct|safe|complete))", line, re.IGNORECASE):
            add("AP-EVL", "degraded", "AP-R4", "C4", "AI-3",
                "DEGRADED/BLOCKED", "evidence as approval",
                line.strip(), "Evidence laundering: evidence treated as approval without verification.",
                "Evidence supports review; evidence does not approve.",
                True)

    # ── Rule 9: Baseline debt masking ──
    if re.search(r"(?:all\s+tests?\s+pass|PASS\b.*\bfail)", line, re.IGNORECASE):
        if "degraded" not in line.lower() and "known" not in line.lower():
            add("AP-BDM", "warning", "AP-R5", "C5", "AI-3",
                "BLOCKED", "PASS with failures",
                line.strip(), "Baseline debt masking: failures claimed as PASS without known-debt classification.",
                "Classify failures as new vs pre-existing with baseline evidence.",
                False)

    # ── Rule 10: Protected path violation ──
    protected = r"(?:AGENTS\.md|docs/ai/|docs/governance/|docs/runtime/|\.github/|pyproject\.toml|package\.json|\.env|secrets?/|credential\b|policy\b|schema\b)"
    if re.search(protected, line, re.IGNORECASE):
        if re.search(r"(?:modif|chang|updat|writ|delet|remov|refactor|clean).*?(?:governance|registry|credential|policy|schema|AGENTS)", line, re.IGNORECASE):
            if "Allowe" not in line and "Forbidde" not in line and "boundary" not in line.lower():
                add("AP-PPV", "degraded", "AP-R2", "C2", "AI-3",
                    "REVIEW_REQUIRED", "no boundary",
                    line.strip(), "Protected path change without explicit boundary declaration.",
                    "Protected paths require explicit Allowed/Forbidden scope.",
                    True)

    # ── Rule 11: Shell risk gate mismatch ──
    if re.search(r"(?:shell|bash|command|build|test\s+run)", line, re.IGNORECASE):
        if re.search(r"READY_WITHOUT_AUTHORIZATION|READY\b(?!_WITHOUT)", line) and not re.search(r"REVIEW_REQUIRED|BLOCKED", line):
            add("AP-SHE", "degraded", "AP-R3", "C3", "AI-4",
                "REVIEW_REQUIRED/BLOCKED", "READY",
                line.strip(), "Shell execution with READY gate — requires REVIEW_REQUIRED or BLOCKED.",
                "C3/AP-R3 requires REVIEW_REQUIRED or BLOCKED plus evidence plan.",
                True)

    # ── Rule 12: C4/C5 gate mismatch ──
    c4_terms = r"(?:credentials?|network|MCP|browser|external\s+API|remote\s+tool|side\s+effect)"
    c5_terms = r"(?:broker|live\s+trading|production\s+deploy|irreversible|destructive)"
    if re.search(c4_terms, line, re.IGNORECASE):
        if re.search(r"READY\b(?!_WITHOUT_AUTHORIZATION)|PASS\b|proceed", line) and not re.search(r"BLOCKED|NO-GO|REVIEW_REQUIRED", line):
            add("AP-GATE-C4", "blocking", "AP-R4", "C4", "AI-5",
                "BLOCKED", "READY/PASS",
                line.strip(), "C4 gate mismatch: C4 capability with non-BLOCKED gate.",
                "C4 defaults to BLOCKED. Use REVIEW_REQUIRED only with explicit authorization.",
                True)
    if re.search(c5_terms, line, re.IGNORECASE):
        if not re.search(r"NO-GO|BLOCKED|DEFERRED|remains?\s+(?:NO-GO|BLOCKED|forbidden)", line, re.IGNORECASE):
            add("AP-GATE-C5", "blocking", "AP-R5", "C5", "AI-6",
                "NO-GO", "non-NO-GO",
                line.strip(), "C5 gate mismatch: C5 capability without NO-GO/BLOCKED.",
                "C5 defaults to NO-GO in current project state.",
                True)

    return results



# ── ADP-3: Structure-aware + Registry-aware + PV-aware checks ──────────

REGISTRY_PATH = ROOT / "docs" / "governance" / "document-registry.jsonl"

def _check_json_objects(filepath: Path, content_str: str) -> list[Finding]:
    """Parse HAP-3 TaskPlan/ReviewRecord JSON and run structure-aware checks."""
    results = []
    rel = str(filepath.relative_to(ROOT)) if str(filepath).startswith(str(ROOT)) else str(filepath)
    try:
        data = json.loads(content_str)
    except Exception:
        return results
    obj_type = data.get("object_type", "")
    if obj_type not in ("HarnessTaskPlan", "HarnessReviewRecord"):
        return results

    def add(pid, sev, risk, cap, ai, gate_exp, gate_obs, expl, fix, blocks, ln=0):
        results.append(Finding(
            finding_id=f"ADP3-{pid}-{filepath.name}",
            pattern_id=pid, severity=sev, risk_level=risk,
            capability_class=cap, authority_impact=ai,
            gate_expected=gate_exp, gate_observed=gate_obs,
            file=rel, line=ln, evidence_snippet=json.dumps(data)[:200],
            explanation=expl, recommended_fix=fix, blocks_closure=blocks,
        ))

    if obj_type == "HarnessTaskPlan":
        stmt = data.get("no_action_authorization_statement", "").lower()
        status = data.get("planned_status", "")
        if status == "READY_WITHOUT_AUTHORIZATION":
            if "does not authorize" not in stmt and "not authorization" not in stmt:
                add("ADP3-PLAN-EXEC", "blocking", "AP-R2", "C2", "AI-3",
                    "PLAN_ONLY/BLOCKED", "READY_WITHOUT_AUTHORIZATION",
                    "TaskPlan READY without authorization denial.", "Add denial.", True)
        if "execution authorized" in stmt:
            add("ADP3-PLAN-EXEC", "blocking", "AP-R2", "C2", "AI-3",
                "PLAN_ONLY/BLOCKED", "execution authorized",
                "TaskPlan claims execution permission.", "Remove execution claim.", True)
        cc = data.get("capability_class", "")
        ps = data.get("planned_status", "")
        if cc == "C4" and ps not in ("BLOCKED", "REVIEW_REQUIRED"):
            add("ADP3-PLAN-C4", "blocking", "AP-R4", "C4", "AI-5",
                "BLOCKED", ps, "C4 TaskPlan not BLOCKED.", "Set to BLOCKED.", True)
        if cc == "C5" and ps != "NO_GO":
            add("ADP3-PLAN-C5", "blocking", "AP-R5", "C5", "AI-6",
                "NO_GO", ps, "C5 TaskPlan not NO_GO.", "Set to NO_GO.", True)
        pp = data.get("protected_paths", [])
        bs = data.get("boundary_statement", "")
        if pp and not bs:
            add("ADP3-PLAN-PPATH", "degraded", "AP-R2", "C2", "AI-3",
                "REVIEW_REQUIRED", "no boundary", "Protected paths without boundary_statement.",
                "Add boundary_statement.", True)

    if obj_type == "HarnessReviewRecord":
        rt = data.get("reviewer_type", "")
        rs = data.get("review_status", "")
        nsa = data.get("no_action_authorization_statement", "").lower()
        if rt == "detector" and ("approved" in nsa or "authorized" in nsa or "proceed" in nsa):
            add("ADP3-REVIEW-DETECTOR", "blocking", "AP-R4", "C4", "AI-2",
                "REVIEW_REQUIRED", "detector approval", "Detector PASS as authorization.",
                "Detector PASS is not authorization.", True)
        if rs == "COMMENT_ONLY" and ("approved" in nsa or "merge" in nsa):
            add("ADP3-REVIEW-COMMENT", "blocking", "AP-R4", "C4", "AI-3",
                "REVIEW_REQUIRED", "comment approval", "COMMENT_ONLY as approval.",
                "COMMENT_ONLY is not approval.", True)
        crs = data.get("candidate_rule_status", "")
        if crs not in ("none", "proposed_non_binding", "rejected", "deferred"):
            add("ADP3-CR-BINDING", "blocking", "AP-R5", "C5", "AI-6",
                "BLOCKED", crs, "CandidateRule status implies binding.",
                "Use proposed_non_binding.", True)
    return results


def _check_registry(registry_path: Path = None) -> list[Finding]:
    results = []
    rp = Path(registry_path).resolve() if registry_path else REGISTRY_PATH
    if not rp.exists():
        return results
    def add(pid, sev, risk, cap, ai, gate_exp, gate_obs, expl, fix, blocks, ln=0):
        results.append(Finding(finding_id=f"ADP3-{pid}-REG", pattern_id=pid, severity=sev,
            risk_level=risk, capability_class=cap, authority_impact=ai,
            gate_expected=gate_exp, gate_observed=gate_obs,
            file=str(rp.relative_to(ROOT)), line=ln, evidence_snippet=expl[:200],
            explanation=expl, recommended_fix=fix, blocks_closure=blocks))
    try:
        entries = [json.loads(l) for l in rp.read_text().strip().split("\n") if l.strip()]
    except Exception:
        return results
    for i, e in enumerate(entries, 1):
        if e.get("status") == "current" and e.get("superseded_by"):
            add("ADP3-DG-SUPERSEDED", "blocking", "AP-R1", "C1", "AI-0",
                "READY_WITHOUT_AUTHORIZATION", "current+superseded",
                f"Entry {e.get('doc_id')} current but superseded_by={e.get('superseded_by')}",
                "Mark superseded or clear.", True, i)
        if e.get("ai_read_priority", 99) <= 1 and e.get("status") in ("superseded", "archived"):
            add("ADP3-DG-AI-STALE", "degraded", "AP-R1", "C1", "AI-0",
                "current", f"priority={e.get('ai_read_priority')}, status={e.get('status')}",
                f"High-priority AI doc {e.get('doc_id')} is {e.get('status')}",
                "Update or lower priority.", True, i)
        dt = e.get("doc_type", "")
        nt = (e.get("notes", "") or "").lower()
        if dt in ("receipt", "ledger"):
            if "action authorization" in nt or "authorizes" in nt or "authorization" in nt:
                add("ADP3-DG-RECEIPT-AUTH", "blocking", "AP-R1", "C1", "AI-0",
                    "supporting_evidence", e.get("authority", ""),
                    f"Receipt/ledger {e.get('doc_id')} claims action authorization",
                    "Receipts are evidence, not authorization.", True, i)
    return results


def _check_public_surface(filepath: Path, lines: list[str]) -> list[Finding]:
    results = []
    rel = str(filepath.relative_to(ROOT)) if str(filepath).startswith(str(ROOT)) else str(filepath)
    if "ordivon-verify" not in rel and "ordivon_verify" not in rel and "public_surface" not in rel:
        return results
    content = "\n".join(lines)
    cl = content.lower()
    def add(pid, sev, risk, cap, ai, gate_exp, gate_obs, expl, fix, blocks):
        results.append(Finding(finding_id=f"ADP3-{pid}-PV", pattern_id=pid, severity=sev,
            risk_level=risk, capability_class=cap, authority_impact=ai,
            gate_expected=gate_exp, gate_observed=gate_obs, file=rel, line=0,
            evidence_snippet=expl[:200], explanation=expl, recommended_fix=fix, blocks_closure=blocks))
    for claim in ["package published", "public repo created", "license activated", "production-ready"]:
        if claim in cl:
            idx = cl.find(claim)
            ctx = cl[max(0,idx-30):idx+len(claim)+30]
            if "not " + claim not in ctx and "no " + claim not in ctx:
                add("ADP3-PV-RELEASE", "blocking", "AP-R1", "C1", "AI-0",
                    "BLOCKED", claim, f"PV doc claims: {claim}", "No release occurred.", True)
                break
    if "the full" in cl and "ordivon" in cl:
        idx = cl.find("the full")
        ctx = cl[max(0,idx-40):idx+60]
        if "not the full" in ctx or "not the entire" in ctx:
            pass  # Safe negation
        else:
            add("ADP3-PV-WEDGE", "blocking", "AP-R1", "C1", "AI-0",
            "BLOCKED", "wedge=core", "PV doc collapses wedge into core.",
            "Ordivon Verify != Ordivon core.", True)
    if "ready" in cl and ("approve" in cl or "production" in cl):
        if "ready_without_authorization" not in cl and "does not authorize" not in cl:
            add("ADP3-PV-READY", "blocking", "AP-R4", "C4", "AI-0",
                "READY_WITHOUT_AUTHORIZATION", "READY as approval",
                "PV doc uses READY as approval.", "Use READY_WITHOUT_AUTHORIZATION.", True)
    return results


# ── CLI ────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="ADP-3 Agentic Pattern Detector")
    parser.add_argument("paths", nargs="+", help="Paths to scan")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--fail-on-blocking", action="store_true", help="Exit non-zero on blocking findings")
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.paths]
    findings, stats = detect(input_paths)

    if args.json:
        output = {"findings": [f.to_dict() for f in findings], "stats": stats}
        print(json.dumps(output, indent=2))
    else:
        print(f"ADP-3 Agentic Pattern Detector")
        print(f"  Scanned: {stats['total_files_scanned']} files")
        print(f"  Findings: {stats['total_findings']}")
        print(f"    blocking: {stats['blocking']}")
        print(f"    degraded: {stats['degraded']}")
        print(f"    warning: {stats['warning']}")
        print(f"    info: {stats['info']}")
        if findings:
            print(f"\n  Findings ({len(findings)}):")
            for f in findings:
                print(f"    [{f.severity.upper()}] {f.pattern_id} {f.file}:{f.line}: {f.explanation}")
        print(f"\n  ADP-2 is local static detection only. Detector PASS is not authorization.")
        print(f"  Absence of findings is not safety proof.")

    if args.fail_on_blocking and stats["blocking"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
