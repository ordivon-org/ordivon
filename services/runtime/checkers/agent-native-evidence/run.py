"""Agent-native evidence boundary checker.

Shadow-first. Read-only. No network, agent, tool, token, server, or external
action.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = ROOT / "docs" / "governance" / "agent-native-evidence-surfaces-2026.md"
REDTEAM_LEDGER = ROOT / "docs" / "governance" / "agent-native-evidence-redteam.jsonl"
SKILLS_DIR = ROOT / "skills"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "agent_native_evidence"
MEMORY_RECORD_REQUIRED_FIELDS = {
    "record_id",
    "project_scope",
    "source_receipt",
    "last_verified",
    "stale_after_days",
    "authority",
    "claim",
}
HARNESS_BUNDLE_REQUIRED_FIELDS = {
    "bundle_id",
    "trace",
    "checkpoint",
    "tool_calls",
    "review_record",
    "execution_receipt",
}
MCP_MANIFEST_REQUIRED_FIELDS = {
    "manifest_id",
    "server_name",
    "tools",
    "resources",
    "authorization",
    "token_handling",
    "audience",
}
ALLOWED_MEMORY_AUTHORITIES = {"source_of_truth", "supporting_evidence", "current_status", "candidate_rule", "policy"}
CURRENT_PROJECT_SCOPE = "Ordivon"

REQUIRED_DOC_PHRASES = [
    "Ordivon should verify",
    "their evidence boundaries without becoming the runtime",
    "Skill Safety Review",
    "Memory / Content Hygiene",
    "Harness Evidence Import",
    "MCP Boundary Review",
    "Agent evidence import is evidence hygiene only",
]

SAFE_CONTEXT = re.compile(
    r"\b(?:not|no|does\s+not|must\s+not|cannot|evidence\s+only|read-only|flagged|unsafe|boundary|risk|fixture|red-team)\b",
    re.IGNORECASE,
)

VIOLATION_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "skill_permission_laundering": [
        re.compile(
            r"\bskill\b.{0,120}\b(?:can|capability|able\s+to)\b.{0,120}\b(?:therefore|so|means)\b.{0,80}\b(?:may|permission|authorized|approved)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bskill\s+capability\b.{0,100}\b(?:permission|authorization|approval)\b", re.IGNORECASE),
    ],
    "skill_credential_seeking": [
        re.compile(
            r"\bskill\b.{0,160}\b(?:ask|asks|request|requests|collect|read|export|print|store)\b.{0,80}\b(?:api[_\s-]?key|token|secret|password|credential)\b",
            re.IGNORECASE,
        ),
    ],
    "memory_stale_current_truth": [
        re.compile(
            r"\b(?:stale|expired|old|unverified)\b.{0,120}\b(?:memory|note|content)\b.{0,120}\b(?:current\s+truth|source\s+of\s+truth|authoritative|current\s+authority)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:cross[-\s]?project|other\s+project)\b.{0,120}\b(?:memory|note|content)\b.{0,120}\b(?:current\s+truth|source\s+of\s+truth|authoritative)\b",
            re.IGNORECASE,
        ),
    ],
    "memory_signal_laundering": [
        re.compile(
            r"\b(?:DEGRADED|BLOCKED)\b.{0,120}\b(?:clean|pass|passed|ready|approved|current\s+fact|current\s+truth)\b",
            re.IGNORECASE,
        ),
    ],
    "harness_checkpoint_approval": [
        re.compile(
            r"\b(?:checkpoint|trace|execution\s+receipt|receipt)\b.{0,120}\b(?:approves|approved|approval|authorizes|authorized)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\btrace\s+presence\b.{0,100}\b(?:truth|approval|authorization)\b", re.IGNORECASE),
    ],
    "harness_failed_tool_omission": [
        re.compile(
            r"\bfailed\s+tool\s+call\b.{0,120}\b(?:omitted|removed|hidden|not\s+included|missing)\b",
            re.IGNORECASE,
        ),
    ],
    "mcp_token_passthrough": [
        re.compile(r"\btoken\s+passthrough\b", re.IGNORECASE),
        re.compile(
            r"\b(?:pass|forward|reuse|relay)\b.{0,80}\b(?:user\s+)?token\b.{0,80}\b(?:server|tool|resource)\b",
            re.IGNORECASE,
        ),
    ],
    "mcp_audience_resource_confusion": [
        re.compile(r"\baudience\b.{0,100}\bresource\b.{0,100}\b(?:same|interchangeable|equivalent)\b", re.IGNORECASE),
        re.compile(r"\bresource\b.{0,100}\baudience\b.{0,100}\b(?:same|interchangeable|equivalent)\b", re.IGNORECASE),
    ],
    "mcp_tool_availability_authorization": [
        re.compile(
            r"\btool\s+available\b.{0,120}\b(?:permission|authorization|authorized|approved|may\s+execute)\b",
            re.IGNORECASE,
        ),
    ],
}

SKILL_CREDENTIAL_PATTERN = re.compile(
    r"\b(?:ask|asks|request|requests|collect|read|export|print|store|paste|provide)\b.{0,100}\b(?:api[_\s-]?key|token|secret|password|credential)\b",
    re.IGNORECASE,
)
SKILL_DANGEROUS_ALLOWED_TOOLS = {
    "bash",
    "shell",
    "network",
    "web",
    "write",
    "edit",
    "filesystem",
    "mcp",
}
SKILL_PATH_REF_PATTERN = re.compile(r"\b(?:scripts|tools|resources|templates)/[A-Za-z0-9_./-]+")


@dataclass(frozen=True)
class CheckerResult:
    status: str
    exit_code: int
    findings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def _load_jsonl(path: Path) -> tuple[list[dict], list[str]]:
    entries: list[dict] = []
    errors: list[str] = []
    if not path.exists():
        return entries, [f"missing JSONL ledger: {path.relative_to(ROOT)}"]
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(ROOT)}:{lineno}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path.relative_to(ROOT)}:{lineno}: entry must be object")
            continue
        entries.append(value)
    return entries, errors


def _safe_context(text: str, start: int) -> bool:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", start)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    if line.lstrip().startswith("|"):
        return True
    return bool(SAFE_CONTEXT.search(line))


def detect_agent_evidence_violations(text: str) -> list[str]:
    violations: list[str] = []
    for violation_id, patterns in VIOLATION_PATTERNS.items():
        for pattern in patterns:
            for match in pattern.finditer(text):
                if _safe_context(text, match.start()):
                    continue
                violations.append(violation_id)
                break
            if violation_id in violations:
                break
    return sorted(set(violations))


def validate_plan_document(path: Path = PLAN_DOC) -> list[str]:
    if not path.exists():
        return [f"missing plan document: {path.relative_to(ROOT)}"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for phrase in REQUIRED_DOC_PHRASES:
        if phrase not in text:
            errors.append(f"{path.relative_to(ROOT)}: missing phrase '{phrase}'")
    unsafe = detect_agent_evidence_violations(text)
    if unsafe:
        errors.append(f"{path.relative_to(ROOT)}: unsafe agent-native evidence wording {unsafe}")
    return errors


def validate_redteam_ledger(path: Path = REDTEAM_LEDGER) -> list[str]:
    entries, load_errors = _load_jsonl(path)
    errors = list(load_errors)
    seen: set[str] = set()
    required_surfaces = {"skill", "memory", "harness", "mcp"}

    for entry in entries:
        case_id = str(entry.get("case_id", ""))
        surface = str(entry.get("surface", ""))
        expected = str(entry.get("expected_violation", ""))
        text = str(entry.get("text", ""))
        if not case_id:
            errors.append("redteam entry missing case_id")
        if case_id in seen:
            errors.append(f"{case_id}: duplicate case_id")
        seen.add(case_id)
        if surface not in required_surfaces:
            errors.append(f"{case_id}: unknown surface '{surface}'")
        if expected not in VIOLATION_PATTERNS:
            errors.append(f"{case_id}: unknown expected_violation '{expected}'")
            continue
        if not text.strip():
            errors.append(f"{case_id}: missing text")
            continue
        actual = detect_agent_evidence_violations(text)
        if expected not in actual:
            errors.append(f"{case_id}: expected {expected}, detected {actual}")

    covered_surfaces = {str(e.get("surface", "")) for e in entries}
    for missing in sorted(required_surfaces - covered_surfaces):
        errors.append(f"missing agent-native evidence surface coverage: {missing}")
    return errors


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        data[key.strip()] = value.strip().strip("'\"")
    return data, body


def _line_is_safe(line: str) -> bool:
    return bool(SAFE_CONTEXT.search(line))


def _split_allowed_tools(raw: str) -> set[str]:
    value = raw.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    parts = re.split(r"[,;\s]+", value)
    return {p.strip().strip("'\"").lower() for p in parts if p.strip()}


def _skill_name(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def validate_skill_file(path: Path) -> list[str]:
    name = _skill_name(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = _parse_frontmatter(text)
    errors: list[str] = []

    if not frontmatter:
        errors.append(f"{name}: missing YAML frontmatter")
    for field_name in ("name", "description"):
        if not frontmatter.get(field_name):
            errors.append(f"{name}: missing frontmatter field '{field_name}'")

    for lineno, line in enumerate(text.splitlines(), 1):
        if SKILL_CREDENTIAL_PATTERN.search(line) and not _line_is_safe(line):
            errors.append(f"{name}:{lineno}: skill requests or handles protected credential/token material")

    unsafe = detect_agent_evidence_violations(text)
    for violation in unsafe:
        if violation.startswith("skill_"):
            errors.append(f"{name}: unsafe skill wording {violation}")

    allowed_tools = _split_allowed_tools(frontmatter.get("allowed-tools", ""))
    dangerous = sorted(allowed_tools & SKILL_DANGEROUS_ALLOWED_TOOLS)
    if dangerous:
        lower_body = body.lower()
        has_non_authorization = bool(re.search(r"\b(?:does\s+not|not|no)\b.{0,40}\bauthori[sz]e", lower_body))
        if "read-only" not in lower_body or not has_non_authorization:
            errors.append(
                f"{name}: dangerous allowed-tools {dangerous} require read-only and non-authorization boundaries"
            )

    for ref in sorted(set(SKILL_PATH_REF_PATTERN.findall(text))):
        # Template/resource examples may be generic. Only enforce concrete repo-local
        # references without placeholder markers.
        if "<" in ref or ">" in ref:
            continue
        target = ROOT / ref
        if not target.exists():
            errors.append(f"{name}: referenced file does not exist: {ref}")

    return errors


def validate_skills(root: Path = SKILLS_DIR) -> list[str]:
    if not root.exists():
        return []
    errors: list[str] = []
    for path in sorted(root.rglob("SKILL.md")):
        errors.extend(validate_skill_file(path))
    return errors


def _load_json(path: Path) -> tuple[dict, list[str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path.relative_to(ROOT)}: invalid JSON: {exc}"]
    if not isinstance(value, dict):
        return {}, [f"{path.relative_to(ROOT)}: JSON root must be object"]
    return value, []


def _path_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def validate_memory_record(path: Path, reference_year: int = 2026) -> list[str]:
    name = _path_label(path)
    record, errors = _load_json(path)
    if errors:
        return errors

    missing = sorted(field for field in MEMORY_RECORD_REQUIRED_FIELDS if field not in record)
    for field_name in missing:
        errors.append(f"{name}: missing memory field '{field_name}'")

    source_receipt = str(record.get("source_receipt", "")).strip()
    if not source_receipt:
        errors.append(f"{name}: missing source_receipt")
    elif not (ROOT / source_receipt).exists():
        errors.append(f"{name}: source_receipt does not exist: {source_receipt}")

    project_scope = str(record.get("project_scope", "")).strip()
    if project_scope and project_scope != CURRENT_PROJECT_SCOPE:
        errors.append(f"{name}: cross-project memory scope '{project_scope}' cannot be imported silently")

    authority = str(record.get("authority", "")).strip()
    if authority and authority not in ALLOWED_MEMORY_AUTHORITIES:
        errors.append(f"{name}: invalid authority '{authority}'")

    try:
        stale_after_days = int(record.get("stale_after_days", 0))
    except (TypeError, ValueError):
        stale_after_days = 0
    if stale_after_days <= 0:
        errors.append(f"{name}: stale_after_days must be positive")

    last_verified = str(record.get("last_verified", ""))
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", last_verified):
        errors.append(f"{name}: last_verified must be YYYY-MM-DD")
    elif (
        last_verified[:4].isdigit()
        and int(last_verified[:4]) < reference_year
        and authority
        in {
            "source_of_truth",
            "current_status",
        }
    ):
        errors.append(f"{name}: stale memory cannot be cited as current authority")

    claim = str(record.get("claim", ""))
    claim_lower = claim.lower()
    evidence_status = str(record.get("evidence_status", "")).upper()
    if evidence_status in {"DEGRADED", "BLOCKED"} and re.search(
        r"\b(clean|passed|ready|approved|current truth)\b", claim_lower
    ):
        errors.append(f"{name}: {evidence_status} evidence is rewritten as clean/current fact")

    object_type = str(record.get("object_type", ""))
    if object_type == "CandidateRule" and authority == "policy":
        errors.append(f"{name}: CandidateRule cannot be imported as Policy")
    if "CandidateRule is Policy" in claim:
        errors.append(f"{name}: CandidateRule/Policy authority confusion")

    return errors


def validate_memory_records(root: Path) -> list[str]:
    if not root.exists():
        return []
    errors: list[str] = []
    for path in sorted(root.rglob("*.json")):
        errors.extend(validate_memory_record(path))
    return errors


def validate_harness_bundle(path: Path) -> list[str]:
    name = _path_label(path)
    bundle, errors = _load_json(path)
    if errors:
        return errors

    missing = sorted(field for field in HARNESS_BUNDLE_REQUIRED_FIELDS if field not in bundle)
    for field_name in missing:
        errors.append(f"{name}: missing harness field '{field_name}'")

    trace = bundle.get("trace") if isinstance(bundle.get("trace"), dict) else {}
    checkpoint = bundle.get("checkpoint") if isinstance(bundle.get("checkpoint"), dict) else {}
    tool_calls = bundle.get("tool_calls") if isinstance(bundle.get("tool_calls"), list) else []
    review = bundle.get("review_record") if isinstance(bundle.get("review_record"), dict) else {}
    receipt = bundle.get("execution_receipt") if isinstance(bundle.get("execution_receipt"), dict) else {}

    if "trace" in bundle and not isinstance(bundle.get("trace"), dict):
        errors.append(f"{name}: trace must be object")
    if "checkpoint" in bundle and not isinstance(bundle.get("checkpoint"), dict):
        errors.append(f"{name}: checkpoint must be object")
    if "tool_calls" in bundle and not isinstance(bundle.get("tool_calls"), list):
        errors.append(f"{name}: tool_calls must be array")
    if "review_record" in bundle and not isinstance(bundle.get("review_record"), dict):
        errors.append(f"{name}: review_record must be object")
    if "execution_receipt" in bundle and not isinstance(bundle.get("execution_receipt"), dict):
        errors.append(f"{name}: execution_receipt must be object")

    trace_nodes = trace.get("nodes", [])
    if not isinstance(trace_nodes, list):
        errors.append(f"{name}: trace.nodes must be array")
        trace_nodes = []
    node_ids = {str(node.get("node_id", "")) for node in trace_nodes if isinstance(node, dict)}

    if trace.get("presence_claims_truth") is True:
        errors.append(f"{name}: trace presence cannot be imported as truth")

    if checkpoint.get("approval_claim") is True or checkpoint.get("authorizes_action") is True:
        errors.append(f"{name}: checkpoint cannot claim approval or action authorization")

    reviewed_node = str(review.get("reviewed_node_id", ""))
    if review.get("human_reviewed") is not True:
        errors.append(f"{name}: human review must be explicit")
    if reviewed_node and reviewed_node not in node_ids:
        errors.append(f"{name}: human review references unknown trace node '{reviewed_node}'")

    failed_calls = [
        call for call in tool_calls if isinstance(call, dict) and str(call.get("status", "")).lower() == "failed"
    ]
    expected_failed = receipt.get("failed_tool_call_count", 0)
    try:
        expected_failed_int = int(expected_failed)
    except (TypeError, ValueError):
        expected_failed_int = 0
        errors.append(f"{name}: failed_tool_call_count must be integer")
    if expected_failed_int > 0 and not failed_calls:
        errors.append(f"{name}: execution receipt reports failed tool calls but trace omits failed tool call evidence")
    if len(failed_calls) < expected_failed_int:
        errors.append(f"{name}: failed tool call evidence count is lower than receipt count")

    if receipt.get("authorization_claim") is True:
        errors.append(f"{name}: execution receipt cannot claim authorization")
    status = str(receipt.get("status", "")).upper()
    if status == "READY" and receipt.get("external_action_taken") is True:
        errors.append(f"{name}: READY receipt cannot imply external action was authorized or taken")

    return errors


def validate_harness_bundles(root: Path) -> list[str]:
    if not root.exists():
        return []
    errors: list[str] = []
    for path in sorted(root.rglob("*.json")):
        errors.extend(validate_harness_bundle(path))
    return errors


def validate_mcp_manifest(path: Path) -> list[str]:
    name = _path_label(path)
    manifest, errors = _load_json(path)
    if errors:
        return errors

    missing = sorted(field for field in MCP_MANIFEST_REQUIRED_FIELDS if field not in manifest)
    for field_name in missing:
        errors.append(f"{name}: missing MCP manifest field '{field_name}'")

    tools = manifest.get("tools") if isinstance(manifest.get("tools"), list) else []
    resources = manifest.get("resources") if isinstance(manifest.get("resources"), list) else []
    auth = manifest.get("authorization") if isinstance(manifest.get("authorization"), dict) else {}
    token = manifest.get("token_handling") if isinstance(manifest.get("token_handling"), dict) else {}
    audience = manifest.get("audience") if isinstance(manifest.get("audience"), dict) else {}

    if "tools" in manifest and not isinstance(manifest.get("tools"), list):
        errors.append(f"{name}: tools must be array")
    if "resources" in manifest and not isinstance(manifest.get("resources"), list):
        errors.append(f"{name}: resources must be array")
    if "authorization" in manifest and not isinstance(manifest.get("authorization"), dict):
        errors.append(f"{name}: authorization must be object")
    if "token_handling" in manifest and not isinstance(manifest.get("token_handling"), dict):
        errors.append(f"{name}: token_handling must be object")
    if "audience" in manifest and not isinstance(manifest.get("audience"), dict):
        errors.append(f"{name}: audience must be object")

    if token.get("passthrough") is True:
        errors.append(f"{name}: token passthrough is not allowed in read-only import boundary")
    if token.get("reads_real_tokens") is True or token.get("refreshes_tokens") is True:
        errors.append(f"{name}: checker boundary cannot read or refresh real tokens")

    if auth.get("tool_availability_authorizes_action") is True:
        errors.append(f"{name}: tool availability cannot authorize action")
    if auth.get("optional") is True and auth.get("boundary_note"):
        note = str(auth.get("boundary_note", "")).lower()
        if "not authorization" not in note and "does not authorize" not in note:
            errors.append(f"{name}: optional authorization needs explicit non-authorization boundary")

    if audience.get("resource_equals_audience") is True:
        errors.append(f"{name}: resource and audience cannot be treated as equivalent")

    if tools:
        for idx, tool in enumerate(tools, 1):
            if not isinstance(tool, dict):
                errors.append(f"{name}: tools[{idx}] must be object")
                continue
            if tool.get("available") is True and tool.get("authorized") is True:
                errors.append(f"{name}: tools[{idx}] availability is conflated with authorization")
            if tool.get("external_side_effects") is True and tool.get("read_only") is not True:
                errors.append(f"{name}: tools[{idx}] external side effects require read_only=true for import boundary")

    if resources:
        for idx, resource in enumerate(resources, 1):
            if not isinstance(resource, dict):
                errors.append(f"{name}: resources[{idx}] must be object")
                continue
            if (
                resource.get("audience")
                and audience.get("expected")
                and resource.get("audience") != audience.get("expected")
            ):
                errors.append(f"{name}: resources[{idx}] audience does not match expected audience")

    risk_notes = " ".join(str(item) for item in manifest.get("risk_notes", []))
    risk_notes_lower = risk_notes.lower()
    if "confused deputy" not in risk_notes_lower and "confused-deputy" not in risk_notes_lower:
        errors.append(f"{name}: MCP boundary must name confused-deputy risk")

    text = json.dumps(manifest, sort_keys=True)
    for violation in detect_agent_evidence_violations(text):
        if violation.startswith("mcp_"):
            errors.append(f"{name}: unsafe MCP wording {violation}")

    return errors


def validate_mcp_manifests(root: Path) -> list[str]:
    if not root.exists():
        return []
    errors: list[str] = []
    for path in sorted(root.rglob("*.json")):
        errors.extend(validate_mcp_manifest(path))
    return errors


def validate_fixture_suite(root: Path = FIXTURES_DIR) -> list[str]:
    """Validate positive fixtures pass and negative fixtures keep failing."""
    if not root.exists():
        return [f"missing agent-native evidence fixture root: {root.relative_to(ROOT)}"]

    errors: list[str] = []
    validators = {
        "skills": (validate_skill_file, "SKILL.md"),
        "memory": (validate_memory_record, "*.json"),
        "harness": (validate_harness_bundle, "*.json"),
        "mcp": (validate_mcp_manifest, "*.json"),
    }

    for surface, (validator, pattern) in validators.items():
        surface_root = root / surface
        valid_root = surface_root / "valid"
        invalid_root = surface_root / "invalid"

        valid_files = sorted(valid_root.rglob(pattern)) if valid_root.exists() else []
        if not valid_files:
            errors.append(f"{surface}: missing positive fixtures")
        for path in valid_files:
            fixture_errors = validator(path)
            if fixture_errors:
                label = _path_label(path)
                errors.append(f"{label}: positive fixture failed: {'; '.join(fixture_errors)}")

        invalid_files = sorted(invalid_root.rglob(pattern)) if invalid_root.exists() else []
        if not invalid_files:
            errors.append(f"{surface}: missing red-team fixtures")
        for path in invalid_files:
            fixture_errors = validator(path)
            if not fixture_errors:
                errors.append(f"{_path_label(path)}: red-team fixture did not produce a finding")

    return errors


def fixture_suite_stats(root: Path = FIXTURES_DIR) -> dict[str, dict[str, int]]:
    stats: dict[str, dict[str, int]] = {}
    patterns = {
        "skills": "SKILL.md",
        "memory": "*.json",
        "harness": "*.json",
        "mcp": "*.json",
    }
    for surface, pattern in patterns.items():
        valid = list((root / surface / "valid").rglob(pattern)) if (root / surface / "valid").exists() else []
        invalid = list((root / surface / "invalid").rglob(pattern)) if (root / surface / "invalid").exists() else []
        stats[surface] = {"valid": len(valid), "redteam": len(invalid), "total": len(valid) + len(invalid)}
    return stats


def run() -> CheckerResult:
    findings: list[str] = []
    findings.extend(validate_plan_document())
    findings.extend(validate_redteam_ledger())
    findings.extend(validate_skills())
    findings.extend(validate_fixture_suite())
    entries, _ = _load_jsonl(REDTEAM_LEDGER)
    skill_files = list(SKILLS_DIR.rglob("SKILL.md")) if SKILLS_DIR.exists() else []
    stats = {
        "surfaces": sorted({str(e.get("surface", "")) for e in entries if e.get("surface")}),
        "redteam_cases": len(entries),
        "skill_files": len(skill_files),
        "fixture_suite": fixture_suite_stats(),
        "findings": len(findings),
    }
    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings, stats)


def main() -> int:
    result = run()
    if result.findings:
        print("Agent-native evidence boundary: FAIL")
        for finding in result.findings:
            print(f"  - {finding}")
    else:
        print("Agent-native evidence boundary: PASS")
        print(f"Surfaces: {', '.join(result.stats['surfaces'])}")
        print(f"Red-team cases: {result.stats['redteam_cases']}")
        print(f"Skill files: {result.stats['skill_files']}")
        for surface, counts in result.stats["fixture_suite"].items():
            print(f"{surface} fixtures: {counts['valid']} valid, {counts['redteam']} red-team")
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
