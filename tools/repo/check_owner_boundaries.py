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
    "meta/next/authorities/",
    "meta/next/knowledge/",
    "meta/next/domains/",
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
    seen: set[Seam] = set()
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
        seam = Seam(**values)
        if seam in seen:
            raise ValueError(f"duplicate dependency seam: {seam.from_owner}->{seam.to_owner}:{seam.source_glob}")
        seen.add(seam)
        result.append(seam)
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
    # Git paths are byte strings: its default quoted presentation can hide
    # an active source file from the actual cross-Owner consumer scan.
    # NUL records preserve embedded newlines and non-UTF-8 path bytes.
    output = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"])
    return tuple(
        path
        for part in output.split(b"\0")
        if part
        for path in (part.decode("utf-8", errors="surrogateescape"),)
        if is_active_path(path)
    )


def _matches_source_glob(path: str, pattern: str) -> bool:
    """A source_glob is an owner-local file pattern: '*' cannot cross '/'."""
    parts = path.split("/")
    globs = pattern.split("/")
    return len(parts) == len(globs) and all(
        fnmatch.fnmatchcase(part, glob)
        for part, glob in zip(parts, globs, strict=True)
    )


def _matching_seams(
    finding: Finding,
    seams: tuple[Seam, ...],
) -> tuple[Seam, ...]:
    """Bind each exception to one exact source/consumer literal."""
    return tuple(
        seam for seam in seams
        if seam.from_owner == finding.from_owner
        and seam.to_owner == finding.to_owner
        and _matches_source_glob(finding.source_path, seam.source_glob)
        and seam.allowed_fragment in finding.text
    )


def _allowed(finding: Finding, seams: tuple[Seam, ...]) -> bool:
    return bool(_matching_seams(finding, seams))


def validate_consumed_seams(
    seams: tuple[Seam, ...],
    findings: tuple[Finding, ...],
) -> dict[Seam, tuple[tuple[str, int], ...]]:
    """Reject ghost or overlapping Owner permissions via the existing policy.

    This establishes exact source-text use only, not runtime calls or
    consumer-domain safety; a referenced line may be dead/commented code.
    """
    observations: dict[Seam, list[tuple[str, int]]] = {seam: [] for seam in seams}
    for finding in findings:
        matches = _matching_seams(finding, seams)
        if len(matches) > 1:
            raise AssertionError(
                "ambiguous dependency seam: multiple exceptions match "
                f"{finding.source_path}:{finding.line}"
            )
        if matches:
            observations[matches[0]].append((finding.source_path, finding.line))
    stale = [seam for seam, uses in observations.items() if not uses]
    if stale:
        rendered = ", ".join(
            f"{seam.from_owner}->{seam.to_owner}:{seam.source_glob} "
            f"[{seam.allowed_fragment}]"
            for seam in stale
        )
        raise AssertionError("stale dependency seam declarations: " + rendered)
    return {seam: tuple(uses) for seam, uses in observations.items()}


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

    # A declared source/consumer permission is admitted only by the same
    # exact typed matcher used to permit it. Pair+glob alone is insufficient:
    # it can let obsolete or shadow permissions survive indefinitely.
    witnessed = validate_consumed_seams(seams, tuple(all_findings))
    kinds: dict[str, int] = {}
    for seam, uses in witnessed.items():
        kinds[seam.kind] = kinds.get(seam.kind, 0) + len(uses)

    print(
        "owner boundary literals: valid "
        f"(active_files={len(tracked_active_files())}, seams={len(seams)}, "
        f"references={len(all_findings)}, kinds={dict(sorted(kinds.items()))})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
