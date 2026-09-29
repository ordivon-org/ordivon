from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ScanState(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True, slots=True)
class ScanResult:
    state: ScanState
    findings: tuple[str, ...] = ()
    risk_tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AdvisoryProjection:
    content: str
    removed_risk_tags: tuple[str, ...] = ()


_SENSITIVE_NAMES = {".env", "id_rsa", "id_ed25519", "credentials.json", "secrets.json"}
_PRIVATE_KEY_BEGIN_RE = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
_PRIVATE_KEY_BLOCK_RE = re.compile(
    rb"-----BEGIN (?P<kind>(?:RSA |EC |OPENSSH )?PRIVATE KEY)-----\r?\n"
    rb"(?P<body>(?:[A-Za-z0-9+/=]{16,}\r?\n){4,})"
    rb"-----END (?P=kind)-----"
)
_PIPE_SHELL_RE = re.compile(r"\b(?:curl|wget)\b[^\n|]{0,512}\|\s*(?:sh|bash)\b", re.IGNORECASE)
_PROMPT_OVERRIDE_RE = re.compile(
    r"\bignore\s+(?:all\s+)?(?:previous|prior)\s+instructions\b",
    re.IGNORECASE,
)
_SELF_ROUTING_RE = re.compile(
    r"(?:\b(?:must|always|absolutely|before\s+any\s+response|do\s+not\s+have\s+a\s+choice|not\s+negotiable)\b[^\n]{0,180}\b(?:invoke|use|select|check)\b[^\n]{0,80}\bskill\b|"
    r"\b(?:invoke|use|select|check)\b[^\n]{0,80}\bskill\b[^\n]{0,180}\b(?:must|always|before\s+any\s+response|before\s+clarifying)\b)",
    re.IGNORECASE,
)
_SELF_PRIORITY_RE = re.compile(
    r"\b(?:skill\s+priority|skills?\s+come\s+first|skills?\s+.*override\s+default\s+behavior)\b",
    re.IGNORECASE,
)
_MANDATED_CITATION_RE = re.compile(
    r"(?:citing\s+scientific\s+agent\s+skills|materially\s+contributed[^\n]{0,180}(?:cite|references?|software\s+section|tell\s+the\s+user)|"
    r"\b(?:must|always)\s+cite\b)",
    re.IGNORECASE,
)
_MANDATED_DISCLOSURE_RE = re.compile(
    r"(?:tell\s+the\s+user\s+you\s+did\s+so|announce\s+[\"']using\s+\[?skill)",
    re.IGNORECASE,
)
_CONTROL_PLANE_DIRECTIVE_RE = re.compile(
    r"(?:\bmandatory\s+load\s+order\b|"
    r"\bhard\s+rule\b[^\n]{0,200}\b(?:route|routing|authority|load|selected|execution|response|confirmation|approval)\b|"
    r"\bthis\s+file\s+wins\b|"
    r"\b(?:active|selected)\s+(?:runtime\s+)?authority\s+owns\s+execution\b|"
    r"\bblocking\s+means\s+stop\b|"
    r"\bstops?\s+(?:the\s+)?skill\s+immediately\b)",
    re.IGNORECASE,
)
_USER_INTERACTION_MANDATE_RE = re.compile(
    r"(?:\bwait\s+for\s+explicit\s+user\s+(?:confirmation|approval|permission)\b|"
    r"\bdo\s+not\s+decide\s+on\s+the\s+user'?s\s+behalf\b|"
    r"\b(?:must|mandatory)\b[^\n]{0,120}\b(?:ask|confirm|wait|pause)\b[^\n]{0,80}\b(?:user|confirmation|approval|permission)\b)",
    re.IGNORECASE,
)
_SKILL_NAME_ATOM = r"[a-z0-9][a-z0-9._-]{1,63}"
_MARKED_TOKEN_PATTERN = (
    r"(?:`" + _SKILL_NAME_ATOM + r"`|"
    r"\*\*" + _SKILL_NAME_ATOM + r"\*\*|"
    r"\[`" + _SKILL_NAME_ATOM + r"`\]\([^)]+\)|"
    r"\[" + _SKILL_NAME_ATOM + r"\]\([^)]+\))"
)
_CROSS_SKILL_ROUTING_RE = re.compile(
    r"(?:\b(?:read|run|invoke|call|select)\b.{0,220}?" + _MARKED_TOKEN_PATTERN + r".{0,100}?\b(?:skill|workflow)\b|"
    r"\bhand\s+off\s+to\b.{0,120}?" + _MARKED_TOKEN_PATTERN + r"|"
    r"\b(?:use|see)\b\s+(?:the\s+)?(?P<bare>[a-z0-9][a-z0-9._]*[-.][a-z0-9._-]+)(?:\s+skill)?\b|"
    r"\blet\s+(?:that|the)\s+skill\s+run\b)",
    re.IGNORECASE | re.DOTALL,
)
_SELF_SERVING_SECTION_HEADING_RE = re.compile(
    r"^(?P<hashes>#{1,6})\s+(?:citing\s+scientific\s+agent\s+skills|skill\s+attribution|citation\s+requirement)\s*$",
    re.IGNORECASE,
)
def _markdown_blocks(text: str) -> tuple[str, ...]:
    """Return coarse Markdown paragraphs/blocks while preserving cross-line prose."""
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines(keepends=True):
        if not line.strip():
            if current:
                blocks.append("".join(current))
                current = []
            blocks.append(line)
        else:
            current.append(line)
    if current:
        blocks.append("".join(current))
    return tuple(blocks)

