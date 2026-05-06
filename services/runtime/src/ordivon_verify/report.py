"""Ordivon Verify — trust report builder.

Status model, human output, JSON output.
"""

from __future__ import annotations

DISCLAIMER = (
    "READY means selected checks passed; it does not authorize execution, "
    "does not authorize merge, does not authorize deployment, and does not authorize external action."
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
        missing.append({
            "check": r["id"],
            "surfaces": _surfaces_for(r["id"]),
            "reason": r.get("stderr", "Evidence missing or not configured."),
            "next_action": r.get("next_action", f"Configure {r['label'].lower()} evidence."),
        })
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


def build_report(results: list[dict], mode: str, root: str, config_path: str | None) -> dict:
    """Build JSON-serializable trust report dict."""
    status = determine_status(results)
    hard_failures = []
    warn_entries = []

    for r in results:
        if r["status"] == "FAIL":
            sub_failures = r.get("failures", [])
            if sub_failures:
                for sf in sub_failures:
                    hard_failures.append({
                        "id": sf["id"],
                        "check": r["id"],
                        "file": sf["file"],
                        "line": sf.get("line", 0),
                        "reason": sf["reason"],
                        "why_it_matters": sf["why_it_matters"],
                        "next_action": sf["next_action"],
                    })
            else:
                hard_failures.append({
                    "id": r["id"],
                    "check": r["id"],
                    "reason": r.get("stderr", "Checker failed"),
                    "why_it_matters": "A hard verification gate failed.",
                    "next_action": f"Review {r['label'].lower()} checker output.",
                })
        elif r["status"] == "WARN":
            warn_entries.append({
                "id": r["id"],
                "check": r["id"],
                "reason": r.get("stderr", "Warning"),
                "next_action": r.get("next_action", f"Configure {r['label'].lower()} when ready."),
            })

    return {
        "tool": "ordivon-verify",
        "schema_version": "0.1",
        "status": status,
        "trust_signal": "READY_WITHOUT_AUTHORIZATION" if status == "READY" else status,
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
        "missing_evidence": _missing_evidence(results),
        "disclaimer": DISCLAIMER,
    }


def render_markdown(report: dict) -> str:
    """Render a PR-pasteable Markdown trust report."""
    lines = [
        "## Ordivon Verify Trust Report",
        "",
        f"**Status:** {report['status']}",
        f"**Trust signal:** {report['trust_signal']}",
        f"**Mode:** {report['mode']}",
        f"**Root:** `{report['root']}`",
    ]
    if report.get("config"):
        lines.append(f"**Config:** `{report['config']}`")
    lines.extend([
        "",
        "### Surfaces",
        "",
        "| Surface | Status | Checks |",
        "|---|---|---|",
    ])
    surfaces = report.get("surfaces", {})
    for surface in ("claims", "receipts", "tests", "diff", "debt", "docs", "gates", "review"):
        entry = surfaces.get(surface, {"status": "NOT_APPLICABLE", "checks": []})
        checks = ", ".join(entry.get("checks", [])) or "-"
        lines.append(f"| {surface} | {entry.get('status', 'NOT_APPLICABLE')} | {checks} |")

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

    lines.extend([
        "",
        "### Recommended Next Action",
        "",
    ])
    if report["status"] == "READY":
        lines.append("- Record the evidence status. Do not treat READY as action authorization.")
    elif report["status"] == "DEGRADED":
        lines.append("- Review missing evidence and decide whether to add evidence or keep an explicit review boundary.")
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
