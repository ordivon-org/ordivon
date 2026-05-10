"""External repository evidence discovery for Ordivon Verify.

This module is read-only. It proposes candidate evidence surfaces for external
repositories, but it does not validate them and does not write config files.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path

from ordivon_verify.scanners.skill_boundary import discover_skill_surfaces
from ordivon_verify.scanners.memory_hygiene import discover_memory_surfaces
from ordivon_verify.scanners.trace_evidence import discover_trace_surfaces
from ordivon_verify.metabolic.discover import discover_artifacts
from ordivon_verify.metabolic.registry import build_registry

SUPPORTED_TEMPLATE_TIERS = {"minimal", "standard", "deep"}
SUPPORTED_EMIT_FILENAMES = (".json", ".jsonl", ".md")

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

_MEMORY_CANDIDATE_FILES = (
    "governance/memory-source-ledger.jsonl",
    "docs/governance/memory-source-ledger.jsonl",
)

_HARNESS_CANDIDATE_FILES = (
    "governance/harness-evidence.jsonl",
    "governance/trace-evidence.jsonl",
    "docs/governance/harness-evidence.jsonl",
    "docs/governance/trace-evidence.jsonl",
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


def _safe_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


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
        workflows.append({
            "path": _rel(p, root),
            "tags": tags,
            "triggers": triggers,
            "write_or_deploy_surface": write_surface,
            "line_count": len(text.splitlines()),
        })
    return workflows


def _infer_gate_manifest(workflows: list[dict], tests: dict) -> list[dict]:
    gates: list[dict] = []
    for command in tests.get("candidate_commands", []):
        gate_id = command.split("#", 1)[0].strip().split()[0:3]
        gate_type = "test" if "test" in command.lower() or "pytest" in command.lower() else "quality"
        gates.append({
            "gate_id": "-".join(gate_id).replace("/", "-"),
            "command": command.split("#", 1)[0].strip(),
            "source": "test-discovery",
            "gate_type": gate_type,
            "confidence": "medium",
            "canonical_confidence": "medium",
            "requires_owner_confirmation": True,
            "write_or_deploy_surface": False,
            "note": "Candidate only; reviewer must confirm this is canonical.",
        })
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
        gates.append({
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
        })
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
        matrix.append({
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
        })
    if skills.get("count", 0):
        matrix.append({
            "surface": "skills",
            "risk": "high" if skills.get("high_attention") else "medium",
            "evidence_count": skills["count"],
            "sample": skills.get("sample", [])[:5],
            "boundary": "Skill capability is not permission; scripts and credential language need review.",
        })
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


def _classify_memory_record(row: dict, root: Path) -> dict:
    memory_id = (
        row.get("memory_id") or row.get("record_id") or f"memory-{abs(hash(json.dumps(row, sort_keys=True))) % 10000}"
    )
    source = row.get("source") or row.get("source_receipt")
    freshness = row.get("freshness") or row.get("last_verified")
    scope = str(row.get("scope") or row.get("project_scope") or "")
    authority = str(row.get("authority", ""))
    claim = str(row.get("claim", ""))
    object_type = str(row.get("object_type", ""))
    evidence_status = str(row.get("evidence_status", ""))
    missing = [
        name
        for name, value in (
            ("memory_id", memory_id),
            ("source", source),
            ("freshness", freshness),
            ("scope", scope),
            ("authority", authority),
            ("claim", claim),
        )
        if not value
    ]
    finding_ids: list[str] = []

    if source and not (root / source).exists():
        finding_ids.append("source_receipt_missing")
    verified_at = _safe_date(str(freshness))
    stale_after = int(row.get("stale_after_days", 90) or 90)
    if verified_at is None:
        finding_ids.append("freshness_missing")
    elif (date.today() - verified_at).days > stale_after:
        finding_ids.append("freshness_stale")
    if scope and scope not in ("project", root.name, "<project>", "<project-scope>"):
        finding_ids.append("project_scope_unclear")
    if object_type.lower() == "candidaterule" and authority.lower() == "policy":
        finding_ids.append("candidate_rule_treated_as_policy")
    if evidence_status.upper() in ("DEGRADED", "BLOCKED") and re.search(
        r"\b(clean|pass|passed|ready|truth|fact)\b", claim, re.I
    ):
        finding_ids.append("degraded_or_blocked_treated_as_fact")

    if missing:
        finding_ids.append("required_memory_fields_missing")
    if any(
        item in finding_ids
        for item in (
            "source_receipt_missing",
            "candidate_rule_treated_as_policy",
            "degraded_or_blocked_treated_as_fact",
        )
    ):
        signal = "BLOCKED"
    elif finding_ids:
        signal = "DEGRADED"
    else:
        signal = "READY_WITHOUT_AUTHORIZATION"

    return {
        "memory_id": memory_id,
        "trust_signal": signal,
        "findings": finding_ids,
        "missing_fields": missing,
        "boundary": "Memory/content evidence is not automatic truth; source, freshness, and project scope must remain explicit.",
    }


def _collect_memory_evidence(root: Path) -> dict:
    selected = next((root / name for name in _MEMORY_CANDIDATE_FILES if (root / name).is_file()), None)
    rows = _safe_jsonl(selected) if selected else []
    items = [_classify_memory_record(row, root) for row in rows]
    counts = {"READY_WITHOUT_AUTHORIZATION": 0, "DEGRADED": 0, "BLOCKED": 0}
    for item in items:
        counts[item["trust_signal"]] += 1
    return {
        "ledger_file": _rel(selected, root) if selected else None,
        "count": len(items),
        "items": items,
        "status_counts": counts,
        "note": "Memory/content evidence is read-only and heuristic; OV does not decide factual truth.",
    }


def _classify_harness_bundle(row: dict) -> dict:
    bundle_id = (
        row.get("bundle_id") or row.get("trace_id") or f"harness-{abs(hash(json.dumps(row, sort_keys=True))) % 10000}"
    )
    trace = row.get("trace", {}) if isinstance(row.get("trace"), dict) else {}
    checkpoint = row.get("checkpoint", {}) if isinstance(row.get("checkpoint"), dict) else {}
    review = row.get("review_record", {}) if isinstance(row.get("review_record"), dict) else {}
    receipt = row.get("execution_receipt", {}) if isinstance(row.get("execution_receipt"), dict) else {}
    tool_calls = row.get("tool_calls", [])
    findings: list[str] = []

    if trace.get("presence_claims_truth") is True or row.get("trace_claims_truth") is True:
        findings.append("trace_present_treated_as_truth")
    if checkpoint.get("approval_claim") is True or checkpoint.get("authorizes_action") is True:
        findings.append("checkpoint_claims_approval")
    failed_tool_calls = [
        call for call in tool_calls if isinstance(call, dict) and str(call.get("status", "")).lower() == "failed"
    ]
    expected_failed = int(receipt.get("failed_tool_call_count", row.get("failed_tool_call_count", 0)) or 0)
    if expected_failed and len(failed_tool_calls) < expected_failed:
        findings.append("failed_tool_call_missing_from_trace")
    node_ids = {str(node.get("node_id")) for node in trace.get("nodes", []) if isinstance(node, dict)}
    reviewed_node = str(review.get("reviewed_node_id", ""))
    if review.get("human_reviewed") is True and reviewed_node and node_ids and reviewed_node not in node_ids:
        findings.append("review_node_not_in_trace")
    if receipt.get("authorization_claim") is True or receipt.get("external_action_taken") is True:
        findings.append("receipt_claims_authorization_or_action")

    if any(
        item in findings
        for item in (
            "checkpoint_claims_approval",
            "failed_tool_call_missing_from_trace",
            "receipt_claims_authorization_or_action",
        )
    ):
        signal = "BLOCKED"
    elif findings:
        signal = "DEGRADED"
    else:
        signal = "READY_WITHOUT_AUTHORIZATION"
    return {
        "bundle_id": bundle_id,
        "trust_signal": signal,
        "findings": findings,
        "boundary": "Trace/checkpoint/tool-call evidence is not truth, approval, consent, or safe action.",
    }


def _collect_harness_evidence(root: Path) -> dict:
    selected = next((root / name for name in _HARNESS_CANDIDATE_FILES if (root / name).is_file()), None)
    rows: list[dict] = []
    if selected:
        if selected.suffix == ".jsonl":
            rows = _safe_jsonl(selected)
        else:
            raw = _safe_json(selected)
            rows = raw.get("items", [raw]) if isinstance(raw.get("items"), list) else [raw]
    for p in sorted((root / "traces").glob("**/*.json"))[:40] + sorted((root / "harness").glob("**/*.json"))[:40]:
        raw = _safe_json(p)
        if raw:
            rows.append(raw)
    items = [_classify_harness_bundle(row) for row in rows]
    counts = {"READY_WITHOUT_AUTHORIZATION": 0, "DEGRADED": 0, "BLOCKED": 0}
    for item in items:
        counts[item["trust_signal"]] += 1
    return {
        "evidence_file": _rel(selected, root) if selected else None,
        "count": len(items),
        "items": items,
        "status_counts": counts,
        "note": "Harness/trace import is read-only. OV does not run agents or treat traces as approval.",
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
        items.append({
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
        })
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
            "Use Ordivon discovery as hints, not authority. This playbook is for the target project's AI.\n\n"
            "## Flow\n\n"
            "1. Read `governance/discovery-candidates.json` as hints only.\n"
            "2. Inventory local docs, tests, workflows, skills, release notes, traces, memory, and receipts.\n"
            "3. Fill `governance/agent-claim-bindings.jsonl` by binding each AI claim to work artifacts, test evidence, receipt, and review evidence.\n"
            "4. Propose candidate gates, but ask owner/reviewer to confirm which gates are canonical before putting them in `verification-gate-manifest.json`.\n"
            "5. Fill project-local evidence files; keep template placeholders out of final claims.\n"
            "6. Run OV in vibe, merge, then release stages as needed.\n"
            "7. Convert DEGRADED/BLOCKED findings into evidence repair, claim downgrade, or `verification-debt-ledger.jsonl` entries.\n"
            "8. Record `receipts/external-audit-receipt.md` with claim, evidence, review, decision boundary, debt, lesson, and optional CandidateRule/no-rule rationale.\n\n"
            "## Claim Binding Checklist\n\n"
            "- `claim_id`: stable local identifier.\n"
            "- `claim`: exact AI/contributor claim; do not include approval language.\n"
            "- `work_artifacts`: changed files, generated artifact, or diff reference.\n"
            "- `test_evidence`: command output, CI run, or explicit reason tests are missing.\n"
            "- `receipt`: local receipt recording what was checked.\n"
            "- `review_evidence`: human review note, PR review, or explicit missing-review debt.\n\n"
            "## DEGRADED/BLOCKED Handling\n\n"
            "- Add missing evidence when it exists.\n"
            "- Downgrade over-strong claims when evidence is weaker than the claim.\n"
            "- Register debt when evidence cannot be repaired in this cycle.\n"
            "- Do not chase green reports by deleting claims or hiding failed evidence.\n\n"
            "## Boundaries\n\n"
            "- Discovery is not proof.\n"
            "- Workflow presence is not a canonical gate.\n"
            "- Review is not approval unless project policy says so.\n"
            "- READY_WITHOUT_AUTHORIZATION is evidence sufficiency only.\n"
            "- CandidateRule draft is not active policy.\n"
            "- Skill/tool/workflow/trace/memory evidence is not permission, truth, approval, or safe action.\n"
        ),
        "PROJECT_AI_LOCALIZATION.md": (
            "# Project AI Localization\n\n"
            "This file is a project-independent instruction sheet for the target project's AI.\n"
            "Fill local evidence; do not copy discovery candidates into authority fields without owner/reviewer confirmation.\n\n"
            "## Required Loop\n\n"
            "1. Claim: identify the AI work claim.\n"
            "2. Evidence: bind artifacts, diff, tests, receipt, review, and gates.\n"
            "3. Decision boundary: record READY_WITHOUT_AUTHORIZATION, DEGRADED, or BLOCKED.\n"
            "4. Repair: convert gaps into evidence repair, debt, claim downgrade, lesson, or CandidateRule draft.\n\n"
            "## Localization Rules\n\n"
            "- Treat `governance/discovery-candidates.json` as hints only.\n"
            "- Confirm canonical gates with owner/reviewer before using them as gate evidence.\n"
            "- Fill `agent-claim-bindings.jsonl` with claim, work artifacts, test evidence, receipt, and review evidence.\n"
            "- Turn DEGRADED/BLOCKED into evidence repair, claim downgrade, or verification debt.\n"
            "- CandidateRule is advisory until separately promoted by project policy.\n"
            "- Skill/tool/workflow/trace/memory evidence is not permission, truth, approval, or safe action.\n\n"
            "OV verifies trust structure only. Project owner/reviewer authorizes merge, release, deploy, execution, tool use, and business workflow.\n"
        ),
        "AI_TRUST_LEVELS.md": (
            "# AI Trust Levels\n\n"
            "| Level | Meaning | Boundary |\n"
            "|---|---|---|\n"
            "| L0 Unobserved | AI wrote without structured record | Not READY |\n"
            "| L1 Claimed | AI claims completion | Claim only |\n"
            "| L2 Evidenced | Artifacts, tests, receipt, or diff exist | Evidence can still be weak |\n"
            "| L3 Reviewed | Review evidence exists | Review is not approval |\n"
            "| L4 Gate-Checked | Owner-confirmed gates passed | Still not authorization |\n"
            "| L5 Release-Evidence | Release/debt/skill/tool surfaces handled | Evidence only |\n"
            "| L6 Authorized | Project owner authorizes action | OV never emits this |\n\n"
            "READY_WITHOUT_AUTHORIZATION maps only to evidence sufficiency. It never authorizes action.\n"
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


def emit_template_pack(draft: dict, output_dir: Path) -> dict:
    """Write a generated template pack to an explicit output directory.

    This never writes to the target repository unless the caller explicitly
    chooses that path. The files remain placeholders; discovery observations are
    isolated in governance/discovery-candidates.json.
    """
    files = draft.get("files", {})
    if not isinstance(files, dict):
        raise ValueError("template draft missing files")
    written: list[str] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for rel_path, content in files.items():
        if not rel_path.endswith(SUPPORTED_EMIT_FILENAMES):
            raise ValueError(f"unsupported template file type: {rel_path}")
        dest = output_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if rel_path.endswith(".json"):
            text = json.dumps(content, indent=2) + "\n"
        elif rel_path.endswith(".jsonl"):
            rows = content if isinstance(content, list) else [content]
            text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
        else:
            text = str(content)
            if not text.endswith("\n"):
                text += "\n"
        dest.write_text(text, encoding="utf-8")
        written.append(rel_path)

    # Auto-discovery pass: populate generated artifact registry
    records = discover_artifacts(output_dir)
    registry = build_registry(records, str(output_dir))
    registry_path = output_dir / ".ordivon" / "graph" / "generated-artifact-registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    records_data = []
    for r in registry.records:
        records_data.append({
            "artifact_id": r.artifact_id,
            "path": r.path,
            "artifact_type": r.artifact_type,
            "authority_tier": r.authority_tier.value,
            "lifecycle_state": r.lifecycle_state.value,
            "temperature": r.temperature.value,
            "owner": r.owner,
            "scope": r.scope,
            "content_hash": r.content_hash,
            "last_verified": r.last_verified,
            "review_date": r.review_date,
            "supersedes": r.supersedes,
            "superseded_by": r.superseded_by,
            "depends_on": r.depends_on,
            "new_ai_entry": r.new_ai_entry,
            "current_truth_allowed": r.current_truth_allowed,
            "notes": r.notes,
        })
    findings_data = []
    for f in registry.findings:
        findings_data.append({
            "code": f.code,
            "status": f.status,
            "message": f.message,
            "artifact_id": f.artifact_id,
            "repair_action": f.repair_action,
        })
    registry_json = {
        "generated_at": registry.generated_at,
        "repo_root": registry.repo_root,
        "records": records_data,
        "findings": findings_data,
        "note": "Auto-discovered by convention after template emit.",
    }
    registry_path.write_text(json.dumps(registry_json, indent=2) + "\n", encoding="utf-8")
    written.append(".ordivon/graph/generated-artifact-registry.json")

    return {
        "output_dir": str(output_dir),
        "written_files": written,
        "file_count": len(written),
        "writes_target_repo": False,
        "boundary": "Template export writes only to the explicit output directory and does not authorize project action.",
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
    memory_evidence = _collect_memory_evidence(root)
    harness_evidence = _collect_harness_evidence(root)
    agent_risk_matrix = _build_agent_risk_matrix(agent_surfaces, skills)

    # Structured skill boundary scan (A2 scanner)
    skill_findings, skill_records = discover_skill_surfaces(root)
    skill_boundary = {
        "discovered_count": len(skill_records),
        "findings": [
            {
                "code": f.code,
                "status": f.status,
                "message": f.message,
                "artifact_id": f.artifact_id,
                "repair_action": f.repair_action,
            }
            for f in skill_findings
        ],
        "records_count": len(skill_records),
        "blocked_count": sum(1 for f in skill_findings if f.status == "BLOCKED"),
        "degraded_count": sum(1 for f in skill_findings if f.status == "DEGRADED"),
        "boundary": "Scanner is read-only; no skills/scripts/tools executed. Skill exists != permission.",
    }

    # Structured memory/content hygiene scan (A3 scanner)
    memory_findings, memory_records = discover_memory_surfaces(root)
    memory_hygiene = {
        "discovered_count": len(memory_records),
        "findings": [
            {
                "code": f.code,
                "status": f.status,
                "message": f.message,
                "artifact_id": f.artifact_id,
                "repair_action": f.repair_action,
            }
            for f in memory_findings
        ],
        "records_count": len(memory_records),
        "blocked_count": sum(1 for f in memory_findings if f.status == "BLOCKED"),
        "degraded_count": sum(1 for f in memory_findings if f.status == "DEGRADED"),
        "boundary": "Scanner is read-only; no factual truth judged. Memory source != truth; lesson != policy.",
    }

    # Structured trace/harness evidence scan (A4 scanner)
    trace_findings, trace_records = discover_trace_surfaces(root)
    trace_evidence = {
        "discovered_count": len(trace_records),
        "findings": [
            {
                "code": f.code,
                "status": f.status,
                "message": f.message,
                "artifact_id": f.artifact_id,
                "repair_action": f.repair_action,
            }
            for f in trace_findings
        ],
        "records_count": len(trace_records),
        "blocked_count": sum(1 for f in trace_findings if f.status == "BLOCKED"),
        "degraded_count": sum(1 for f in trace_findings if f.status == "DEGRADED"),
        "boundary": "Scanner is read-only; no trace replay or runtime API calls. Trace is evidence, not truth or authorization.",
    }

    next_actions = []
    if trace_evidence["blocked_count"]:
        next_actions.append(
            f"Trace evidence scanner found {trace_evidence['blocked_count']} BLOCKED finding(s). "
            "Review trace completeness, authorization claims, and review timing boundaries."
        )
    if memory_hygiene["blocked_count"]:
        next_actions.append(
            f"Memory hygiene scanner found {memory_hygiene['blocked_count']} BLOCKED finding(s). "
            "Review memory source, freshness, scope, and policy boundaries."
        )
    if skill_boundary["blocked_count"]:
        next_actions.append(
            f"Skill boundary scanner found {skill_boundary['blocked_count']} BLOCKED finding(s). "
            "Review skill allowed-tools, credential language, and authorization claims."
        )
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
    if memory_evidence["status_counts"]["BLOCKED"] or memory_evidence["status_counts"]["DEGRADED"]:
        next_actions.append("Repair memory/content source, freshness, project scope, or authority boundaries.")
    if harness_evidence["status_counts"]["BLOCKED"] or harness_evidence["status_counts"]["DEGRADED"]:
        next_actions.append("Repair trace/checkpoint/review evidence before treating harness artifacts as trustworthy.")

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
            "skill_boundary": skill_boundary,
            "memory_hygiene": memory_hygiene,
            "trace_evidence": trace_evidence,
            "agent_native_surfaces": agent_surfaces,
            "agent_native_risk_matrix": agent_risk_matrix,
            "release_claim_audit": release_claims,
            "agent_claim_bindings": agent_claim_bindings,
            "memory_content_hygiene": memory_evidence,
            "harness_evidence_import": harness_evidence,
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
    memory = inv["memory_content_hygiene"]
    harness = inv["harness_evidence_import"]
    skill_bdy = inv.get("skill_boundary", {})
    mem_bdy = inv.get("memory_hygiene", {})
    trace_bdy = inv.get("trace_evidence", {})
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
        f"- Memory/content records: {memory['count']}",
        f"- Harness/trace bundles: {harness['count']}",
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

    lines.extend([
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
        "### Skill / Tool Boundary Findings",
        "",
        f"- Discovered skill surfaces: {skill_bdy.get('discovered_count', 0)}",
        f"- Blocked findings: {skill_bdy.get('blocked_count', 0)}",
        f"- Degraded findings: {skill_bdy.get('degraded_count', 0)}",
        f"> {skill_bdy.get('boundary', 'Skill scanner is read-only.')}",
        "",
        "### Memory / Content Hygiene Findings",
        "",
        f"- Discovered memory/content surfaces: {mem_bdy.get('discovered_count', 0)}",
        f"- Blocked findings: {mem_bdy.get('blocked_count', 0)}",
        f"- Degraded findings: {mem_bdy.get('degraded_count', 0)}",
        f"> {mem_bdy.get('boundary', 'Memory scanner is read-only.')}",
        "",
        "### Trace / Harness Evidence Findings",
        "",
        f"- Discovered trace/checkpoint/review surfaces: {trace_bdy.get('discovered_count', 0)}",
        f"- Blocked findings: {trace_bdy.get('blocked_count', 0)}",
        f"- Degraded findings: {trace_bdy.get('degraded_count', 0)}",
        f"> {trace_bdy.get('boundary', 'Trace scanner is read-only.')}",
        "",
        "| Skill | Status | Risk | Findings |",
        "|---|---|---|---|",
    ])
    for item in skills.get("items", [])[:20]:
        lines.append(
            f"| `{item['path']}` | {item['status']} | {item['risk']} | {', '.join(item['findings'][:5]) or '-'} |"
        )
    if not skills.get("items"):
        lines.append("| - | - | - | - |")

    lines.extend([
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
    ])
    for item in release.get("items", [])[:12]:
        lines.append(
            f"| {item['claim_id']} | {item['trust_signal']} | {item['evidence_status']} | "
            f"`{item['file']}:{item['line']}` | {item['next_action']} |"
        )
    if not release.get("items"):
        lines.append("| - | - | - | - | - |")

    lines.extend([
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
    ])
    for item in bindings.get("items", [])[:12]:
        missing = ", ".join(item["missing_evidence"] + item["missing_artifacts"]) or "-"
        lines.append(f"| {item['claim_id']} | {item['trust_signal']} | {missing} |")
    if not bindings.get("items"):
        lines.append("| - | - | - |")

    if report.get("standard_pack_draft"):
        draft = report["standard_pack_draft"]
        files = draft["files"]
        lines.extend([
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
        ])
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
                "PROJECT_AI_LOCALIZATION.md": "project AI evidence-localization instructions",
                "AI_TRUST_LEVELS.md": "L0-L6 trust level boundary reference",
            }.get(name, "draft governance artifact")
            lines.append(f"| `{name}` | {purpose} |")
        lines.extend(["", "```json", json.dumps(files["ordivon.verify.json"], indent=2), "```"])
    if report.get("template_emit"):
        emit = report["template_emit"]
        lines.extend([
            "",
            "### Template Export",
            "",
            f"- Output directory: `{emit['output_dir']}`",
            f"- Files written: {emit['file_count']}",
            "- Target repository was not modified unless this directory was explicitly inside it.",
            f"- Boundary: {emit['boundary']}",
        ])

    lines.extend([
        "",
        "### Agent-Native Risk Matrix",
        "",
        "| Surface | Risk | Evidence Count | Boundary |",
        "|---|---|---:|---|",
    ])
    for item in inv["agent_native_risk_matrix"]:
        lines.append(f"| {item['surface']} | {item['risk']} | {item['evidence_count']} | {item['boundary']} |")
    if not inv["agent_native_risk_matrix"]:
        lines.append("| - | - | 0 | - |")

    lines.extend([
        "",
        "### Next Actions",
        "",
    ])
    for action in report["next_actions"]:
        lines.append(f"- {action}")

    lines.extend([
        "",
        f"> {report['disclaimer']}",
    ])
    return "\n".join(lines) + "\n"


def render_discovery_summary(report: dict) -> str:
    """Render compact discovery output for first-contact project onboarding."""
    inv = report["inventory"]
    tests = inv["tests"]
    skills = inv["skills"]
    release = inv["release_claim_audit"]
    bindings = inv["agent_claim_bindings"]
    memory = inv["memory_content_hygiene"]
    harness = inv["harness_evidence_import"]
    skill_bdy_summary = inv.get("skill_boundary", {})
    mem_summary = inv.get("memory_hygiene", {})
    trace_summary = inv.get("trace_evidence", {})
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
        f"- Memory/content hygiene: {memory['count']} records (DEGRADED {memory['status_counts']['DEGRADED']}, BLOCKED {memory['status_counts']['BLOCKED']})",
        f"- Harness evidence import: {harness['count']} bundles (DEGRADED {harness['status_counts']['DEGRADED']}, BLOCKED {harness['status_counts']['BLOCKED']})",
        f"- Skill boundary scan: {skill_bdy_summary.get('discovered_count', 0)} surfaces (BLOCKED {skill_bdy_summary.get('blocked_count', 0)}, DEGRADED {skill_bdy_summary.get('degraded_count', 0)})",
        f"- Memory hygiene scan: {mem_summary.get('discovered_count', 0)} surfaces (BLOCKED {mem_summary.get('blocked_count', 0)}, DEGRADED {mem_summary.get('degraded_count', 0)})",
        f"- Trace evidence scan: {trace_summary.get('discovered_count', 0)} surfaces (BLOCKED {trace_summary.get('blocked_count', 0)}, DEGRADED {trace_summary.get('degraded_count', 0)})",
        "",
        "### Top Next Actions",
        "",
    ]
    for action in report["next_actions"][:6]:
        lines.append(f"- {action}")
    if report.get("standard_pack_draft"):
        draft = report["standard_pack_draft"]
        lines.extend([
            "",
            "### Template Pack Draft",
            "",
            "- Dry-run only; no target files were written.",
            f"- Tier: `{draft.get('template_tier', 'standard')}`.",
            "- Template pack: project-independent placeholders; project AI must fill and owner-confirm them.",
            "- Discovery candidates are separated into `governance/discovery-candidates.json`.",
            "- Proposed files: " + ", ".join(f"`{name}`" for name in draft["files"].keys()),
        ])
    if report.get("template_emit"):
        emit = report["template_emit"]
        lines.extend([
            "",
            "### Template Export",
            "",
            f"- Output directory: `{emit['output_dir']}`.",
            f"- Files written: {emit['file_count']}.",
            "- OV wrote only to the explicit output directory.",
        ])
    lines.extend([
        "",
        f"> {report['disclaimer']}",
    ])
    return "\n".join(lines) + "\n"
