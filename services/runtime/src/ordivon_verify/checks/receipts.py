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
_CLEAN_TREE_PATTERN = re.compile(r"clean working tree", re.IGNORECASE)
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
    return "Receipt language contradicts evidence."


def _next_action(reason: str) -> str:
    for key, advice in _FAILURE_ADVICE.items():
        if key in reason:
            return advice
    return "Review the receipt and correct contradictory claims."


def _safe_boundary_line(line: str) -> bool:
    return bool(_SAFE_BOUNDARY_PATTERN.search(line))


def scan_receipt_files(receipt_paths: list[str], root: Path) -> tuple[list[dict], int]:
    """Scan receipt files for contradictions. Returns (failures, scanned_count)."""
    failures: list[dict] = []
    scanned = 0
    for rp in receipt_paths:
        scan_dir = root / rp
        if not scan_dir.is_dir():
            continue
        for md_file in sorted(scan_dir.rglob("*.md")):
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
    return failures, scanned
