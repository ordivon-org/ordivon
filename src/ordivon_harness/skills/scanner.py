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


_SENSITIVE_NAMES = {".env", "id_rsa", "id_ed25519", "credentials.json", "secrets.json"}
_PRIVATE_KEY_RE = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
_PIPE_SHELL_RE = re.compile(r"\b(?:curl|wget)\b[^\n|]{0,512}\|\s*(?:sh|bash)\b", re.IGNORECASE)
_PROMPT_OVERRIDE_RE = re.compile(
    r"\bignore\s+(?:all\s+)?(?:previous|prior)\s+instructions\b",
    re.IGNORECASE,
)
_MAX_SCAN_FILE_BYTES = 1024 * 1024
_MAX_FINDINGS = 16


def scan_skill_package(root: Path) -> ScanResult:
    findings: list[str] = []
    quarantined = False
    warned = False

    for candidate in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        relative = candidate.relative_to(root).as_posix()
        if candidate.name.casefold() in _SENSITIVE_NAMES:
            quarantined = True
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
        if _PRIVATE_KEY_RE.search(raw):
            if candidate.suffix.casefold() in {".key", ".pem"}:
                quarantined = True
                label = "private-key file material"
            else:
                warned = True
                label = "private-key-like text material"
            if len(findings) < _MAX_FINDINGS:
                findings.append(f"{label}: {relative}")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if _PIPE_SHELL_RE.search(text):
            warned = True
            if len(findings) < _MAX_FINDINGS:
                findings.append(f"network pipe-to-shell pattern: {relative}")
        if candidate.name == "SKILL.md" and _PROMPT_OVERRIDE_RE.search(text):
            warned = True
            if len(findings) < _MAX_FINDINGS:
                findings.append("prompt-override-like instruction in SKILL.md")

    if quarantined:
        return ScanResult(ScanState.QUARANTINED, tuple(findings))
    if warned:
        return ScanResult(ScanState.WARN, tuple(findings))
    return ScanResult(ScanState.PASS)
