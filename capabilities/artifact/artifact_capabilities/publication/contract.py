from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class CarrierObservation:
    """Observed publication-carrier facts.

    Artifact owns observation and contract evaluation only. Scientific truth,
    venue policy authority, and Human perceptual judgement remain external.
    """

    pdf_sha256: str
    page_count: int
    text: str
    pages: tuple[str, ...]
    qpdf_pass: bool
    all_fonts_embedded: bool
    type3_fonts: int
    overfull_boxes: int | None
    undefined_citations: int | None
    undefined_references: int | None
    human_perceptual_signoff: bool = False

    def __post_init__(self) -> None:
        if self.page_count < 1:
            raise ValueError("page_count must be positive")
        if len(self.pages) != self.page_count:
            raise ValueError("pages length must equal page_count")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", self.pdf_sha256):
            raise ValueError("pdf_sha256 must be a bare 64-hex SHA-256 digest")
        if self.type3_fonts < 0:
            raise ValueError("type3_fonts must be non-negative")
        for name in (
            "overfull_boxes",
            "undefined_citations",
            "undefined_references",
        ):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative when observed")


def load_publication_contract(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("publication carrier contract must be an object")
    if value.get("schemaVersion") != 1:
        raise ValueError("publication carrier contract schemaVersion must be 1")
    if value.get("kind") != "publication-carrier-contract":
        raise ValueError("kind must be publication-carrier-contract")
    contract_id = value.get("id")
    if not isinstance(contract_id, str) or not contract_id:
        raise ValueError("contract id must be a non-empty string")
    authority = value.get("authority")
    if not isinstance(authority, list) or not authority:
        raise ValueError("contract must bind at least one external authority")
    for index, row in enumerate(authority):
        if not isinstance(row, dict):
            raise ValueError(f"authority[{index}] must be an object")
        if not isinstance(row.get("url"), str) or not row["url"].startswith(("https://", "http://")):
            raise ValueError(f"authority[{index}].url must be HTTP(S)")
        if not isinstance(row.get("observedAt"), str) or not row["observedAt"]:
            raise ValueError(f"authority[{index}].observedAt is required")
    return value


def _finding(
    finding_id: str,
    message: str,
    *,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": finding_id,
        "severity": "ERROR",
        "message": message,
    }
    if evidence:
        item["evidence"] = evidence
    return item


def _heading_locations(
    pages: tuple[str, ...],
    pattern: str,
) -> list[tuple[int, int, str]]:
    rx = re.compile(pattern, re.IGNORECASE)
    found: list[tuple[int, int, str]] = []
    for page_number, page in enumerate(pages, start=1):
        for line_number, line in enumerate(page.splitlines(), start=1):
            # acmart review mode projects source line numbers into the PDF text
            # layer. They are carrier annotations, not manuscript heading text.
            normalized = re.sub(r"^\s*\d+\s{2,}", "", line)
            if rx.search(normalized):
                found.append((page_number, line_number, normalized))
    return found


def _position_key(location: tuple[int, int, str]) -> tuple[int, int]:
    return location[0], location[1]


def evaluate_publication_contract(
    observation: CarrierObservation,
    contract: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate one observed carrier against an authority-bound declarative contract.

    This deliberately does not claim scientific correctness or perceptual quality.
    A machine PASS can remain PENDING_HUMAN.
    """

    if contract.get("schemaVersion") != 1 or contract.get("kind") != "publication-carrier-contract":
        raise ValueError("invalid publication carrier contract")

    findings: list[dict[str, Any]] = []

    mechanical = contract.get("mechanical", {})
    if mechanical.get("requireQpdfPass") and not observation.qpdf_pass:
        findings.append(_finding("qpdf", "qpdf structural check did not pass"))
    if mechanical.get("requireAllFontsEmbedded") and not observation.all_fonts_embedded:
        findings.append(_finding("fonts-embedded", "not all PDF fonts are embedded"))
    max_type3 = mechanical.get("maxType3Fonts")
    if isinstance(max_type3, int) and observation.type3_fonts > max_type3:
        findings.append(
            _finding(
                "type3-fonts",
                "Type 3 font count exceeds contract",
                evidence={"observed": observation.type3_fonts, "max": max_type3},
            )
        )
    for key, attr, finding_id in (
        ("maxOverfullBoxes", "overfull_boxes", "overfull-boxes"),
        ("maxUndefinedCitations", "undefined_citations", "undefined-citations"),
        ("maxUndefinedReferences", "undefined_references", "undefined-references"),
    ):
        limit = mechanical.get(key)
        observed = getattr(observation, attr)
        if isinstance(limit, int) and observed is None:
            findings.append(
                _finding(
                    f"{finding_id}:unobserved",
                    f"{attr} is required by the contract but was not observed",
                )
            )
        elif isinstance(limit, int) and observed > limit:
            findings.append(
                _finding(
                    finding_id,
                    f"{attr} exceeds contract",
                    evidence={"observed": observed, "max": limit},
                )
            )

    semantics = contract.get("textSemantics", {})
    for rule in semantics.get("requiredRegex", []):
        pattern = rule["pattern"]
        if re.search(pattern, observation.text, re.IGNORECASE | re.MULTILINE) is None:
            findings.append(
                _finding(
                    rule["id"],
                    f"required publication text pattern is absent: {pattern}",
                )
            )
    for rule in semantics.get("forbiddenRegex", []):
        pattern = rule["pattern"]
        matches = re.findall(pattern, observation.text, re.IGNORECASE | re.MULTILINE)
        if matches:
            findings.append(
                _finding(
                    rule["id"],
                    f"forbidden publication text pattern is present: {pattern}",
                    evidence={"matchCount": len(matches)},
                )
            )
    for rule in semantics.get("exactRegexCounts", []):
        pattern = rule["pattern"]
        count = len(re.findall(pattern, observation.text, re.IGNORECASE | re.MULTILINE))
        expected = rule["count"]
        if count != expected:
            findings.append(
                _finding(
                    rule["id"],
                    "publication text pattern count differs from contract",
                    evidence={"observed": count, "expected": expected},
                )
            )

    if semantics.get("forbidMarkdownHeadingResidue"):
        residue = [
            {"page": page_no, "line": line_no, "text": line}
            for page_no, page in enumerate(observation.pages, start=1)
            for line_no, line in enumerate(page.splitlines(), start=1)
            if re.search(r"^\s*#{1,6}\s+\S", line)
        ]
        if residue:
            findings.append(
                _finding(
                    "markdown-heading-residue",
                    "rendered carrier contains literal Markdown heading syntax",
                    evidence={"occurrences": residue[:20], "count": len(residue)},
                )
            )

    if semantics.get("detectDuplicateFigureCaptions"):
        caption_rx = re.compile(
            r"^\s*(?:Fig\.|Figure)\s+(\d+)\s*[:.]\s*",
            re.IGNORECASE,
        )
        occurrences: dict[str, list[dict[str, Any]]] = {}
        for page_no, page in enumerate(observation.pages, start=1):
            for line_no, line in enumerate(page.splitlines(), start=1):
                match = caption_rx.search(line)
                if match is None:
                    continue
                occurrences.setdefault(match.group(1), []).append(
                    {"page": page_no, "line": line_no, "text": line}
                )
        for figure_id, rows in sorted(occurrences.items(), key=lambda item: int(item[0])):
            if len(rows) > 1:
                findings.append(
                    _finding(
                        f"duplicate-figure-caption:{figure_id}",
                        f"figure {figure_id} has more than one caption-like line",
                        evidence={"count": len(rows), "occurrences": rows[:20]},
                    )
                )

    page_rules = contract.get("pageRules", {})
    total_max = page_rules.get("totalPagesMax")
    if isinstance(total_max, int) and observation.page_count > total_max:
        findings.append(
            _finding(
                "total-pages",
                "total PDF pages exceed contract",
                evidence={"observed": observation.page_count, "max": total_max},
            )
        )

    locations: dict[str, list[tuple[int, int, str]]] = {}
    heading_rules = page_rules.get("headings", [])
    for rule in heading_rules:
        rule_id = rule["id"]
        found = _heading_locations(observation.pages, rule["pattern"])
        locations[rule_id] = found
        if not found:
            findings.append(_finding(f"{rule_id}:missing", f"required heading is absent: {rule_id}"))
            continue
        first = found[0]
        min_page = rule.get("minPage")
        max_page = rule.get("maxPage")
        if isinstance(min_page, int) and first[0] < min_page:
            findings.append(
                _finding(
                    f"{rule_id}:min-page",
                    f"{rule_id} begins before allowed page",
                    evidence={"page": first[0], "minPage": min_page},
                )
            )
        if isinstance(max_page, int) and first[0] > max_page:
            findings.append(
                _finding(
                    f"{rule_id}:max-page",
                    f"{rule_id} begins after allowed page",
                    evidence={"page": first[0], "maxPage": max_page},
                )
            )

    rules_by_id = {rule["id"]: rule for rule in heading_rules}
    for rule_id, rule in rules_by_id.items():
        predecessor = rule.get("mustFollow")
        if not predecessor:
            continue
        current = locations.get(rule_id, [])
        previous = locations.get(predecessor, [])
        if current and previous and _position_key(current[0]) <= _position_key(previous[0]):
            findings.append(
                _finding(
                    f"{rule_id}:order",
                    f"{rule_id} must follow {predecessor}",
                    evidence={
                        "current": {"page": current[0][0], "line": current[0][1]},
                        "predecessor": {"page": previous[0][0], "line": previous[0][1]},
                    },
                )
            )

    machine_standing = "FAIL" if findings else "PASS"
    human_gates: list[str] = []
    reviewer = contract.get("reviewerExperience", {})
    if reviewer.get("humanPerceptualSignoffRequired") and not observation.human_perceptual_signoff:
        human_gates.append("HUMAN_PERCEPTUAL_SIGNOFF")

    if machine_standing == "FAIL":
        standing = "FAIL"
    elif human_gates:
        standing = "PENDING_HUMAN"
    else:
        standing = "PASS"

    return {
        "schemaVersion": 1,
        "kind": "publication-carrier-contract-evaluation",
        "contractId": contract["id"],
        "pdfSha256": "sha256:" + observation.pdf_sha256.lower(),
        "machineStanding": machine_standing,
        "standing": standing,
        "findings": findings,
        "humanGates": human_gates,
        "nonClaims": [
            "machine PASS is not scientific correctness",
            "machine PASS is not Human perceptual quality",
            "venue authority remains external to Artifact",
        ],
    }