SANITIZABLE_AUTHORITY_RISK_TAGS = frozenset({
    "OVERRIDE_HIGHER_AUTHORITY",
    "SELF_ROUTING",
    "SELF_PRIORITY",
    "MANDATED_CITATION",
    "MANDATED_DISCLOSURE",
    "CONTROL_PLANE_DIRECTIVE",
    "USER_INTERACTION_MANDATE",
    "CROSS_SKILL_ROUTING",
})


def _line_risk_tags(line: str) -> tuple[str, ...]:
    checks = (
        ("OVERRIDE_HIGHER_AUTHORITY", _PROMPT_OVERRIDE_RE),
        ("SELF_ROUTING", _SELF_ROUTING_RE),
        ("SELF_PRIORITY", _SELF_PRIORITY_RE),
        ("MANDATED_CITATION", _MANDATED_CITATION_RE),
        ("MANDATED_DISCLOSURE", _MANDATED_DISCLOSURE_RE),
        ("CONTROL_PLANE_DIRECTIVE", _CONTROL_PLANE_DIRECTIVE_RE),
        ("USER_INTERACTION_MANDATE", _USER_INTERACTION_MANDATE_RE),
        ("CROSS_SKILL_ROUTING", _CROSS_SKILL_ROUTING_RE),
    )
    return tuple(tag for tag, pattern in checks if pattern.search(line))


def project_advisory_skill_text(text: str) -> AdvisoryProjection:
    """Project Skill Markdown as advisory knowledge with control-plane blocks removed.

    The source package stays byte-for-byte untouched.  This projection is for
    model consumption only; raw bytes remain available behind explicit raw
    revision-bound resource semantics.
    """
    # First remove whole self-serving attribution/citation sections structurally.
    prefiltered: list[str] = []
    removed: list[str] = []
    skip_section_level: int | None = None
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        heading = re.match(r"^(#{1,6})\s+", stripped)
        if skip_section_level is not None:
            if heading and len(heading.group(1)) <= skip_section_level:
                skip_section_level = None
            else:
                continue
        section = _SELF_SERVING_SECTION_HEADING_RE.match(stripped)
        if section:
            skip_section_level = len(section.group("hashes"))
            if "MANDATED_CITATION" not in removed:
                removed.append("MANDATED_CITATION")
            continue
        prefiltered.append(line)

    # Strip self-contained dangerous lines first so a local control directive
    # does not erase unrelated useful prose in the same Markdown paragraph.
    # Then perform one cross-line pass on the surviving block to catch split
    # routing constructs such as "read the sibling" + linked Skill next line.
    out: list[str] = []
    for block in _markdown_blocks("".join(prefiltered)):
        if not block.strip():
            out.append(block)
            continue
        safe_lines: list[str] = []
        saw_cross_skill_routing = False
        for line in block.splitlines(keepends=True):
            tags = _line_risk_tags(line)
            if tags:
                if "CROSS_SKILL_ROUTING" in tags:
                    saw_cross_skill_routing = True
                for tag in tags:
                    if tag not in removed:
                        removed.append(tag)
                continue
            safe_lines.append(line)
        if saw_cross_skill_routing or not safe_lines:
            continue
        survivor = "".join(safe_lines)
        normalized = re.sub(r"\s+", " ", survivor).strip()
        cross_tags = _line_risk_tags(normalized)
        if cross_tags:
            for tag in cross_tags:
                if tag not in removed:
                    removed.append(tag)
            continue
        out.append(survivor)
    return AdvisoryProjection("".join(out), tuple(removed))

