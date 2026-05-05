"""Philosophy Misuse Checker — detects philosophical language rationalizing harm."""

from __future__ import annotations
import re, sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

RULES = [
    ("PGI-MISUSE-001", re.compile(r"\blong[- ]term(?:ism)?\b.{0,120}\b(?:ignore sleep|sacrifice (?:the )?body|no rest|burn out)\b", re.I),
     "Long-termism used to rationalize overwork or body neglect.", "Run Anti-Overforce review."),
    ("PGI-MISUSE-002", re.compile(r"\bfreedom\b.{0,120}\b(?:all[- ]in|high leverage|gamble|double down)\b", re.I),
     "Freedom language used to rationalize gambling.", "Run Finance Pack risk gate."),
    ("PGI-MISUSE-003", re.compile(r"\bdiscipline\b.{0,120}\b(?:ignore fatigue|suppress emotion|ignore emotion|push through pain)\b", re.I),
     "Discipline used to suppress body/emotion signals.", "Classify signal before increasing effort."),
    ("PGI-MISUSE-004", re.compile(r"\b(?:existential|meaning|destiny)\b.{0,120}\b(?:ignore evidence|skip evidence|bypass evidence)\b", re.I),
     "Meaning language used to bypass evidence.", "Restore EvidenceRecord requirement."),
    ("PGI-MISUSE-005", re.compile(r"\b(?:non[- ]attachment|wu wei|daoism|let it flow)\b.{0,120}\b(?:avoid responsibility|no review|do nothing)\b", re.I),
     "Non-attachment used to avoid responsibility.", "Separate non-force from avoidance."),
    ("PGI-MISUSE-006", re.compile(r"\bpragmatism\b.{0,120}\b(?:ignore principle|skip evidence|bypass boundary|shortcut)\b", re.I),
     "Pragmatism used to justify unprincipled shortcuts.", "Check Constitution boundary."),
]
SAFE = re.compile(r"red-team|unsafe fixture|do\s+not\b|must\s+not\b|not a justification|misuse", re.I)

SCAN_DIRS = ["docs", "AGENTS.md"]

@dataclass(frozen=True)
class CheckerResult:
    status: str; exit_code: int
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

def run():
    findings, stats = [], {"files":0,"findings":0}
    exts = {".md",".txt",".json",".jsonl"}
    files = []
    for d in SCAN_DIRS:
        p = ROOT/d
        if p.is_file(): files.append(p)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and f.suffix in exts and ".git/" not in str(f):
                    files.append(f)
    stats["files"] = len(files)
    for fp in files:
        try: rel = str(fp.relative_to(ROOT))
        except: rel = str(fp)
        try: lines = fp.read_text(encoding="utf-8",errors="replace").split("\n")
        except: continue
        for i,line in enumerate(lines,1):
            if SAFE.search(line): continue
            for rid, pat, expl, fix in RULES:
                m = pat.search(line)
                if m:
                    stats["findings"]+=1
                    findings.append(f"{rel}:{i} [{rid}] {expl}")
    return CheckerResult("fail" if findings else "pass", 1 if findings else 0, findings, dict(stats))

if __name__=="__main__":
    r=run(); print(f"Files: {r.stats.get('files',0)} | Findings: {len(r.findings)}")
    for f in r.findings: print(f"  {f}"); sys.exit(r.exit_code)
