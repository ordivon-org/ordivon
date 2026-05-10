"""Ordivon Verify — receipt contradiction scanner."""

from __future__ import annotations

import re
from pathlib import Path

_SKIP_CONTEXT_WORDS = [
    "not run",
    "not separately executed",
    "skipped",
    "omitted",
    "will verify after commit",
    "pending verification",
    "not yet run",
    "addendum required",
    "pending",
]

_SEALED_PATTERN = re.compile(r"(?:Status:\s*\*?\*?SEALED|FULLY SEALED)", re.IGNORECASE)
_SKIP_NONE_PATTERN = re.compile(r"Skipped Verification:\s*None", re.IGNORECASE)
_CLEAN_TREE_PATTERN = re.compile(
    r"\b(?:clean working tree|working tree is clean)\b",
    re.IGNORECASE,
)
_AUTHORIZATION_LAUNDERING_PATTERN = re.compile(
    r"\b(?:"
    r"READY\s+(?:authorizes|approves|permits|allows)"
    r"|approved\s+(?:for|to)\s+(?:merge|deploy|deployment|release|execute|execution)"
    r"|authorized\s+(?:for|to)\s+(?:merge|deploy|deployment|release|execute|execution)"
    r"|safe\s+to\s+(?:merge|deploy|release|execute)"
    r")\b",
    re.IGNORECASE,
)
_CANDIDATE_RULE_POLICY_PATTERN = re.compile(
    r"\bcandidaterule\b.*\b(?:active|binding|enforced|promoted|converted|policy)\b.*\bpolicy\b"
    r"|\bpolicy\b.*\b(?:from|via)\b.*\bcandidaterule\b",
    re.IGNORECASE,
)
_DEGRADED_AS_PASS_PATTERN = re.compile(
    r"\bdegraded\b.*\b(?:green|pass(?:ed)?|approved|ready)\b"
    r"|\b(?:green|pass(?:ed)?|approved|ready)\b.*\bdegraded\b",
    re.IGNORECASE,
)
_EXTERNAL_BENCHMARK_OVERCLAIM_PATTERN = re.compile(
    r"\b(?:certified|certification|compliant|compliance|production[-\s]?ready|SLSA\s+level\s+\d+)\b",
    re.IGNORECASE,
)
_LOCAL_TEST_CLAIM_PATTERN = re.compile(
    r"\b(?:tests?|test suite|verification)\s+(?:passed|green|succeeded)\s+locally\b",
    re.IGNORECASE,
)
_COMMAND_EVIDENCE_PATTERN = re.compile(
    r"`[^`]*(?:pytest|ruff|uv\s+run|python\s+-m|npm|pnpm|yarn|make)[^`]*`"
    r"|\b(?:command|commands|pytest|ruff|uv\s+run|python\s+-m|npm|pnpm|yarn|make)\b",
    re.IGNORECASE,
)

_SAFE_BOUNDARY_PATTERN = re.compile(
    r"\b(?:not|non-binding|advisory|no-go|without authorization|does not authorize|is not authorization)\b",
    re.IGNORECASE,
)

_FAILURE_ADVICE = {
    "SEALED": "Unverified work was called 'sealed'. Fix the receipt to reflect actual verification state, or complete the missing verification.",
    "Skipped: None": "Receipt claims no verification was skipped, but evidence shows gate(s) were not run. Correct the receipt or run the missing checks.",
    "clean working tree": "Receipt claims 'clean working tree' without acknowledging untracked residue. Either remove residue or qualify as 'Tracked working tree clean'.",
    "authorization": "READY/review evidence must not be written as merge, deploy, execution, release, or external-action authorization.",
    "CandidateRule": "CandidateRule is advisory evidence, not active policy. Correct the receipt or route through the explicit policy process.",
    "test evidence": "A local test success claim must name the command or reproducible evidence that supports it.",
}


def _has_skip_context_excluding_match(lines: list[str], match_line_idx: int) -> bool:
    ctx_start = max(0, match_line_idx - 5)
    ctx_end = min(len(lines), match_line_idx + 5)
    lines_before = lines[ctx_start:match_line_idx]
    lines_after = lines[match_line_idx + 1 : ctx_end]
    context = "\n".join(lines_before + lines_after)
    lower = context.lower()
    return any(w in lower for w in _SKIP_CONTEXT_WORDS)


def _classify_failure(reason: str) -> str:
    if "SEALED" in reason:
        return "receipt_contradiction"
    if "Skipped: None" in reason:
        return "skipped_verification_claim"
    if "clean working tree" in reason:
        return "clean_tree_overclaim"
    if "authorization" in reason:
        return "authorization_laundering"
    if "CandidateRule" in reason:
        return "candidate_rule_policy_confusion"
    if "DEGRADED" in reason:
        return "degraded_as_pass"
    if "external benchmark" in reason:
        return "external_benchmark_overclaim"
    if "test evidence" in reason:
        return "missing_test_evidence"
    return "receipt_contradiction"


def _why_it_matters(reason: str) -> str:
    if "SEALED" in reason:
        return "Unverified work must not be called sealed."
    if "Skipped: None" in reason:
        return "Skipped verification must be registered, not claimed as 'None'."
    if "clean working tree" in reason:
        return "Untracked residue contradicts 'clean working tree' claim."
    if "authorization" in reason:
        return "Verification evidence must not be laundered into action authorization."
    if "CandidateRule" in reason:
        return "CandidateRule must not be treated as binding or active policy."
    if "DEGRADED" in reason:
        return "DEGRADED is missing/weak evidence, not a pass or approval signal."
    if "external benchmark" in reason:
        return (
            "External benchmark references must not become compliance, certification, production, or SLSA-level claims."
        )
    if "test evidence" in reason:
        return "Test success claims must be backed by reproducible command evidence."
    return "Receipt language contradicts evidence."


