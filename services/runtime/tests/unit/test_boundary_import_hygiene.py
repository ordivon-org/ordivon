from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ACTIVE_DIRS = [
    "apps",
    "capabilities",
    "domains",
    "governance",
    "intelligence",
    "knowledge",
    "orchestrator",
    "shared",
    "state",
    "tools",
]
FORBIDDEN_IMPORTS = [
    "pfios.domain.analysis",
    "pfios.domain.recommendation",
    "pfios.domain.review",
    "pfios.domain.outcome",
    "pfios.domain.lessons",
    "pfios.domain.issue",
    "pfios.domain.usage",
    "pfios.domain.audit",
    "pfios.audit.auditor",
]


def test_active_code_does_not_import_migrated_legacy_truth_modules():
    offenders: list[str] = []

    for dirname in ACTIVE_DIRS:
        for path in (ROOT / dirname).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_IMPORTS:
                if forbidden in text:
                    offenders.append(f"{path.relative_to(ROOT)} -> {forbidden}")

    assert offenders == []
