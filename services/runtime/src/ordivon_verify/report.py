"""Ordivon Verify — trust report builder.

Status model, human output, JSON output.
"""

from __future__ import annotations

DISCLAIMER = (
    "READY means selected checks passed; it does not authorize execution, "
    "does not authorize merge, does not authorize deployment, and does not authorize release, "
    "tool use, policy activation, or external action."
)

_CHECK_SURFACES = {
    "receipts": ["claims", "receipts", "tests", "diff", "review"],
    "receipt_integrity": ["claims", "receipts", "tests", "diff", "review"],
    "debt": ["debt"],
    "verification_debt": ["debt"],
    "gates": ["gates"],
    "gate_manifest": ["gates"],
    "docs": ["docs"],
    "document_registry": ["docs"],
    "document_freshness": ["docs"],
    "current_truth": ["docs"],
    "agent_native_evidence": ["claims", "receipts", "tests", "diff", "docs", "gates", "review"],
    "egb3_operating_governance": ["claims", "docs", "gates", "review"],
    "oep_governance": ["claims", "docs", "review"],
    "ownership_manifest": ["docs", "gates", "review"],
    "external_source_registry": ["docs"],
    "agent_claim_bindings": ["claims", "tests", "diff", "receipts", "review"],
    "coding_profile_gate_manifest": ["gates"],
    "release_claim_audit": ["claims", "docs", "gates"],
    "skill_safety": ["claims", "docs", "gates", "review"],
    "memory_content_hygiene": ["claims", "docs", "review"],
    "harness_evidence_import": ["claims", "receipts", "tests", "review"],
}


def determine_status(results: list[dict]) -> str:
    """Determine overall status: READY, DEGRADED, or BLOCKED."""
    has_fail = any(r["status"] == "FAIL" for r in results)
    has_warn = any(r["status"] == "WARN" for r in results)
    if has_fail:
        return "BLOCKED"
    if has_warn:
        return "DEGRADED"
    return "READY"


def _severity(status: str) -> str:
    if status == "FAIL":
        return "hard"
    if status == "WARN":
        return "warning"
    return "info"


def _surfaces_for(check_id: str) -> list[str]:
    return list(_CHECK_SURFACES.get(check_id, [check_id]))


def _missing_evidence(results: list[dict]) -> list[dict]:
    missing = []
    for r in results:
        if not r.get("missing_evidence"):
            continue
        missing.append(
            {
                "check": r["id"],
                "surfaces": _surfaces_for(r["id"]),
                "reason": r.get("stderr", "Evidence missing or not configured."),
                "next_action": r.get("next_action", f"Configure {r['label'].lower()} evidence."),
            }
        )
    return missing


def _surface_summary(results: list[dict]) -> dict:
    surfaces: dict[str, dict] = {
        name: {"status": "NOT_APPLICABLE", "checks": []}
        for name in ("claims", "receipts", "tests", "diff", "debt", "docs", "gates", "review")
    }
    for r in results:
        for surface in _surfaces_for(r["id"]):
            entry = surfaces.setdefault(surface, {"status": "NOT_APPLICABLE", "checks": []})
            entry["checks"].append(r["id"])
            status = r["status"]
            if status == "FAIL":
                entry["status"] = "FAIL"
            elif status == "WARN" and entry["status"] != "FAIL":
                entry["status"] = "MISSING_EVIDENCE" if r.get("missing_evidence") else "WARN"
            elif status == "PASS" and entry["status"] == "NOT_APPLICABLE":
                entry["status"] = "PASS"
    return surfaces


def _top_findings(hard_failures: list[dict], missing: list[dict], warnings: list[dict]) -> list[dict]:
    findings = []
    represented = set()
    for item in hard_failures[:7]:
        represented.add(item.get("check") or item.get("id"))
        findings.append(
            {
                "severity": "blocker",
                "id": item.get("id", item.get("check", "failure")),
                "surface": ", ".join(_surfaces_for(item.get("check", ""))) or "unknown",
                "reason": item.get("reason", "Hard failure"),
                "next_action": item.get("next_action", "Review checker output."),
            }
        )
    for item in missing:
        if len(findings) >= 7:
            break
        if item.get("check") in represented:
            continue
        represented.add(item.get("check"))
        findings.append(
            {
                "severity": "missing_evidence",
                "id": item.get("check", "missing_evidence"),
                "surface": ", ".join(item.get("surfaces", [])) or "unknown",
                "reason": item.get("reason", "Evidence missing."),
                "next_action": item.get("next_action", "Add evidence or record an explicit boundary."),
            }
        )
    filtered_warnings = [
        item for item in warnings if item.get("check") not in represented and item.get("id") not in represented
    ]
    for item in filtered_warnings[: max(0, 7 - len(findings))]:
        findings.append(
            {
                "severity": "warning",
                "id": item.get("id", item.get("check", "warning")),
                "surface": ", ".join(_surfaces_for(item.get("check", ""))) or "unknown",
                "reason": item.get("reason", "Warning"),
                "next_action": item.get("next_action", "Review warning."),
            }
        )
    return findings


