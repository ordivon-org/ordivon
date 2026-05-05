"""Agent Runtime Contract — generates governance context for agent prompts.

Takes a StageManifest and produces a structured governance section that can
be injected into any agent's system prompt. The agent no longer needs to
"read AGENTS.md and figure out boundaries" — the boundaries are declared
by the control plane and enforced by the reconciler.
"""

from __future__ import annotations

from ordivon_verify.control.stage_manifest import StageManifest, RiskClass, AuthorityImpact
from ordivon_verify.control.authority_state import (
    AuthorityState, EvidenceStatus, ReadinessStatus,
    AuthorizationStatus, PolicyStatus,
)


def generate_agent_context(manifest: StageManifest,
                           authority: AuthorityState | None = None) -> str:
    """Generate the governance contract section for an agent's system prompt.

    Returns a markdown string ready for concatenation into a prompt.
    """
    lines = []
    lines.append("## Governance Contract")
    lines.append("")
    lines.append(f"You are operating under Ordivon governance stage **{manifest.stage_id}**.")
    lines.append("")

    # Risk and authority
    risk_desc = {
        RiskClass.AP_R0: "Advisory/documentation only. You may read and write docs, schemas, templates. You must NOT modify production source code, tests, CI, or external interfaces.",
        RiskClass.AP_R1: "Local code changes allowed. You may modify source within allowed_paths. No external effects.",
        RiskClass.AP_R2: "Integration changes. External dependencies may be affected. Extra verification required.",
        RiskClass.AP_R3: "Runtime/external action. Maximum caution. Human approval mandatory for all changes.",
    }
    lines.append(f"**Risk Class**: {manifest.risk_class.value}")
    lines.append(f"> {risk_desc.get(manifest.risk_class, 'Unknown')}")
    lines.append("")

    auth_desc = {
        AuthorityImpact.AI_0: "current_truth only — you may update status docs but NOT create policy",
        AuthorityImpact.AI_1: "governance docs/schemas — you may propose changes to governance artifacts",
        AuthorityImpact.AI_2: "policy proposal — human review required before activation",
        AuthorityImpact.AI_3: "policy activation — human approval mandatory, no exceptions",
    }
    lines.append(f"**Authority Level**: {manifest.authority_impact.value}")
    lines.append(f"> {auth_desc.get(manifest.authority_impact, 'Unknown')}")
    lines.append("")

    # Allowed paths
    lines.append("### ✅ You MAY modify")
    lines.append("")
    for p in manifest.allowed_paths:
        lines.append(f"- `{p}`")
    lines.append("")

    # Forbidden paths
    lines.append("### ❌ You MUST NOT touch")
    lines.append("")
    for p in manifest.forbidden_paths:
        lines.append(f"- `{p}`")
    lines.append("")

    # Forbidden actions
    if manifest.forbidden_actions:
        lines.append("### 🚫 Forbidden actions")
        lines.append("")
        for a in manifest.forbidden_actions:
            lines.append(f"- {a}")
        lines.append("")

    # Required verification
    lines.append("### 🔍 Required verification (must PASS before closure)")
    lines.append("")
    for g in manifest.required_verification:
        lines.append(f"- **{g.gate_id}**: `{g.command}`")
        if g.description:
            lines.append(f"  - {g.description}")
        lines.append(f"  - Failure: {g.on_failure}")
    lines.append("")

    # Closure predicates
    if manifest.closure_predicates:
        lines.append("### 🔒 Closure predicates (all must be satisfied)")
        lines.append("")
        for p in manifest.closure_predicates:
            lines.append(f"- [ ] {p.predicate_id}: {p.description}")
        lines.append("")

    # Authority state (if provided)
    if authority:
        lines.append("### ⚖️ Authority state")
        lines.append("")
        lines.append(f"- Evidence: {authority.evidence.value}")
        lines.append(f"- Readiness: {authority.readiness.value}")
        lines.append(f"- Authorization: {authority.authorization.value}")
        lines.append(f"- Policy: {authority.policy.value}")
        lines.append("")
        lines.append("**Critical**: evidence ≠ approval. READY ≠ authorization. CandidateRule ≠ Policy.")
        lines.append("")

    # Receipt instruction
    lines.append("### 📋 Receipt")
    lines.append("")
    lines.append(f"When your work is complete, a closure receipt will be generated at:")
    lines.append(f"`docs/runtime/{manifest.stage_id}.receipt.json`")
    lines.append("")
    lines.append("The receipt is machine-validated against the closure-receipt JSON Schema.")
    lines.append("It records exactly what files changed, what verification passed, and")
    lines.append("whether any boundaries were violated.")

    return "\n".join(lines)


def generate_handoff_snapshot(
    stage_id: str,
    risk_class: str,
    authority_impact: str,
    head_commit: str,
    dg_entries: int,
    checker_count: int,
    last_verification: str,
    last_receipt: str,
    active_boundaries: list[str],
    entry_docs: list[str],
) -> dict:
    """Generate a machine-readable handoff snapshot for the next agent/dialog.

    This is Ordivon's cross-agent communication protocol — a compact
    state summary that eliminates the need to re-read 193 DG entries.
    """
    return {
        "protocol": "ordivon-handoff-v1",
        "stage_id": stage_id,
        "current_phase": "EG-1",
        "risk_class": risk_class,
        "authority_impact": authority_impact,
        "head_commit": head_commit,
        "dg_entries": dg_entries,
        "checker_count": checker_count,
        "last_verification": last_verification,
        "last_receipt": last_receipt,
        "active_boundaries": active_boundaries,
        "entry_docs": entry_docs,
        "do_not_read": [
            "docs/runtime/pgi-*",
            "docs/product/pgi-*",
            "docs/archive/*",
        ],
    }
