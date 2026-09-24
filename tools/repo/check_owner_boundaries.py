#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from affected_owners import Owner, load_owners

ROOT = Path(__file__).resolve().parents[2]
POLICY = Path(__file__).with_name("dependency_contracts.toml")

ACTIVE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".mjs", ".rs", ".sh", ".ps1",
    ".tf", ".toml", ".json", ".yml", ".yaml",
}
IGNORED_COMPONENTS = {
    "docs", "evidence", "planning", "research", "experiments", "fixtures", "artifacts",
}
IGNORED_PREFIXES = (
    "catalogs/authorities/",
    "catalogs/knowledge/",
    "profiles/domains/",
)


@dataclass(frozen=True)
class Seam:
    from_owner: str
    to_owner: str
    source_glob: str
    allowed_fragment: str
    kind: str
    contract_ref: str


@dataclass(frozen=True)
class Finding:
    source_path: str
    line: int
    from_owner: str
    to_owner: str
    text: str


def load_policy(path: Path = POLICY) -> tuple[Seam, ...]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("dependency policy schema_version must be 1")
    if data.get("truth_role") != "repository-boundary-policy-not-domain-authority":
        raise ValueError("dependency policy truth_role must remain repository-boundary-only")
    if data.get("scan_mode") != "active-source-literal-seams":
        raise ValueError("unexpected dependency policy scan_mode")
    rows = data.get("seams", [])
    if not isinstance(rows, list):
        raise ValueError("dependency policy seams must be an array")
    result: list[Seam] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"seam {index} must be a table")
        values = {key: row.get(key) for key in (
            "from_owner", "to_owner", "source_glob", "allowed_fragment", "kind", "contract_ref"
        )}
        if not all(isinstance(value, str) and value for value in values.values()):
            raise ValueError(f"seam {index} has missing/empty fields")
        if values["from_owner"] == values["to_owner"]:
            raise ValueError(f"seam {index} cannot point to the same owner")
        result.append(Seam(**values))
    return tuple(result)


def owner_for_path(path: str, owners: tuple[Owner, ...]) -> Owner | None:
    return next((owner for owner in owners if path.startswith(owner.root)), None)


def is_active_path(path: str) -> bool:
    candidate = Path(path)
    if candidate.suffix not in ACTIVE_EXTENSIONS:
        return False
    if any(path.startswith(prefix) for prefix in IGNORED_PREFIXES):
        return False
    if any(component in IGNORED_COMPONENTS for component in candidate.parts):
        return False
    return True


def tracked_active_files() -> tuple[str, ...]:
    output = subprocess.check_output(["git", "-C", str(ROOT), "ls-files"], text=True)
    return tuple(path for path in output.splitlines() if is_active_path(path))


def _allowed(
    finding: Finding,
    seams: tuple[Seam, ...],
) -> bool:
    return any(
        seam.from_owner == finding.from_owner
        and seam.to_owner == finding.to_owner
        and fnmatch.fnmatchcase(finding.source_path, seam.source_glob)
        and seam.allowed_fragment in finding.text
        for seam in seams
    )


def findings_for_text(
    source_path: str,
    text: str,
    owners: tuple[Owner, ...],
) -> tuple[Finding, ...]:
    source = owner_for_path(source_path, owners)
    if source is None:
        return ()
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for target in owners:
            if target.name == source.name:
                continue
            target_literal = target.root.rstrip("/")
            if target_literal in line:
                findings.append(
                    Finding(
                        source_path=source_path,
                        line=line_number,
                        from_owner=source.name,
                        to_owner=target.name,
                        text=line.strip(),
                    )
                )
    return tuple(findings)


def main() -> int:
    owners = load_owners()
    owner_names = {owner.name for owner in owners}
    seams = load_policy()

    for seam in seams:
        if seam.from_owner not in owner_names or seam.to_owner not in owner_names:
            raise AssertionError(
                f"dependency seam names unknown owner: {seam.from_owner}->{seam.to_owner}"
            )
        ref = ROOT / seam.contract_ref
        if not ref.is_file():
            raise AssertionError(f"dependency seam contract_ref missing: {seam.contract_ref}")

    all_findings: list[Finding] = []
    violations: list[Finding] = []
    for source_path in tracked_active_files():
        source = owner_for_path(source_path, owners)
        if source is None:
            continue
        text = (ROOT / source_path).read_text(encoding="utf-8", errors="ignore")
        for finding in findings_for_text(source_path, text, owners):
            all_findings.append(finding)
            if not _allowed(finding, seams):
                violations.append(finding)

    if violations:
        rendered = "\n".join(
            f"{item.source_path}:{item.line}: "
            f"{item.from_owner}->{item.to_owner}: {item.text}"
            for item in violations
        )
        raise AssertionError(
            "undeclared active cross-owner source-path seams detected:\n" + rendered
        )

    used = {
        (item.from_owner, item.to_owner, item.source_path)
        for item in all_findings
    }
    stale: list[Seam] = []
    for seam in seams:
        if not any(
            from_owner == seam.from_owner
            and to_owner == seam.to_owner
            and fnmatch.fnmatchcase(source_path, seam.source_glob)
            for from_owner, to_owner, source_path in used
        ):
            stale.append(seam)
    if stale:
        rendered = ", ".join(
            f"{item.from_owner}->{item.to_owner}:{item.source_glob}" for item in stale
        )
        raise AssertionError(f"stale dependency seam declarations: {rendered}")

    kinds: dict[str, int] = {}
    for finding in all_findings:
        for seam in seams:
            if (
                seam.from_owner == finding.from_owner
                and seam.to_owner == finding.to_owner
                and fnmatch.fnmatchcase(finding.source_path, seam.source_glob)
                and seam.allowed_fragment in finding.text
            ):
                kinds[seam.kind] = kinds.get(seam.kind, 0) + 1
                break

    print(
        "owner boundary literals: valid "
        f"(active_files={len(tracked_active_files())}, seams={len(seams)}, "
        f"references={len(all_findings)}, kinds={dict(sorted(kinds.items()))})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