def build_report(
    results: list[dict],
    mode: str,
    root: str,
    config_path: str | None,
    profile_context: dict | None = None,
    evidence_appendix: dict | None = None,
) -> dict:
    """Build JSON-serializable trust report dict."""
    status = determine_status(results)
    hard_failures = []
    warn_entries = []

    for r in results:
        if r["status"] == "FAIL":
            sub_failures = r.get("failures", [])
            if sub_failures:
                for sf in sub_failures:
                    hard_failures.append(
                        {
                            "id": sf["id"],
                            "check": r["id"],
                            "file": sf["file"],
                            "line": sf.get("line", 0),
                            "reason": sf["reason"],
                            "why_it_matters": sf["why_it_matters"],
                            "next_action": sf["next_action"],
                        }
                    )
            else:
                hard_failures.append(
                    {
                        "id": r["id"],
                        "check": r["id"],
                        "reason": r.get("stderr", "Checker failed"),
                        "why_it_matters": "A hard verification gate failed.",
                        "next_action": r.get("next_action", f"Review {r['label'].lower()} checker output."),
                    }
                )
        elif r["status"] == "WARN":
            warn_entries.append(
                {
                    "id": r["id"],
                    "check": r["id"],
                    "reason": r.get("stderr", "Warning"),
                    "next_action": r.get("next_action", f"Configure {r['label'].lower()} when ready."),
                }
            )

    missing = _missing_evidence(results)
    profile_context = profile_context or {
        "pack": "coding",
        "profile": "ai_coding_trust_audit",
        "risk_stage": "vibe" if mode == "advisory" else "merge",
    }
    return {
        "tool": "ordivon-verify",
        "schema_version": "0.1",
        "status": status,
        "trust_signal": "READY_WITHOUT_AUTHORIZATION" if status == "READY" else status,
        "pack": profile_context.get("pack", "coding"),
        "profile": profile_context.get("profile", "ai_coding_trust_audit"),
        "risk_stage": profile_context.get("risk_stage", "vibe"),
        "mode": mode,
        "root": root,
        "config": config_path,
        "checks": [
            {
                "id": r["id"],
                "status": r["status"],
                "severity": _severity(r["status"]),
                "summary": (r["stdout"].split("\n")[-1] if r["stdout"] else (r.get("stderr", "") or "no output")),
                "exit_code": r["exit_code"],
            }
            for r in results
        ],
        "surfaces": _surface_summary(results),
        "hard_failures": hard_failures,
        "warnings": warn_entries,
        "missing_evidence": missing,
        "top_findings": _top_findings(hard_failures, missing, warn_entries),
        "evidence_appendix": evidence_appendix or {},
        "disclaimer": DISCLAIMER,
    }


def render_summary(report: dict) -> str:
    """Render a compact trust report for humans."""
    lines = [
        "## Ordivon Verify Summary",
        "",
        f"**Status:** {report['status']}",
        f"**Trust signal:** {report['trust_signal']}",
        f"**Profile:** `{report.get('profile', 'ai_coding_trust_audit')}`",
        f"**Risk stage:** `{report.get('risk_stage', 'vibe')}`",
        "",
        "### Top Findings",
        "",
    ]
    top = report.get("top_findings", [])[:5]
    if top:
        for item in top:
            lines.append(f"- **{item['severity']} / {item['surface']}**: {item['reason']}")
            if item.get("next_action"):
                lines.append(f"  - Next action: {item['next_action']}")
    else:
        lines.append("- No blocking or missing-evidence findings in selected checks.")
    missing = report.get("missing_evidence", [])[:5]
    if missing:
        lines.extend(["", "### Missing Evidence", ""])
        for item in missing:
            surfaces_text = ", ".join(item.get("surfaces", [])) or "unknown"
            lines.append(f"- **{item['check']}** ({surfaces_text})")
    lines.extend(
        [
            "",
            "### Next Action",
            "",
        ]
    )
    if report["status"] == "READY":
        lines.append("- Record evidence status; project owner/reviewer still decides any action.")
    elif report["status"] == "DEGRADED":
        lines.append("- Add missing evidence, downgrade the claim, or record explicit debt.")
    else:
        lines.append("- Repair blockers before presenting the AI work claim as trustworthy.")
    lines.extend(["", f"> {report['disclaimer']}"])
    return "\n".join(lines) + "\n"