def _next_action(reason: str) -> str:
    for key, advice in _FAILURE_ADVICE.items():
        if key in reason:
            return advice
    return "Review the receipt and correct contradictory claims."


def _safe_boundary_line(line: str) -> bool:
    return bool(_SAFE_BOUNDARY_PATTERN.search(line))


def _has_command_evidence_nearby(lines: list[str], match_line_idx: int) -> bool:
    ctx_start = max(0, match_line_idx - 4)
    ctx_end = min(len(lines), match_line_idx + 5)
    context_lines = [
        line
        for line in lines[ctx_start:ctx_end]
        if not re.search(
            r"\b(?:no|not|without|does\s+not|did\s+not|missing)\b.{0,40}\b(?:command|evidence)\b",
            line,
            re.IGNORECASE,
        )
    ]
    context = "\n".join(context_lines)
    return bool(_COMMAND_EVIDENCE_PATTERN.search(context))


def _iter_receipt_markdown_files(receipt_path: str, root: Path) -> list[Path]:
    """Return in-root Markdown receipt files for a configured file or directory."""
    candidate = (root / receipt_path).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        return []
    if candidate.is_file():
        return [candidate] if candidate.suffix.lower() == ".md" else []
    if candidate.is_dir():
        return sorted(p for p in candidate.rglob("*.md") if p.is_file())
    return []


def scan_receipt_files(receipt_paths: list[str], root: Path) -> tuple[list[dict], int]:
    """Scan receipt files/directories for contradictions. Returns (failures, scanned_count)."""
    failures: list[dict] = []
    scanned = 0
    for rp in receipt_paths:
        for md_file in _iter_receipt_markdown_files(rp, root):
            scanned += 1
            try:
                content = md_file.read_text()
            except Exception:
                continue
            lines = content.split("\n")
            rel = str(md_file.relative_to(root))
            for i, line in enumerate(lines, 1):
                idx = i - 1
                if _SEALED_PATTERN.search(line) and _has_skip_context_excluding_match(lines, idx):
                    reason = "Status SEALED but nearby text suggests incomplete verification"
                    failures.append({
                        "id": _classify_failure(reason),
                        "file": rel,
                        "line": i,
                        "reason": reason,
                        "why_it_matters": _why_it_matters(reason),
                        "next_action": _next_action(reason),
                    })
                elif _SKIP_NONE_PATTERN.search(line) and _has_skip_context_excluding_match(lines, idx):
                    reason = "Claims 'Skipped: None' but nearby text suggests gate was not run"
                    failures.append({
                        "id": _classify_failure(reason),
                        "file": rel,
                        "line": i,
                        "reason": reason,
                        "why_it_matters": _why_it_matters(reason),
                        "next_action": _next_action(reason),
                    })
                elif _CLEAN_TREE_PATTERN.search(line):
                    ctx_start, ctx_end = max(0, idx - 5), min(len(lines), idx + 5)
                    ctx_text = "\n".join(lines[ctx_start:ctx_end])
                    if not re.compile(r"tracked working tree clean|tracked clean", re.IGNORECASE).search(ctx_text):
                        reason = "Claims 'clean working tree' without acknowledging untracked residue"
                        failures.append({
                            "id": _classify_failure(reason),
                            "file": rel,
                            "line": i,
                            "reason": reason,
                            "why_it_matters": _why_it_matters(reason),
                            "next_action": _next_action(reason),
                        })
                elif _AUTHORIZATION_LAUNDERING_PATTERN.search(line) and not _safe_boundary_line(line):
                    reason = "Receipt language turns verification/review evidence into authorization"
                    failures.append({
                        "id": _classify_failure(reason),
                        "file": rel,
                        "line": i,
                        "reason": reason,
                        "why_it_matters": _why_it_matters(reason),
                        "next_action": _next_action(reason),
                    })
                elif _CANDIDATE_RULE_POLICY_PATTERN.search(line) and not _safe_boundary_line(line):
                    reason = "CandidateRule is described as active or binding policy"
                    failures.append({
                        "id": _classify_failure(reason),
                        "file": rel,
                        "line": i,
                        "reason": reason,
                        "why_it_matters": _why_it_matters(reason),
                        "next_action": _next_action(reason),
                    })
                elif _DEGRADED_AS_PASS_PATTERN.search(line) and not _safe_boundary_line(line):
                    reason = "DEGRADED is described as a pass or readiness signal"
                    failures.append({
                        "id": _classify_failure(reason),
                        "file": rel,
                        "line": i,
                        "reason": reason,
                        "why_it_matters": _why_it_matters(reason),
                        "next_action": _next_action(reason),
                    })
                elif _EXTERNAL_BENCHMARK_OVERCLAIM_PATTERN.search(line) and not _safe_boundary_line(line):
                    reason = "Receipt makes unsafe external benchmark or supply-chain overclaim"
                    failures.append({
                        "id": _classify_failure(reason),
                        "file": rel,
                        "line": i,
                        "reason": reason,
                        "why_it_matters": _why_it_matters(reason),
                        "next_action": _next_action(reason),
                    })
                elif _LOCAL_TEST_CLAIM_PATTERN.search(line) and not _has_command_evidence_nearby(lines, idx):
                    reason = "Receipt claims tests passed locally without reproducible test evidence"
                    failures.append({
                        "id": _classify_failure(reason),
                        "file": rel,
                        "line": i,
                        "reason": reason,
                        "why_it_matters": _why_it_matters(reason),
                        "next_action": _next_action(reason),
                    })
    return failures, scanned
