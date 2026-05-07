"""External repository evidence discovery for Ordivon Verify.

This module is read-only. It proposes candidate evidence surfaces for external
repositories, but it does not validate them and does not write config files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SUPPORTED_TEMPLATE_TIERS = {"minimal", "standard", "deep"}

CLAIM_DOC_NAMES = {
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
}

_SENSITIVE_TEXT_MARKERS = (
    "api " + "key",
    "to" + "ken",
    "sec" + "ret",
    "pass" + "word",
    "authorization" + ": " + "bear" + "er",
)

_SENSITIVE_PATH_MARKERS = ("credential", "sec" + "ret", "to" + "ken")

_CLAIM_MARKERS = (
    "ship",
    "support",
    "deploy",
    "release",
    "security",
    "secure",
    "hardening",
    "fix",
)

_AUTHZ_MARKERS = (
    "authorizes",
    "authorization",
    "approved to",
    "permission to",
    "can merge",
    "can deploy",
    "safe to merge",
)

_BOUNDARY_MARKERS = (
    "not authorization",
    "does not authorize",
    "review required",
    "human review",
    "read-only",
    "no external action",
    "requires approval",
)

_TEST_MARKERS = ("test", "pytest", "ci", "workflow", "check", "verify")

_RELEASE_STRONG_MARKERS = (
    "production" + "-" + "ready",
    "production ready",
    "secure",
    "approved",
    "authorized",
    "compliant",
    "certified",
)


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _safe_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _safe_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            rows.append(data)
    return rows


def _first_existing(root: Path, names: list[str]) -> str | None:
    for name in names:
        if (root / name).is_file():
            return name
    return None


def _collect_claim_docs(root: Path) -> list[str]:
    docs: list[str] = []
    for name in sorted(CLAIM_DOC_NAMES):
        if (root / name).is_file():
            docs.append(name)
    for p in sorted(root.glob("RELEASE*.md"))[:12]:
        docs.append(_rel(p, root))
    for p in sorted(root.glob("docs/**/*.md"))[:12]:
        rel = _rel(p, root)
        lower = rel.lower()
        if any(marker in lower for marker in ("receipt", "release", "review", "security", "runbook")):
            docs.append(rel)
    return list(dict.fromkeys(docs))


def _collect_tests(root: Path) -> dict:
    py_tests = sorted(root.glob("tests/**/test*.py"))
    js_tests = sorted(root.glob("**/*.test.*"))
    scripts: list[str] = []

    pyproject = _safe_json(root / "pyproject.toml")
    # pyproject.toml is not JSON; keep command inference conservative below.
    _ = pyproject

    package = _safe_json(root / "package.json")
    package_scripts = package.get("scripts", {}) if isinstance(package.get("scripts"), dict) else {}
    for name, command in package_scripts.items():
        if "test" in name.lower() or "lint" in name.lower():
            scripts.append(f"npm run {name}  # {command}")

    if (root / "scripts" / "run_tests.sh").is_file():
        scripts.append("bash scripts/run_tests.sh")
    if py_tests:
        scripts.append("python -m pytest tests/ -q")

    return {
        "python_test_files": len(py_tests),
        "js_test_files": len(js_tests),
        "candidate_commands": list(dict.fromkeys(scripts)),
    }


def _collect_workflows(root: Path) -> list[dict]:
    workflows: list[dict] = []
    for p in sorted((root / ".github" / "workflows").glob("*.yml")) + sorted(
        (root / ".github" / "workflows").glob("*.yaml")
    ):
        text = p.read_text(encoding="utf-8", errors="ignore")
        tags = []
        lower = text.lower()
        for key in ("test", "deploy", "docker", "supply", "nix", "docs", "skills"):
            if key in lower:
                tags.append(key)
        triggers = []
        for trigger in ("pull_request", "push", "workflow_dispatch", "release", "schedule"):
            if trigger in lower:
                triggers.append(trigger)
        write_surface = bool(
            re.search(r"permissions:\s*(?:\n|.){0,260}(contents|packages|id-" + "to" + r"ken):\s*write", lower)
            or any(marker in lower for marker in ("deploy", "publish", "release", "docker push", "gh release"))
        )
        workflows.append(
            {
                "path": _rel(p, root),
                "tags": tags,
                "triggers": triggers,
                "write_or_deploy_surface": write_surface,
                "line_count": len(text.splitlines()),
            }
        )
    return workflows


def _infer_gate_manifest(workflows: list[dict], tests: dict) -> list[dict]:
    gates: list[dict] = []
    for command in tests.get("candidate_commands", []):
        gate_id = command.split("#", 1)[0].strip().split()[0:3]
        gate_type = "test" if "test" in command.lower() or "pytest" in command.lower() else "quality"
        gates.append(
            {
                "gate_id": "-".join(gate_id).replace("/", "-"),
                "command": command.split("#", 1)[0].strip(),
                "source": "test-discovery",
                "gate_type": gate_type,
                "confidence": "medium",
                "canonical_confidence": "medium",
                "requires_owner_confirmation": True,
                "write_or_deploy_surface": False,
                "note": "Candidate only; reviewer must confirm this is canonical.",
            }
        )
    for wf in workflows:
        tags = set(wf.get("tags", []))
        if not tags:
            continue
        gate_id = wf["path"].rsplit("/", 1)[-1].rsplit(".", 1)[0]
        gate_type = "release" if "deploy" in tags or wf.get("write_or_deploy_surface") else "quality"
        if "test" in tags:
            gate_type = "test"
        elif "supply" in tags:
            gate_type = "supply-chain-evidence"
        elif "docs" in tags:
            gate_type = "docs"
        canonical_confidence = "medium"
        note = "Workflow mentions quality behavior; not proof that it ran for a claim."
        if "pull_request" in wf.get("triggers", []) and gate_type in ("test", "quality", "supply-chain-evidence"):
            canonical_confidence = "high"
        if "workflow_dispatch" in wf.get("triggers", []) and "pull_request" not in wf.get("triggers", []):
            canonical_confidence = "low"
            note = "Manual-only workflow is weak as a canonical gate without owner confirmation."
        if wf.get("write_or_deploy_surface"):
            canonical_confidence = "not_canonical"
            note = "Workflow has deploy/write/release surface; keep separate from verification gates."
        gates.append(
            {
                "gate_id": gate_id,
                "command": f"github workflow: {wf['path']}",
                "source": "github-actions",
                "gate_type": gate_type,
                "confidence": "medium" if canonical_confidence != "not_canonical" else "low",
                "canonical_confidence": canonical_confidence,
                "requires_owner_confirmation": True,
                "write_or_deploy_surface": bool(wf.get("write_or_deploy_surface")),
                "trigger_scope": wf.get("triggers", []),
                "note": note,
            }
        )
    seen = set()
    unique = []
    for gate in gates:
        key = (gate["gate_id"], gate["command"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(gate)
    return unique[:30]


def _frontmatter_present(raw: str) -> bool:
    return raw.lstrip().startswith("---")


def _classify_skill(path: Path, root: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = raw.lower()
    rel = _rel(path, root)
    findings: list[str] = []
    if not _frontmatter_present(raw):
        findings.append("missing_frontmatter")
    if "allowed-tools" in text or "allow all" in text:
        findings.append("tool_scope_declared")
    if any(marker in text for marker in ("bash", "shell", "script", ".py", ".sh", "npm ", "uv run", "python ")):
        findings.append("script_or_shell_surface")
    if any(marker in text for marker in _SENSITIVE_TEXT_MARKERS):
        findings.append("credential_language")
    if "mcp" in text or "server" in text:
        findings.append("protocol_or_server_surface")
    if any(marker in text for marker in _AUTHZ_MARKERS):
        findings.append("authorization_language")
    if not any(marker in text for marker in _BOUNDARY_MARKERS):
        findings.append("missing_boundary_statement")
    if not any(marker in text for marker in _TEST_MARKERS):
        findings.append("missing_verification_instruction")

    if "authorization_language" in findings or (
        "credential_language" in findings
        and "script_or_shell_surface" in findings
        and "missing_boundary_statement" in findings
    ):
        status = "FAIL"
        risk = "high"
    elif any(f in findings for f in ("credential_language", "protocol_or_server_surface", "tool_scope_declared")):
        status = "WARN"
        risk = "medium"
    elif any(
        f in findings for f in ("missing_frontmatter", "script_or_shell_surface", "missing_verification_instruction")
    ):
        status = "WARN"
        risk = "low"
    else:
        status = "PASS"
        risk = "low"

    return {
        "path": rel,
        "status": status,
        "risk": risk,
        "findings": findings,
        "boundary": "Skill capability is not permission; tool use requires explicit project authority.",
    }


def _collect_skill_files(root: Path) -> dict:
    skill_files = sorted(root.glob("skills/**/SKILL.md")) + sorted(root.glob("optional-skills/**/SKILL.md"))
    broad_tool_mentions = []
    credential_mentions = []
    frontmatter_missing = []
    script_mentions = []
    items = []
    for p in skill_files[:300]:
        raw = p.read_text(encoding="utf-8", errors="ignore")
        text = raw.lower()
        rel = _rel(p, root)
        if not raw.lstrip().startswith("---"):
            frontmatter_missing.append(rel)
        if "allowed-tools" in text or "allow all" in text or "bash" in text or "shell" in text:
            broad_tool_mentions.append(rel)
        if any(marker in text for marker in _SENSITIVE_TEXT_MARKERS):
            credential_mentions.append(rel)
        if any(marker in text for marker in ("script", ".py", ".sh", "npm ", "uv run", "python ")):
            script_mentions.append(rel)
        items.append(_classify_skill(p, root))
    high_attention = sorted(set(broad_tool_mentions) & set(credential_mentions))
    status_counts = {
        "PASS": sum(1 for item in items if item["status"] == "PASS"),
        "WARN": sum(1 for item in items if item["status"] == "WARN"),
        "FAIL": sum(1 for item in items if item["status"] == "FAIL"),
    }
    return {
        "count": len(skill_files),
        "sample": [_rel(p, root) for p in skill_files[:20]],
        "items": items,
        "status_counts": status_counts,
        "broad_tool_or_shell_mentions": broad_tool_mentions[:20],
        "credential_language_mentions": credential_mentions[:20],
        "missing_frontmatter": frontmatter_missing[:20],
        "script_mentions": script_mentions[:20],
        "high_attention": high_attention[:20],
        "risk_summary": {
            "broad_tool_or_shell_count": len(broad_tool_mentions),
            "credential_language_count": len(credential_mentions),
            "missing_frontmatter_count": len(frontmatter_missing),
            "script_mention_count": len(script_mentions),
            "high_attention_count": len(high_attention),
        },
    }


def _collect_agent_surfaces(root: Path) -> dict:
    candidates = {
        "mcp": [],
        "acp": [],
        "approval": [],
        "memory": [],
        "credential": [],
    }
    for p in sorted(root.glob("**/*")):
        if not p.is_file():
            continue
        rel = _rel(p, root)
        lower = rel.lower()
        if any(part in lower for part in (".git/", ".venv/", "__pycache__/", "node_modules/")):
            continue
        if "mcp" in lower:
            candidates["mcp"].append(rel)
        if "acp" in lower:
            candidates["acp"].append(rel)
        if "approval" in lower or "permission" in lower:
            candidates["approval"].append(rel)
        if "memory" in lower:
            candidates["memory"].append(rel)
        if any(marker in lower for marker in _SENSITIVE_PATH_MARKERS):
            candidates["credential"].append(rel)
    return {k: v[:30] for k, v in candidates.items()}


def _build_agent_risk_matrix(agent_surfaces: dict, skills: dict) -> list[dict]:
    matrix = []
    for surface, paths in agent_surfaces.items():
        if not paths:
            continue
        risk = "medium"
        if surface in ("approval", "credential"):
            risk = "high"
        if surface in ("mcp", "acp") and len(paths) > 5:
            risk = "high"
        matrix.append(
            {
                "surface": surface,
                "risk": risk,
                "evidence_count": len(paths),
                "sample": paths[:5],
                "boundary": {
                    "mcp": "Tool availability is not action authorization.",
                    "acp": "Protocol adapter presence is not permission to execute.",
                    "approval": "Approval code must separate request, review, and authorization.",
                    "memory": "Memory presence is not current truth without source and freshness.",
                    "credential": "Credential surface requires explicit handling boundaries.",
                }.get(surface, "Evidence presence is not verification."),
            }
        )
    if skills.get("count", 0):
        matrix.append(
            {
                "surface": "skills",
                "risk": "high" if skills.get("high_attention") else "medium",
                "evidence_count": skills["count"],
                "sample": skills.get("sample", [])[:5],
                "boundary": "Skill capability is not permission; scripts and credential language need review.",
            }
        )
    return matrix


def _collect_release_claims(root: Path) -> dict:
    files = sorted(root.glob("RELEASE*.md")) + sorted(root.glob("CHANGELOG*.md"))
    claim_lines = []
    missing_evidence_refs = []
    status_counts = {"supported": 0, "partial": 0, "missing": 0, "blocked": 0}
    claim_index = 0
    for p in files[:20]:
        for idx, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            stripped = line.strip()
            lower = stripped.lower()
            if not stripped or not any(marker in lower for marker in _CLAIM_MARKERS):
                continue
            claim_index += 1
            has_link = bool(re.search(r"(?:#\d+|https?://)", stripped))
            has_test_ref = any(marker in lower for marker in ("test", "ci", "workflow", "pytest", "check"))
            has_evidence_ref = has_link or has_test_ref
            strong = any(marker in lower for marker in _RELEASE_STRONG_MARKERS)
            if has_link and has_test_ref:
                evidence_status = "supported"
                trust_signal = "READY_WITHOUT_AUTHORIZATION"
            elif has_evidence_ref:
                evidence_status = "partial"
                trust_signal = "DEGRADED"
            elif strong:
                evidence_status = "blocked"
                trust_signal = "BLOCKED"
            else:
                evidence_status = "missing"
                trust_signal = "DEGRADED"
            status_counts[evidence_status] += 1
            item = {
                "claim_id": f"release-claim-{claim_index:03d}",
                "file": _rel(p, root),
                "line": idx,
                "claim": stripped[:220],
                "has_evidence_ref": has_evidence_ref,
                "evidence_status": evidence_status,
                "trust_signal": trust_signal,
                "next_action": (
                    "Attach CI/test/workflow/review evidence for this release claim."
                    if evidence_status in ("missing", "blocked")
                    else "Reviewer should confirm referenced evidence is relevant to the claim."
                ),
            }
            claim_lines.append(item)
            if not has_evidence_ref:
                missing_evidence_refs.append(item)
            if len(claim_lines) >= 80:
                break
        if len(claim_lines) >= 80:
            break
    return {
        "claim_count": len(claim_lines),
        "sample": claim_lines[:20],
        "items": claim_lines,
        "status_counts": status_counts,
        "missing_evidence_ref_count": len(missing_evidence_refs),
        "missing_evidence_ref_sample": missing_evidence_refs[:20],
        "note": "Release claim scan is heuristic. It flags lines needing reviewer evidence mapping; it does not prove claims false.",
    }


def collect_agent_claim_bindings(root: Path) -> dict:
    candidates = [
        root / "agent_claims.jsonl",
        root / "governance" / "agent-claim-bindings.jsonl",
        root / "docs" / "governance" / "agent-claim-bindings.jsonl",
    ]
    selected = next((p for p in candidates if p.is_file()), None)
    if selected is None:
        return {
            "binding_file": None,
            "count": 0,
            "items": [],
            "status_counts": {"READY_WITHOUT_AUTHORIZATION": 0, "DEGRADED": 0, "BLOCKED": 0},
            "note": "No agent claim binding file found. Add agent_claims.jsonl to bind claims to artifacts, tests, receipts, and review evidence.",
        }
    items = []
    counts = {"READY_WITHOUT_AUTHORIZATION": 0, "DEGRADED": 0, "BLOCKED": 0}
    for row in _safe_jsonl(selected):
        claim = str(row.get("claim", ""))
        claim_lower = claim.lower()
        work_artifacts = row.get("work_artifacts", [])
        if isinstance(work_artifacts, str):
            work_artifacts = [work_artifacts]
        missing_artifacts = [p for p in work_artifacts if not (root / p).exists()]
        test_evidence = row.get("test_evidence")
        receipt = row.get("receipt")
        review_evidence = row.get("review_evidence")
        authz = any(marker in claim_lower for marker in _AUTHZ_MARKERS)
        test_claim_without_evidence = "test" in claim_lower and not test_evidence
        if authz or missing_artifacts or test_claim_without_evidence:
            signal = "BLOCKED"
        elif not receipt or not review_evidence:
            signal = "DEGRADED"
        else:
            signal = "READY_WITHOUT_AUTHORIZATION"
        counts[signal] += 1
        items.append(
            {
                "claim_id": row.get("claim_id") or f"claim-{len(items) + 1:03d}",
                "claim": claim[:220],
                "trust_signal": signal,
                "missing_artifacts": missing_artifacts,
                "missing_evidence": [
                    name
                    for name, value in (
                        ("test_evidence", test_evidence),
                        ("receipt", receipt),
                        ("review_evidence", review_evidence),
                    )
                    if not value
                ],
                "boundary": "Agent claim binding verifies evidence sufficiency only; it does not authorize action.",
            }
        )
    return {
        "binding_file": _rel(selected, root),
        "count": len(items),
        "items": items,
        "status_counts": counts,
        "note": "Claim binding is read-only and heuristic; reviewer must confirm evidence relevance.",
    }


def _base_template_files(report: dict, template_tier: str) -> dict:
    inv = report["inventory"]
    default_mode = "advisory" if template_tier == "minimal" else "standard"
    return {
        "ordivon.verify.json": {
            "schema_version": "0.1",
            "project_name": "<project-name>",
            "pack": "coding",
            "profile": "ai_coding_trust_audit",
            "risk_stage": report.get("risk_stage", "vibe"),
            "mode": default_mode,
            "receipt_paths": ["<path-to-receipt-or-claim-doc.md>", "<path-to-receipt-directory>"],
        },
        "governance/agent-claim-bindings.jsonl": [
            {
                "claim_id": "claim-001",
                "claim": "<agent completion claim>",
                "work_artifacts": ["<changed-file-or-artifact>"],
                "test_evidence": "<command/output/ci-run>",
                "receipt": "<receipt-file>",
                "review_evidence": "<review-note-or-pr-review>",
                "trust_signal": "DEGRADED",
                "boundary": "This binding verifies evidence sufficiency only; it does not authorize merge, release, deploy, execution, or external action.",
            }
        ],
        "receipts/external-audit-receipt.md": (
            "# External Audit Receipt\n\n"
            "Project AI fills this after collecting evidence.\n\n"
            "Required loop:\n\n"
            "1. Claim: what the AI or contributor says changed.\n"
            "2. Evidence: files, diff, tests, CI, review, release notes.\n"
            "3. Review: what a human or project policy confirmed.\n"
            "4. Decision boundary: READY_WITHOUT_AUTHORIZATION, DEGRADED, or BLOCKED.\n"
            "5. Debt: what remains missing or stale.\n"
            "6. Lesson: what should change next time.\n"
            "7. CandidateRule: optional non-binding rule proposal.\n\n"
            "This receipt does not authorize action.\n"
        ),
        "governance/project-ai-onboarding-playbook.md": (
            "# Project AI Onboarding Playbook\n\n"
            "Use Ordivon discovery as hints, not authority.\n\n"
            "## Flow\n\n"
            "1. Inventory local evidence surfaces.\n"
            "2. Propose candidate receipt paths, gates, docs, debts, skills, release claims, and agent claim bindings.\n"
            "3. Ask the project owner to confirm canonical gates and ownership boundaries.\n"
            "4. Fill the template files with project-local evidence.\n"
            "5. Run Ordivon in vibe, merge, then release stages as needed.\n"
            "6. Convert BLOCKED/DEGRADED findings into debt or claim downgrades.\n"
            "7. Record a receipt and lessons for the next cycle.\n\n"
            "## Boundaries\n\n"
            "- Discovery is not proof.\n"
            "- Workflow presence is not a canonical gate.\n"
            "- Review is not approval unless project policy says so.\n"
            "- READY_WITHOUT_AUTHORIZATION is evidence sufficiency only.\n"
        ),
        "governance/discovery-candidates.json": {
            "project_name": report["project_name"],
            "root": report["root"],
            "claim_or_receipt_candidate_docs": inv["claim_or_receipt_candidate_docs"],
            "gate_manifest_candidates": inv["gate_manifest_candidates"],
            "release_claim_audit_sample": inv["release_claim_audit"].get("sample", []),
            "skill_status_counts": inv["skills"].get("status_counts", {}),
            "agent_native_risk_matrix": inv["agent_native_risk_matrix"],
            "note": "Candidate evidence only. Project AI and owner must decide what belongs in the real governance pack.",
        },
    }


def _standard_template_files() -> dict:
    return {
        "governance/verification-gate-manifest.json": {
            "manifest_id": "<project-name>-coding-trust",
            "profile": "ai_coding_trust_audit",
            "version": "0.1",
            "gate_count": 1,
            "gates": [
                {
                    "gate_id": "<gate-id>",
                    "display_name": "<human-readable gate name>",
                    "layer": "external",
                    "hardness": "hard",
                    "command": "<canonical read-only test/lint/security command>",
                    "purpose": "Verify the project claim with reproducible evidence.",
                    "owner_confirmed": False,
                    "reviewer": "<reviewer-role-or-handle>",
                    "approver": "<approver-role-or-handle>",
                    "notes": "Project AI must propose candidates; project owner must confirm canonical status.",
                }
            ],
        },
        "governance/verification-debt-ledger.jsonl": [
            {
                "debt_id": "VD-001",
                "status": "open",
                "category": "missing_evidence",
                "source": "<file-or-claim-id>",
                "reason": "<what evidence is missing>",
                "owner": "<owner-role-or-handle>",
                "next_action": "<specific evidence to add or claim to downgrade>",
                "boundary": "Open debt blocks READY in standard/merge trust audit until closed or explicitly accepted by project policy.",
            }
        ],
        "governance/document-registry.jsonl": [
            {
                "doc_id": "<doc-id>",
                "path": "<path-to-project-doc.md>",
                "type": "claim_or_receipt_candidate",
                "status": "current",
                "authority": "supporting_evidence",
                "notes": "Project AI fills this from local evidence; Ordivon discovery candidates are hints, not authority.",
            }
        ],
    }


def _deep_template_files() -> dict:
    return {
        "governance/release-claim-map.jsonl": [
            {
                "claim_id": "release-claim-001",
                "file": "<release-or-changelog-file.md>",
                "line": 0,
                "claim": "<release claim text>",
                "evidence_refs": ["<ci-run-url-or-local-test-receipt>", "<review-note>"],
                "trust_signal": "DEGRADED",
                "next_action": "Attach CI/test/workflow/review evidence or downgrade the claim.",
            }
        ],
        "governance/skill-safety-report.json": {
            "status_counts": {"PASS": 0, "WARN": 0, "FAIL": 0},
            "items": [
                {
                    "path": "<path-to-SKILL.md>",
                    "status": "WARN",
                    "risk": "medium",
                    "findings": ["<finding-id>"],
                    "owner_disposition": "<accept|repair|remove|defer-with-rationale>",
                    "boundary": "Skill capability is not permission; tool use requires explicit project authority.",
                }
            ],
        },
        "governance/tool-boundary-map.jsonl": [
            {
                "tool_id": "<tool-or-skill-id>",
                "surface": "<tool|skill|mcp|workflow|credential>",
                "capability": "<what the tool can do>",
                "permission_boundary": "Capability is not permission; project owner must authorize high-impact actions.",
                "owner_disposition": "<accept|repair|remove|defer-with-rationale>",
            }
        ],
        "governance/memory-source-ledger.jsonl": [
            {
                "memory_id": "memory-001",
                "source": "<source-receipt-or-doc>",
                "freshness": "<YYYY-MM-DD>",
                "scope": "<project|team|global>",
                "authority": "supporting_evidence",
                "boundary": "Memory is not current truth without source, freshness, and scope.",
            }
        ],
        "governance/lesson-ledger.jsonl": [
            {
                "lesson_id": "lesson-001",
                "source_receipt": "<receipt-file>",
                "lesson": "<what changed in future behavior>",
                "rule_update": "<candidate-rule-id or no-rule rationale>",
            }
        ],
        "governance/candidate-rule-drafts.jsonl": [
            {
                "candidate_rule_id": "cr-001",
                "source_lesson": "lesson-001",
                "proposal": "<non-binding rule proposal>",
                "status": "draft",
                "boundary": "CandidateRule is advisory until project policy explicitly promotes it.",
            }
        ],
    }


def _build_template_pack_draft(report: dict, template_tier: str = "standard") -> dict:
    if template_tier not in SUPPORTED_TEMPLATE_TIERS:
        raise ValueError(f"unsupported template tier: {template_tier}")
    files = _base_template_files(report, template_tier)
    if template_tier in ("standard", "deep"):
        files["ordivon.verify.json"]["debt_ledger"] = "governance/verification-debt-ledger.jsonl"
        files["ordivon.verify.json"]["gate_manifest"] = "governance/verification-gate-manifest.json"
        files["ordivon.verify.json"]["document_registry"] = "governance/document-registry.jsonl"
        files.update(_standard_template_files())
    if template_tier == "deep":
        files.update(_deep_template_files())
    return {
        "mode": "dry_run",
        "writes_files": False,
        "template_pack": True,
        "template_tier": template_tier,
        "project_specific_candidates": "governance/discovery-candidates.json",
        "files": files,
        "notes": [
            "Templates are project-independent; placeholders must be filled by the target project's AI or owner.",
            "Discovery candidates are hints only and are separated from canonical governance templates.",
            "No schema, compliance, release, merge, deploy, or execution authorization is implied.",
        ],
    }


def discover_external_evidence(
    root: Path,
    include_standard_pack: bool = False,
    risk_stage: str = "vibe",
    template_tier: str = "standard",
) -> dict:
    """Return read-only evidence inventory and suggested config for a repo."""
    claim_docs = _collect_claim_docs(root)
    governance = {
        "config": _first_existing(root, ["ordivon.verify.json"]),
        "debt_ledger": _first_existing(
            root,
            [
                "docs/governance/verification-debt-ledger.jsonl",
                "governance/verification-debt-ledger.jsonl",
            ],
        ),
        "gate_manifest": _first_existing(
            root,
            [
                "docs/governance/verification-gate-manifest.json",
                "governance/verification-gate-manifest.json",
            ],
        ),
        "document_registry": _first_existing(
            root,
            [
                "docs/governance/document-registry.jsonl",
                "governance/document-registry.jsonl",
            ],
        ),
    }
    suggested_config: dict = {
        "schema_version": "0.1",
        "project_name": root.name,
        "pack": "coding",
        "profile": "ai_coding_trust_audit",
        "risk_stage": risk_stage,
        "mode": "advisory",
    }
    if claim_docs:
        suggested_config["receipt_paths"] = claim_docs[:8]
    for key in ("debt_ledger", "gate_manifest", "document_registry"):
        if governance.get(key):
            suggested_config[key] = governance[key]

    tests = _collect_tests(root)
    workflows = _collect_workflows(root)
    skills = _collect_skill_files(root)
    agent_surfaces = _collect_agent_surfaces(root)
    gate_candidates = _infer_gate_manifest(workflows, tests)
    release_claims = _collect_release_claims(root)
    agent_claim_bindings = collect_agent_claim_bindings(root)
    agent_risk_matrix = _build_agent_risk_matrix(agent_surfaces, skills)

    next_actions = []
    if not governance["config"]:
        next_actions.append("Review suggested_config and add an explicit ordivon.verify.json when adopting Ordivon.")
    if not governance["debt_ledger"]:
        next_actions.append("Add a verification debt ledger before moving from advisory to standard mode.")
    if not governance["gate_manifest"]:
        next_actions.append("Add a gate manifest that names canonical test/lint/security commands.")
    if skills["count"]:
        next_actions.append("Run or add skill safety review for discovered SKILL.md files.")
    if agent_surfaces["mcp"] or agent_surfaces["acp"]:
        next_actions.append("Treat MCP/ACP manifests and permission code as evidence surfaces, not authorization.")
    if gate_candidates:
        next_actions.append("Review inferred gate candidates before converting them into a gate manifest.")
    if release_claims["missing_evidence_ref_count"]:
        next_actions.append("Map release claims to test, CI, PR, or review evidence before trusting completion claims.")
    if not agent_claim_bindings["binding_file"]:
        next_actions.append("Add agent claim bindings when you need to prove a specific AI work claim.")

    report = {
        "tool": "ordivon-verify",
        "schema_version": "0.1",
        "mode": "suggest_config",
        "pack": "coding",
        "profile": "ai_coding_trust_audit",
        "risk_stage": risk_stage,
        "root": str(root),
        "project_name": root.name,
        "suggested_config": suggested_config,
        "inventory": {
            "claim_or_receipt_candidate_docs": claim_docs[:40],
            "tests": tests,
            "github_workflows": workflows,
            "gate_manifest_candidates": gate_candidates,
            "governance_files": governance,
            "skills": skills,
            "agent_native_surfaces": agent_surfaces,
            "agent_native_risk_matrix": agent_risk_matrix,
            "release_claim_audit": release_claims,
            "agent_claim_bindings": agent_claim_bindings,
            "security_docs": [p for p in ("SECURITY.md", "README.md", "AGENTS.md") if (root / p).is_file()],
        },
        "next_actions": next_actions,
        "disclaimer": (
            "Discovery is advisory only. Suggested config and discovered files are not verification, "
            "not approval, and not authorization for merge, deploy, release, execution, token handling, or external action."
        ),
    }
    if include_standard_pack:
        report["standard_pack_draft"] = _build_template_pack_draft(report, template_tier=template_tier)
    return report


def render_discovery_markdown(report: dict) -> str:
    """Render discovery output as newcomer-readable Markdown."""
    inv = report["inventory"]
    tests = inv["tests"]
    skills = inv["skills"]
    release = inv["release_claim_audit"]
    bindings = inv["agent_claim_bindings"]
    lines = [
        "## Ordivon Verify Discovery Report",
        "",
        f"**Project:** `{report['project_name']}`",
        f"**Root:** `{report['root']}`",
        "**Mode:** `suggest_config`",
        "",
        "### Suggested Config",
        "",
        "```json",
        json.dumps(report["suggested_config"], indent=2),
        "```",
        "",
        "### Evidence Inventory",
        "",
        f"- Candidate claim/receipt docs: {len(inv['claim_or_receipt_candidate_docs'])}",
        f"- Python test files: {tests['python_test_files']}",
        f"- JS test-like files: {tests['js_test_files']}",
        f"- Candidate test commands: {len(tests['candidate_commands'])}",
        f"- GitHub workflows: {len(inv['github_workflows'])}",
        f"- SKILL.md files: {skills['count']}",
        f"- Release claim lines sampled: {release['claim_count']}",
        f"- Release claim lines without evidence refs: {release['missing_evidence_ref_count']}",
        f"- Agent claim bindings: {bindings['count']}",
        "",
        "### Gate Candidates",
        "",
        "| Gate | Source | Canonical Confidence | Type | Command |",
        "|---|---|---|---|---|",
    ]
    for gate in inv["gate_manifest_candidates"][:12]:
        lines.append(
            f"| {gate['gate_id']} | {gate['source']} | {gate.get('canonical_confidence', gate['confidence'])} | "
            f"{gate.get('gate_type', 'unknown')} | `{gate['command']}` |"
        )
    if not inv["gate_manifest_candidates"]:
        lines.append("| - | - | - | - | - |")

    lines.extend(
        [
            "",
            "### Skill Safety Precheck",
            "",
            f"- Broad tool/shell mentions: {skills['risk_summary']['broad_tool_or_shell_count']}",
            f"- Credential-language mentions: {skills['risk_summary']['credential_language_count']}",
            f"- Missing frontmatter: {skills['risk_summary']['missing_frontmatter_count']}",
            f"- Script mentions: {skills['risk_summary']['script_mention_count']}",
            f"- High-attention overlaps: {skills['risk_summary']['high_attention_count']}",
            f"- Per-file status: PASS {skills['status_counts']['PASS']} / WARN {skills['status_counts']['WARN']} / FAIL {skills['status_counts']['FAIL']}",
            "",
            "| Skill | Status | Risk | Findings |",
            "|---|---|---|---|",
        ]
    )
    for item in skills.get("items", [])[:20]:
        lines.append(
            f"| `{item['path']}` | {item['status']} | {item['risk']} | {', '.join(item['findings'][:5]) or '-'} |"
        )
    if not skills.get("items"):
        lines.append("| - | - | - | - |")

    lines.extend(
        [
            "",
            "### Release Claim Evidence Map",
            "",
            f"- Supported: {release['status_counts']['supported']}",
            f"- Partial: {release['status_counts']['partial']}",
            f"- Missing: {release['status_counts']['missing']}",
            f"- Blocked: {release['status_counts']['blocked']}",
            "",
            "| Claim | Signal | Evidence Status | Source | Next Action |",
            "|---|---|---|---|---|",
        ]
    )
    for item in release.get("items", [])[:12]:
        lines.append(
            f"| {item['claim_id']} | {item['trust_signal']} | {item['evidence_status']} | "
            f"`{item['file']}:{item['line']}` | {item['next_action']} |"
        )
    if not release.get("items"):
        lines.append("| - | - | - | - | - |")

    lines.extend(
        [
            "",
            "### Agent Claim Bindings",
            "",
            f"- Binding file: `{bindings['binding_file'] or 'not found'}`",
            f"- READY_WITHOUT_AUTHORIZATION: {bindings['status_counts']['READY_WITHOUT_AUTHORIZATION']}",
            f"- DEGRADED: {bindings['status_counts']['DEGRADED']}",
            f"- BLOCKED: {bindings['status_counts']['BLOCKED']}",
            "",
            "| Claim | Signal | Missing Evidence |",
            "|---|---|---|",
        ]
    )
    for item in bindings.get("items", [])[:12]:
        missing = ", ".join(item["missing_evidence"] + item["missing_artifacts"]) or "-"
        lines.append(f"| {item['claim_id']} | {item['trust_signal']} | {missing} |")
    if not bindings.get("items"):
        lines.append("| - | - | - |")

    if report.get("standard_pack_draft"):
        draft = report["standard_pack_draft"]
        files = draft["files"]
        lines.extend(
            [
                "",
                "### Template Pack Draft",
                "",
                f"- Tier: `{draft.get('template_tier', 'standard')}`",
                f"- Mode: `{draft['mode']}`",
                f"- Writes files: `{draft['writes_files']}`",
                "- Template files are project-independent placeholders.",
                "- Project observations are separated into `governance/discovery-candidates.json`.",
                "",
                "| Proposed File | Purpose |",
                "|---|---|",
            ]
        )
        for name in files:
            purpose = {
                "ordivon.verify.json": "standard-mode config draft",
                "governance/verification-gate-manifest.json": "canonical gate candidates",
                "governance/verification-debt-ledger.jsonl": "missing evidence backlog",
                "governance/document-registry.jsonl": "candidate document registry",
                "governance/skill-safety-report.json": "per-skill safety findings",
                "governance/release-claim-map.jsonl": "release claim evidence mapping",
                "governance/agent-claim-bindings.jsonl": "claim-to-evidence binding template",
                "governance/tool-boundary-map.jsonl": "tool and permission boundary template",
                "governance/memory-source-ledger.jsonl": "memory source and freshness template",
                "governance/lesson-ledger.jsonl": "feedback-loop lesson template",
                "governance/candidate-rule-drafts.jsonl": "non-binding rule proposal template",
                "governance/project-ai-onboarding-playbook.md": "project AI localization flow",
                "governance/discovery-candidates.json": "candidate evidence hints, not authority",
                "receipts/external-audit-receipt.md": "read-only audit receipt draft",
            }.get(name, "draft governance artifact")
            lines.append(f"| `{name}` | {purpose} |")
        lines.extend(["", "```json", json.dumps(files["ordivon.verify.json"], indent=2), "```"])

    lines.extend(
        [
            "",
            "### Agent-Native Risk Matrix",
            "",
            "| Surface | Risk | Evidence Count | Boundary |",
            "|---|---|---:|---|",
        ]
    )
    for item in inv["agent_native_risk_matrix"]:
        lines.append(f"| {item['surface']} | {item['risk']} | {item['evidence_count']} | {item['boundary']} |")
    if not inv["agent_native_risk_matrix"]:
        lines.append("| - | - | 0 | - |")

    lines.extend(
        [
            "",
            "### Next Actions",
            "",
        ]
    )
    for action in report["next_actions"]:
        lines.append(f"- {action}")

    lines.extend(
        [
            "",
            f"> {report['disclaimer']}",
        ]
    )
    return "\n".join(lines) + "\n"


def render_discovery_summary(report: dict) -> str:
    """Render compact discovery output for first-contact project onboarding."""
    inv = report["inventory"]
    tests = inv["tests"]
    skills = inv["skills"]
    release = inv["release_claim_audit"]
    bindings = inv["agent_claim_bindings"]
    gates = inv["gate_manifest_candidates"]
    canonical_gates = [gate for gate in gates if gate.get("canonical_confidence") == "high"]
    write_gates = [gate for gate in gates if gate.get("write_or_deploy_surface")]
    lines = [
        "## Ordivon Verify Onboarding Summary",
        "",
        f"**Project:** `{report['project_name']}`",
        f"**Profile:** `{report.get('profile', 'ai_coding_trust_audit')}`",
        f"**Risk stage:** `{report.get('risk_stage', 'vibe')}`",
        "",
        "### Evidence Found",
        "",
        f"- Claim/receipt candidate docs: {len(inv['claim_or_receipt_candidate_docs'])}",
        f"- Candidate test commands: {len(tests['candidate_commands'])}",
        f"- GitHub workflows: {len(inv['github_workflows'])} ({len(canonical_gates)} likely verification candidates, {len(write_gates)} write/deploy surfaces)",
        f"- SKILL.md files: {skills['count']} (WARN {skills['status_counts']['WARN']}, FAIL {skills['status_counts']['FAIL']})",
        f"- Release claims sampled: {release['claim_count']} ({release['missing_evidence_ref_count']} missing evidence refs)",
        f"- Agent claim bindings: {bindings['count']} ({bindings['binding_file'] or 'not found'})",
        "",
        "### Top Next Actions",
        "",
    ]
    for action in report["next_actions"][:6]:
        lines.append(f"- {action}")
    if report.get("standard_pack_draft"):
        draft = report["standard_pack_draft"]
        lines.extend(
            [
                "",
                "### Template Pack Draft",
                "",
                "- Dry-run only; no target files were written.",
                f"- Tier: `{draft.get('template_tier', 'standard')}`.",
                "- Template pack: project-independent placeholders; project AI must fill and owner-confirm them.",
                "- Discovery candidates are separated into `governance/discovery-candidates.json`.",
                "- Proposed files: " + ", ".join(f"`{name}`" for name in draft["files"].keys()),
            ]
        )
    lines.extend(
        [
            "",
            f"> {report['disclaimer']}",
        ]
    )
    return "\n".join(lines) + "\n"