def render_markdown(report: dict, full: bool = False) -> str:
    """Render a PR-pasteable Markdown trust report."""
    lines = [
        "## Ordivon Verify Trust Report",
        "",
        f"**Status:** {report['status']}",
        f"**Trust signal:** {report['trust_signal']}",
        f"**Profile:** `{report.get('profile', 'ai_coding_trust_audit')}`",
        f"**Risk stage:** `{report.get('risk_stage', 'vibe')}`",
        f"**Mode:** {report['mode']}",
        f"**Root:** `{report['root']}`",
    ]
    if report.get("config"):
        lines.append(f"**Config:** `{report['config']}`")
    lines.extend(
        [
            "",
            "### Surfaces",
            "",
            "| Surface | Status | Checks |",
            "|---|---|---|",
        ]
    )
    surfaces = report.get("surfaces", {})
    for surface in ("claims", "receipts", "tests", "diff", "debt", "docs", "gates", "review"):
        entry = surfaces.get(surface, {"status": "NOT_APPLICABLE", "checks": []})
        checks = ", ".join(entry.get("checks", [])) or "-"
        lines.append(f"| {surface} | {entry.get('status', 'NOT_APPLICABLE')} | {checks} |")

    if report.get("top_findings"):
        lines.extend(["", "### Top Findings", ""])
        for item in report["top_findings"][:7]:
            lines.append(f"- **{item['severity']} / {item['surface']}**: {item['reason']}")
            if item.get("next_action"):
                lines.append(f"  - Next action: {item['next_action']}")

    appendix = report.get("evidence_appendix", {})
    bindings = appendix.get("agent_claim_bindings", {})
    gates = appendix.get("gate_manifest_candidates", [])
    if bindings or gates:
        lines.extend(["", "### Adoption Boundaries", ""])
        if bindings:
            counts = bindings.get("status_counts", {})
            lines.append(
                "- Claim/evidence/review: "
                f"{bindings.get('count', 0)} binding(s), "
                f"READY_WITHOUT_AUTHORIZATION {counts.get('READY_WITHOUT_AUTHORIZATION', 0)}, "
                f"DEGRADED {counts.get('DEGRADED', 0)}, BLOCKED {counts.get('BLOCKED', 0)}."
            )
        if gates:
            canonical_like = sum(1 for gate in gates if gate.get("canonical_confidence") == "high")
            blocked_as_canonical = sum(1 for gate in gates if gate.get("canonical_confidence") == "not_canonical")
            lines.append(
                "- Candidate vs canonical gates: "
                f"{len(gates)} candidate(s), {canonical_like} likely verification candidate(s), "
                f"{blocked_as_canonical} write/deploy surface(s); owner/reviewer confirmation is still required."
            )
        lines.append(
            "- Evidence is not approval; discovery candidates are hints until confirmed by the target project."
        )

    if report.get("hard_failures"):
        lines.extend(["", "### Hard Failures", ""])
        for failure in report["hard_failures"]:
            file_part = f" `{failure['file']}`" if failure.get("file") else ""
            line_part = f":{failure['line']}" if failure.get("line") else ""
            lines.append(f"- **{failure['id']}**{file_part}{line_part}: {failure.get('reason', 'Checker failed')}")
            if failure.get("next_action"):
                lines.append(f"  - Next action: {failure['next_action']}")

    if report.get("missing_evidence"):
        lines.extend(["", "### Missing Evidence", ""])
        for item in report["missing_evidence"]:
            surfaces_text = ", ".join(item.get("surfaces", [])) or "unknown"
            lines.append(f"- **{item['check']}** ({surfaces_text}): {item.get('reason', 'Evidence missing')}")
            if item.get("next_action"):
                lines.append(f"  - Next action: {item['next_action']}")

    if report.get("warnings"):
        lines.extend(["", "### Warnings", ""])
        for warning in report["warnings"]:
            lines.append(f"- **{warning['id']}**: {warning.get('reason', 'Warning')}")
            if warning.get("next_action"):
                lines.append(f"  - Next action: {warning['next_action']}")

    if full and report.get("evidence_appendix"):
        appendix = report["evidence_appendix"]
        lines.extend(["", "### Evidence Appendix", ""])
        bindings = appendix.get("agent_claim_bindings", {})
        if bindings:
            lines.append(
                f"- Agent claim bindings: {bindings.get('count', 0)} "
                f"(file: `{bindings.get('binding_file') or 'not found'}`)"
            )
        release = appendix.get("release_claim_audit", {})
        if release:
            counts = release.get("status_counts", {})
            lines.append(
                "- Release claims: "
                f"supported {counts.get('supported', 0)}, partial {counts.get('partial', 0)}, "
                f"missing {counts.get('missing', 0)}, blocked {counts.get('blocked', 0)}"
            )
        skills = appendix.get("skills", {})
        if skills:
            counts = skills.get("status_counts", {})
            lines.append(
                "- Skill safety: "
                f"PASS {counts.get('PASS', 0)}, WARN {counts.get('WARN', 0)}, FAIL {counts.get('FAIL', 0)}"
            )
        memory = appendix.get("memory_content_hygiene", {})
        if memory:
            counts = memory.get("status_counts", {})
            lines.append(
                "- Memory/content hygiene: "
                f"READY_WITHOUT_AUTHORIZATION {counts.get('READY_WITHOUT_AUTHORIZATION', 0)}, "
                f"DEGRADED {counts.get('DEGRADED', 0)}, BLOCKED {counts.get('BLOCKED', 0)}"
            )
        harness = appendix.get("harness_evidence_import", {})
        if harness:
            counts = harness.get("status_counts", {})
            lines.append(
                "- Harness evidence import: "
                f"READY_WITHOUT_AUTHORIZATION {counts.get('READY_WITHOUT_AUTHORIZATION', 0)}, "
                f"DEGRADED {counts.get('DEGRADED', 0)}, BLOCKED {counts.get('BLOCKED', 0)}"
            )
        gates = appendix.get("gate_manifest_candidates", [])
        if gates:
            lines.append(f"- Gate candidates: {len(gates)} discovered; owner confirmation still required.")
        risk = appendix.get("agent_native_risk_matrix", [])
        if risk:
            lines.append(f"- Agent-native risk surfaces: {len(risk)}")

    lines.extend(
        [
            "",
            "### Recommended Next Action",
            "",
        ]
    )
    if report["status"] == "READY":
        lines.append("- Record the evidence status. Do not treat READY as permission for action.")
    elif report["status"] == "DEGRADED":
        lines.append(
            "- Review missing evidence and decide whether to add evidence or keep an explicit review boundary."
        )
    else:
        lines.append("- Fix hard failures before claiming the agent work is complete or trustworthy.")
    lines.extend(["", f"> {report['disclaimer']}"])
    return "\n".join(lines) + "\n"