_MAX_SCAN_FILE_BYTES = 1024 * 1024
_MAX_FINDINGS = 16


def scan_skill_package(root: Path) -> ScanResult:
    findings: list[str] = []
    risk_tags: list[str] = []
    quarantined = False
    warned = False

    def flag(tag: str, finding: str) -> None:
        nonlocal warned
        warned = True
        if tag not in risk_tags:
            risk_tags.append(tag)
        if len(findings) < _MAX_FINDINGS:
            findings.append(finding)

    for candidate in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        relative = candidate.relative_to(root).as_posix()
        if candidate.name.casefold() in _SENSITIVE_NAMES:
            quarantined = True
            if "CREDENTIAL_MATERIAL" not in risk_tags:
                risk_tags.append("CREDENTIAL_MATERIAL")
            if len(findings) < _MAX_FINDINGS:
                findings.append(f"credential-like file name: {relative}")
        try:
            size = candidate.stat().st_size
        except OSError:
            continue
        if size > _MAX_SCAN_FILE_BYTES:
            continue
        try:
            raw = candidate.read_bytes()
        except OSError:
            continue
        if _PRIVATE_KEY_BLOCK_RE.search(raw):
            quarantined = True
            if "CREDENTIAL_MATERIAL" not in risk_tags:
                risk_tags.append("CREDENTIAL_MATERIAL")
            if len(findings) < _MAX_FINDINGS:
                findings.append(f"complete private-key PEM block: {relative}")
        elif _PRIVATE_KEY_BEGIN_RE.search(raw):
            flag("PRIVATE_KEY_MATERIAL", f"private-key-like text material: {relative}")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if _PIPE_SHELL_RE.search(text):
            flag("NETWORK_PIPE_SHELL", f"network pipe-to-shell pattern: {relative}")
        if candidate.suffix.casefold() == ".md":
            if _PROMPT_OVERRIDE_RE.search(text):
                flag("OVERRIDE_HIGHER_AUTHORITY", f"prompt-override-like instruction: {relative}")
            if _SELF_ROUTING_RE.search(text):
                flag("SELF_ROUTING", f"self-routing instruction: {relative}")
            if _SELF_PRIORITY_RE.search(text):
                flag("SELF_PRIORITY", f"self-priority instruction: {relative}")
            if _MANDATED_CITATION_RE.search(text):
                flag("MANDATED_CITATION", f"self-serving citation directive: {relative}")
            if _MANDATED_DISCLOSURE_RE.search(text):
                flag("MANDATED_DISCLOSURE", f"self-serving disclosure directive: {relative}")
            if _CONTROL_PLANE_DIRECTIVE_RE.search(text):
                flag("CONTROL_PLANE_DIRECTIVE", f"skill-local control-plane directive: {relative}")
            if _USER_INTERACTION_MANDATE_RE.search(text):
                flag("USER_INTERACTION_MANDATE", f"skill-mandated user-interaction policy: {relative}")
            if _CROSS_SKILL_ROUTING_RE.search(re.sub(r"\s+", " ", text)):
                flag("CROSS_SKILL_ROUTING", f"cross-skill routing directive: {relative}")
    result = (tuple(findings), tuple(risk_tags))
    if quarantined:
        return ScanResult(ScanState.QUARANTINED, *result)
    if warned:
        return ScanResult(ScanState.WARN, *result)
    return ScanResult(ScanState.PASS, *result)