def print_human(results: list[dict], mode: str, root: str, config_path: str | None) -> None:
    """Print human-readable trust report."""
    status = determine_status(results)
    print("ORDIVON VERIFY")
    print(f"Status:  {status}")
    if status == "READY":
        print("Signal:  READY_WITHOUT_AUTHORIZATION")
    print(f"Mode:    {mode}")
    print(f"Root:    {root}")
    if config_path:
        print(f"Config:  {config_path}")
    print()

    print("Checks:")
    for r in results:
        if r["status"] == "PASS":
            icon, label_status = "\u2713", ""
        elif r["status"] == "WARN":
            icon, label_status = "\u26a0", " (not configured)"
        else:
            icon, label_status = "\u2717", ""
        print(f"  {r['label'].lower()}: {icon} {r['status']}{label_status}")

    surfaces = _surface_summary(results)
    print("\nSurfaces:")
    for surface in ("claims", "receipts", "tests", "diff", "debt", "docs", "gates", "review"):
        entry = surfaces.get(surface, {"status": "NOT_APPLICABLE"})
        print(f"  {surface}: {entry['status']}")

    failures = [r for r in results if r["status"] == "FAIL"]
    if failures:
        print("\nHard failures:")
        for f in failures:
            sub = f.get("failures", [])
            if sub:
                for sf in sub:
                    print(f"  {sf['id']}")
                    print(f"    File:    {sf['file']}")
                    print(f"    Line:    {sf.get('line', '?')}")
                    print(f"    Reason:  {sf['reason']}")
                    print(f"    Why:     {sf['why_it_matters']}")
                    print(f"    Action:  {sf['next_action']}")
                    print()
            else:
                print(f"  {f['id']}")
                reason = f.get("stderr", "Checker failed")
                print(f"    Reason:  {reason}")
                print()

    warns = [r for r in results if r["status"] == "WARN"]
    if warns:
        print("Warnings:")
        for w in warns:
            print(f"  {w['id']}")
            print(f"    Reason:  {w.get('stderr', 'Warning')}")
            na = w.get("next_action", "")
            if na:
                print(f"    Action:  {na}")
            print()

    missing = _missing_evidence(results)
    if missing:
        print("Missing evidence:")
        for item in missing:
            print(f"  {item['check']}: {', '.join(item['surfaces'])}")
            print(f"    Reason:  {item['reason']}")
            print(f"    Action:  {item['next_action']}")
        print()

    if failures or warns:
        print("Next suggested action:")
        if failures:
            print("  - Fix hard failures above. They block CI / trust.")
        if warns:
            print("  - Address warnings before moving to a stricter mode.")
        print()

    print(DISCLAIMER)
    print()


def status_to_exit_code(status: str) -> int:
    """Map status string to exit code."""
    return {"READY": 0, "BLOCKED": 1, "DEGRADED": 2, "NEEDS_REVIEW": 2}.get(status, 1)
