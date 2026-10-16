#!/usr/bin/env python3
"""Build a rebuildable source-cut information/reference census.

The census is deliberately a projection. It does not mint a universal object ontology,
turn references into authority, or infer semantic relations from field names. It records
only mechanically observable carrier, identity, and reference facts from the exact Git
checkout and preserves ambiguity/unknowns.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import posixpath
import re
import subprocess
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import affected_owners

ROOT = Path(__file__).resolve().parents[2]

TOP_LEVEL_PREFIXES = (
    ".agents/",
    ".github/",
    "apps/",
    "capabilities/",
    "catalogs/",
    "docs/",
    "domains/",
    "extensions/",
    "meta/",
    "packages/",
    "platform/",
    "profiles/",
    "services/",
    "studies/",
    "tests/",
    "tools/",
)
MEDIA_TYPE_PREFIXES = (
    "application/",
    "audio/",
    "font/",
    "image/",
    "message/",
    "model/",
    "multipart/",
    "text/",
    "video/",
)
HOST_PATH_PREFIXES = (
    "etc/",
    "home/",
    "mnt/",
    "opt/",
    "proc/",
    "root/",
    "tmp/",
    "usr/",
    "var/",
)
PATH_KEY_RE = re.compile(
    r"(path|paths|file|files|source|sources|evidence|artifact|carrier|contract|schema|"
    r"implementation|script|module|document|docs|location|manifest|workflow|receipt|"
    r"fixture|profile|report|input|output|target|subject|binding|reference)",
    re.IGNORECASE,
)
HISTORICAL_HINT_RE = re.compile(
    r"(old|legacy|retir|delete|histor|previous|prior|supersed|relocat|archive)",
    re.IGNORECASE,
)
PATH_SHAPE_RE = re.compile(
    r"^(?:\./|\.\./)?[A-Za-z0-9_.@:+-]+(?:/[A-Za-z0-9_.@:+-]+)+(?:\.[A-Za-z0-9_.+-]+)$"
)
NAMESPACE_REF_RE = re.compile(
    r"^(work|space|topic|message|runtime|git|skill|agent|actor|artifact|job|attempt|"
    r"capability|study|research|provider|owner):"
)
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
REVISION_KEY_RE = re.compile(
    r"(revision|commit|sourceRevision|implementationRevision|headRevision|baseRevision)",
    re.IGNORECASE,
)
MARKDOWN_BACKTICK_RE = re.compile(chr(96) + r"([^\n]+?)" + chr(96))
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def _git(*args: str, input_text: str | None = None) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        input=input_text,
        capture_output=True,
    )
    return proc.stdout.strip()


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _current_head(revision: str) -> tuple[str, str]:
    resolved = _git("rev-parse", f"{revision}^{{commit}}")
    head = _git("rev-parse", "HEAD^{commit}")
    if resolved != head:
        raise ValueError(
            "information census must be built from the exact checked-out HEAD; "
            "checkout the requested revision first"
        )
    return resolved, _git("show", "-s", "--format=%T", resolved)


def tracked_files() -> tuple[str, ...]:
    return tuple(line for line in _git("ls-files").splitlines() if line)


def tracked_directories(paths: Iterable[str]) -> set[str]:
    directories: set[str] = set()
    for path in paths:
        parent = posixpath.dirname(path)
        while parent:
            directories.add(parent)
            next_parent = posixpath.dirname(parent)
            if next_parent == parent:
                break
            parent = next_parent
    return directories


def file_basename_index(paths: Iterable[str]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for path in paths:
        name = posixpath.basename(path)
        index.setdefault(name, []).append(path)
    return {name: sorted(values) for name, values in index.items()}


def carrier_family(path: str) -> str:
    lower = path.lower()
    if path.startswith("catalogs/knowledge/"):
        return "knowledge"
    if path.startswith("catalogs/authorities/"):
        return "external-authority"
    if path.startswith("catalogs/capabilities/"):
        return "capability-catalog"
    if path.startswith(".agents/skills/"):
        return "skill"
    if path.startswith("studies/"):
        return "study"
    if path.startswith("profiles/research/") or "/research/" in path:
        return "research"
    if "/evidence/" in path or path.startswith("services/harness/evidence/"):
        return "evidence"
    if "friction" in lower or "incident" in lower:
        return "friction-incident"
    if "/planning/" in path:
        return "planning"
    if path.startswith("docs/architecture/"):
        return "architecture"
    if path.startswith("services/runtime/"):
        return "runtime"
    if path.startswith("services/harness/"):
        return "harness"
    if path.startswith("services/host/"):
        return "host"
    if path.startswith("services/gateway/"):
        return "gateway"
    if path.startswith("packages/composition/"):
        return "composition"
    return "other"


def repository_owner_refs(path: str) -> list[str]:
    if path in affected_owners.CROSS_CUTTING_PATHS:
        return []
    return sorted(owner.name for owner in affected_owners.owners_for_paths((path,)))


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def historical_context_hint(carrier: str, pointer: str) -> bool:
    return bool(
        HISTORICAL_HINT_RE.search(carrier) or HISTORICAL_HINT_RE.search(pointer)
    )


def looks_like_source_path(value: str, key: str = "") -> bool:
    if not value or "://" in value:
        return False
    lower = value.lower()
    if lower.startswith(MEDIA_TYPE_PREFIXES) or lower.startswith(HOST_PATH_PREFIXES):
        return False
    if value.startswith(TOP_LEVEL_PREFIXES) or value.startswith(("./", "../")):
        return True
    return bool(PATH_SHAPE_RE.match(value) and PATH_KEY_RE.search(key))


def _ancestor_candidates(carrier: str, value: str, tracked: set[str]) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    carrier_parent = posixpath.dirname(carrier)

    # Explicit ./ and ../ references have standard carrier-relative semantics.
    # Do not reinterpret them from every ancestor, which would manufacture
    # ambiguity (for example ../README.md matching both owner and root README).
    if value.startswith(("./", "../")):
        candidate = posixpath.normpath(posixpath.join(carrier_parent, value))
        if (
            candidate != ".."
            and not candidate.startswith("../")
            and candidate in tracked
        ):
            candidates.append(candidate)
        return candidates

    root_candidate = posixpath.normpath(value)
    if root_candidate in tracked:
        candidates.append(root_candidate)
        seen.add(root_candidate)

    # Bare owner-local references are common in historical/domain carriers.
    # Search carrier ancestors only to find mechanically unique candidates.
    parent = carrier_parent
    while True:
        candidate = posixpath.normpath(posixpath.join(parent, value))
        if (
            candidate not in seen
            and candidate != ".."
            and not candidate.startswith("../")
            and candidate in tracked
        ):
            candidates.append(candidate)
            seen.add(candidate)
        if not parent:
            break
        next_parent = posixpath.dirname(parent)
        if next_parent == parent:
            break
        parent = next_parent

    return sorted(candidates)


def resolve_source_path(
    carrier: str,
    value: str,
    tracked: set[str],
    *,
    pointer: str = "",
    directories: set[str] | None = None,
    locations: set[str] | None = None,
    basename_index: dict[str, list[str]] | None = None,
) -> dict[str, object]:
    location_set = (
        locations if locations is not None else tracked | (directories or set())
    )
    candidates = _ancestor_candidates(carrier, value, location_set)
    if len(candidates) == 1:
        standing = "EXACT_UNIQUE"
    elif len(candidates) > 1:
        standing = "AMBIGUOUS_EXACT"
    else:
        standing = "UNRESOLVED_IN_SOURCE_CUT"

    candidate_kinds = [
        {
            "path": candidate,
            "kind": "file" if candidate in tracked else "directory",
        }
        for candidate in candidates
    ]

    alternate_location_hints: list[str] = []
    if not candidates and basename_index is not None:
        basename = posixpath.basename(value.rstrip("/"))
        alternate_location_hints = list(basename_index.get(basename, []))

    return {
        "standing": standing,
        "historicalContextHint": historical_context_hint(carrier, pointer),
        "candidates": candidates,
        "candidateKinds": candidate_kinds,
        "alternateLocationHints": alternate_location_hints,
    }


def _top_level_signal(payload: dict[str, object], key: str) -> object | None:
    value = payload.get(key)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def _record_namespace(
    details: list[dict[str, object]],
    counts: Counter[str],
    *,
    carrier: str,
    pointer: str,
    value: str,
) -> None:
    match = NAMESPACE_REF_RE.match(value)
    if match is None:
        return
    namespace = match.group(1)
    counts[namespace] += 1
    details.append(
        {
            "carrier": carrier,
            "jsonPointer": pointer,
            "namespace": namespace,
            "value": value,
            "standing": "OWNER_BINDING_UNKNOWN",
        }
    )


def _walk_json(
    carrier: str,
    value: object,
    tracked: set[str],
    locations: set[str],
    basename_index: dict[str, list[str]],
    path_details: list[dict[str, object]],
    namespace_details: list[dict[str, object]],
    namespace_counts: Counter[str],
    git_revision_values: set[str],
    *,
    pointer: str = "",
    key: str = "",
) -> None:
    if isinstance(value, dict):
        for child_key, child in value.items():
            child_pointer = f"{pointer}/{_pointer_escape(str(child_key))}"
            _walk_json(
                carrier,
                child,
                tracked,
                locations,
                basename_index,
                path_details,
                namespace_details,
                namespace_counts,
                git_revision_values,
                pointer=child_pointer,
                key=str(child_key),
            )
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _walk_json(
                carrier,
                child,
                tracked,
                locations,
                basename_index,
                path_details,
                namespace_details,
                namespace_counts,
                git_revision_values,
                pointer=f"{pointer}/{index}",
                key=key,
            )
        return
    if not isinstance(value, str):
        return

    _record_namespace(
        namespace_details,
        namespace_counts,
        carrier=carrier,
        pointer=pointer,
        value=value,
    )

    if HEX40_RE.match(value) and REVISION_KEY_RE.search(key):
        git_revision_values.add(value)

    if looks_like_source_path(value, key):
        resolution = resolve_source_path(
            carrier,
            value,
            tracked,
            pointer=pointer,
            locations=locations,
            basename_index=basename_index,
        )
        path_details.append(
            {
                "carrier": carrier,
                "format": "json",
                "pointer": pointer,
                "declaredValue": value,
                **resolution,
            }
        )


def _markdown_values(text: str) -> Iterable[tuple[str, str]]:
    for match in MARKDOWN_BACKTICK_RE.finditer(text):
        yield f"backtick:{match.start(1)}", match.group(1).strip()
    for match in MARKDOWN_LINK_RE.finditer(text):
        yield f"link:{match.start(1)}", match.group(1).strip()


def _check_git_revisions(values: set[str]) -> tuple[set[str], set[str]]:
    if not values:
        return set(), set()

    ordered = sorted(values)
    proc = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype)"],
        cwd=ROOT,
        check=True,
        text=True,
        input="".join(f"{value}\n" for value in ordered),
        capture_output=True,
        # This source-cut inventory checks locally available Git objects only.
        # A promised but absent object is unresolved, not an instruction to
        # fetch remote bytes (which can block CI indefinitely).
        env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
    )
    lines = proc.stdout.splitlines()
    if len(lines) != len(ordered):
        raise ValueError("git batch revision check returned unexpected row count")

    exact: set[str] = set()
    unresolved: set[str] = set()
    for value, line in zip(ordered, lines, strict=True):
        if line == f"{value} commit":
            exact.add(value)
        else:
            unresolved.add(value)
    return exact, unresolved


def _compact_reference_counts(
    path_details: list[dict[str, object]],
) -> dict[str, int]:
    counts = Counter(str(row["standing"]) for row in path_details)
    counts["EXACT_UNIQUE_FILE"] = sum(
        1
        for row in path_details
        if row["standing"] == "EXACT_UNIQUE"
        and row.get("candidateKinds")
        and row["candidateKinds"][0]["kind"] == "file"
    )
    counts["EXACT_UNIQUE_DIRECTORY"] = sum(
        1
        for row in path_details
        if row["standing"] == "EXACT_UNIQUE"
        and row.get("candidateKinds")
        and row["candidateKinds"][0]["kind"] == "directory"
    )
    counts["UNRESOLVED_WITH_HISTORICAL_HINT"] = sum(
        1
        for row in path_details
        if row["standing"] == "UNRESOLVED_IN_SOURCE_CUT"
        and row["historicalContextHint"]
    )
    counts["UNRESOLVED_WITHOUT_HISTORICAL_HINT"] = sum(
        1
        for row in path_details
        if row["standing"] == "UNRESOLVED_IN_SOURCE_CUT"
        and not row["historicalContextHint"]
    )
    counts["UNRESOLVED_UNIQUE_ALTERNATE_LOCATION_HINT"] = sum(
        1
        for row in path_details
        if row["standing"] == "UNRESOLVED_IN_SOURCE_CUT"
        and len(row.get("alternateLocationHints", [])) == 1
    )
    counts["UNRESOLVED_MULTIPLE_ALTERNATE_LOCATION_HINTS"] = sum(
        1
        for row in path_details
        if row["standing"] == "UNRESOLVED_IN_SOURCE_CUT"
        and len(row.get("alternateLocationHints", [])) > 1
    )
    counts["UNRESOLVED_NO_ALTERNATE_LOCATION_HINT"] = sum(
        1
        for row in path_details
        if row["standing"] == "UNRESOLVED_IN_SOURCE_CUT"
        and not row.get("alternateLocationHints", [])
    )
    return dict(sorted(counts.items()))


def build_information_census(
    revision: str = "HEAD",
    *,
    include_details: bool = False,
    sample_limit: int = 32,
) -> dict[str, object]:
    source_revision, source_tree = _current_head(revision)
    paths = tracked_files()
    tracked = set(paths)
    directories = tracked_directories(paths)
    locations = tracked | directories
    basename_index = file_basename_index(paths)

    family_counts = Counter(carrier_family(path) for path in paths)
    owner_counts: Counter[str] = Counter()
    unowned_count = 0
    cross_cutting_count = 0
    for path in paths:
        if path in affected_owners.CROSS_CUTTING_PATHS:
            cross_cutting_count += 1
            continue
        owners = repository_owner_refs(path)
        if owners:
            owner_counts.update(owners)
        else:
            unowned_count += 1

    top_level_kinds: Counter[str] = Counter()
    top_level_signals: Counter[str] = Counter()
    path_details: list[dict[str, object]] = []
    namespace_details: list[dict[str, object]] = []
    namespace_counts: Counter[str] = Counter()
    git_revision_values: set[str] = set()
    parse_errors: list[dict[str, str]] = []
    json_files = 0
    markdown_files = 0
    top_level_kind_files = 0

    for path in paths:
        absolute = ROOT / path
        suffix = absolute.suffix.lower()

        if suffix == ".json":
            json_files += 1
            try:
                payload = json.loads(absolute.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                parse_errors.append(
                    {
                        "carrier": path,
                        "errorType": type(exc).__name__,
                        "detail": str(exc)[:240],
                    }
                )
                continue

            if isinstance(payload, dict):
                top_kind = payload.get("kind")
                if isinstance(top_kind, str) and top_kind:
                    top_level_kind_files += 1
                    top_level_kinds[top_kind] += 1
                for signal_key in (
                    "status",
                    "standing",
                    "state",
                    "truthRole",
                    "truth_role",
                ):
                    signal = _top_level_signal(payload, signal_key)
                    if signal is not None:
                        top_level_signals[f"{signal_key}={signal}"] += 1

            _walk_json(
                path,
                payload,
                tracked,
                locations,
                basename_index,
                path_details,
                namespace_details,
                namespace_counts,
                git_revision_values,
            )
            continue

        if suffix in {".md", ".mdx"}:
            markdown_files += 1
            try:
                text = absolute.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for pointer, value in _markdown_values(text):
                if not looks_like_source_path(value, "reference"):
                    continue
                resolution = resolve_source_path(
                    path,
                    value,
                    tracked,
                    pointer=pointer,
                    locations=locations,
                    basename_index=basename_index,
                )
                path_details.append(
                    {
                        "carrier": path,
                        "format": "markdown-explicit",
                        "pointer": pointer,
                        "declaredValue": value,
                        **resolution,
                    }
                )

    exact_git, unresolved_git = _check_git_revisions(git_revision_values)
    path_counts = _compact_reference_counts(path_details)

    unresolved_no_hint = [
        row
        for row in path_details
        if row["standing"] == "UNRESOLVED_IN_SOURCE_CUT"
        and not row["historicalContextHint"]
    ]
    unresolved_historical = [
        row
        for row in path_details
        if row["standing"] == "UNRESOLVED_IN_SOURCE_CUT"
        and row["historicalContextHint"]
    ]
    ambiguous = [row for row in path_details if row["standing"] == "AMBIGUOUS_EXACT"]
    unique_alternate = [
        row
        for row in path_details
        if row["standing"] == "UNRESOLVED_IN_SOURCE_CUT"
        and len(row.get("alternateLocationHints", [])) == 1
    ]

    details_body = {
        "sourcePathReferences": path_details,
        "namespaceShapedReferences": namespace_details,
        "gitRevisionCandidates": {
            "exactCurrentRepositoryCommits": sorted(exact_git),
            "unresolvedInCurrentRepository": sorted(unresolved_git),
        },
    }
    details_digest = canonical_digest(details_body)

    body: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.information-fragment-census",
        "truthRole": (
            "rebuildable-source-reference-projection-not-semantic-live-or-domain-authority"
        ),
        "sourceRevision": source_revision,
        "sourceTree": source_tree,
        "coverage": {
            "trackedFiles": len(paths),
            "jsonFiles": json_files,
            "markdownFiles": markdown_files,
            "jsonParseErrors": len(parse_errors),
            "topLevelKindFiles": top_level_kind_files,
            "uniqueTopLevelKinds": len(top_level_kinds),
            "referenceExtractionFormats": ["json", "markdown-explicit"],
            "coverageClaim": (
                "BOUNDED_FORMAT_AND_SYNTAX_COVERAGE_NOT_SEMANTIC_COMPLETENESS"
            ),
        },
        "carrierFamilies": [
            {"family": family_name, "count": count}
            for family_name, count in sorted(family_counts.items())
        ],
        "repositoryOwnerProjection": {
            "truthRole": "repository-mechanics-only-not-semantic-owner-inference",
            "ownerFileCounts": [
                {"ownerRef": owner, "count": count}
                for owner, count in sorted(owner_counts.items())
            ],
            "unownedTrackedFiles": unowned_count,
            "crossCuttingTrackedFiles": cross_cutting_count,
        },
        "structuredIdentityProjection": {
            "topLevelKinds": [
                {"kind": kind, "count": count}
                for kind, count in sorted(top_level_kinds.items())
            ],
            "topLevelSignals": [
                {"signal": signal, "count": count}
                for signal, count in sorted(top_level_signals.items())
            ],
            "identityLaw": (
                "Only top-level kind is counted as a structured carrier identity signal. "
                "Nested kind/status/relation fields remain payload-local and are not promoted."
            ),
        },
        "referenceProjection": {
            "sourcePathStandingCounts": path_counts,
            "namespaceShapedCounts": [
                {"namespace": namespace, "count": count}
                for namespace, count in sorted(namespace_counts.items())
            ],
            "gitRevisionCandidateCounts": {
                "exactCurrentRepositoryCommit": len(exact_git),
                "unresolvedInCurrentRepository": len(unresolved_git),
            },
            "detailsDigest": details_digest,
            "samples": {
                "ambiguousExact": ambiguous[:sample_limit],
                "unresolvedWithoutHistoricalHint": unresolved_no_hint[:sample_limit],
                "unresolvedWithHistoricalHint": unresolved_historical[:sample_limit],
                "uniqueAlternateLocationHint": unique_alternate[:sample_limit],
            },
            "resolutionLaw": (
                "EXACT means one mechanically unique tracked file/directory path or current-"
                "repository Git commit. Alternate-location hints are basename-only navigation "
                "candidates. AMBIGUOUS and UNRESOLVED remain non-semantic findings; none proves "
                "brokenness, staleness, relocation, or dangling domain truth."
            ),
        },
        "parseErrors": parse_errors[:sample_limit],
        "nonClaims": [
            "Carrier families are navigation facets, not a universal Ordivon ontology.",
            "Repository path ownership does not establish semantic authority.",
            "A namespace-shaped reference does not establish a natural owner and is not validated by this source-only projection.",
            "An unresolved source path may name an external, generated, historical, archived, or untracked carrier.",
            "A Git revision absent from the current repository may belong to historical or external lineage.",
            "A basename-only alternate-location hint does not establish relocation or identity.",
            "Lexical or structural co-reference does not establish semantic duplication.",
            "This census does not infer supports, causes, supersedes, depends-on, or other domain relations unless an owner already declares them.",
        ],
    }
    if include_details:
        body["details"] = details_body
    body["projectionDigest"] = canonical_digest(body)
    return body


def compact_information_census(census: dict[str, object]) -> dict[str, object]:
    compact = {key: value for key, value in census.items() if key != "details"}
    compact.pop("projectionDigest", None)
    compact["projectionDigest"] = canonical_digest(compact)
    return compact


def summarize_information_census(census: dict[str, object]) -> dict[str, object]:
    return {
        "schemaVersion": census["schemaVersion"],
        "kind": census["kind"],
        "truthRole": census["truthRole"],
        "sourceRevision": census["sourceRevision"],
        "sourceTree": census["sourceTree"],
        "coverage": census["coverage"],
        "carrierFamilies": census["carrierFamilies"],
        "repositoryOwnerProjection": census["repositoryOwnerProjection"],
        "referenceProjection": {
            "sourcePathStandingCounts": census["referenceProjection"][
                "sourcePathStandingCounts"
            ],
            "namespaceShapedCounts": census["referenceProjection"][
                "namespaceShapedCounts"
            ],
            "gitRevisionCandidateCounts": census["referenceProjection"][
                "gitRevisionCandidateCounts"
            ],
            "detailsDigest": census["referenceProjection"]["detailsDigest"],
            "resolutionLaw": census["referenceProjection"]["resolutionLaw"],
        },
        "structuredIdentityProjection": {
            "topLevelKindFiles": census["coverage"]["topLevelKindFiles"],
            "uniqueTopLevelKinds": census["coverage"]["uniqueTopLevelKinds"],
            "identityLaw": census["structuredIdentityProjection"]["identityLaw"],
        },
        "nonClaims": census["nonClaims"],
        "summaryDigest": canonical_digest(
            {
                "sourceRevision": census["sourceRevision"],
                "sourceTree": census["sourceTree"],
                "coverage": census["coverage"],
                "carrierFamilies": census["carrierFamilies"],
                "repositoryOwnerProjection": census["repositoryOwnerProjection"],
                "referenceProjection": census["referenceProjection"],
            }
        ),
    }


@functools.lru_cache(maxsize=8)
def _cached_information_summary_json(source_revision: str) -> str:
    summary = summarize_information_census(
        build_information_census(source_revision, include_details=False)
    )
    return json.dumps(
        summary,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def build_information_summary(revision: str = "HEAD") -> dict[str, object]:
    source_revision = _git("rev-parse", f"{revision}^{{commit}}")
    return json.loads(_cached_information_summary_json(source_revision))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an Ordivon source-cut information/reference census."
    )
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--details-output", type=Path)
    return parser


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = _parser().parse_args()
    try:
        detailed = build_information_census(
            args.revision, include_details=bool(args.details_output)
        )
        compact = compact_information_census(detailed)
    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        raise SystemExit(str(exc)) from exc

    if args.output:
        _write(args.output, compact)
    else:
        print(json.dumps(compact, indent=2, sort_keys=True, ensure_ascii=False))

    if args.details_output:
        _write(args.details_output, detailed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
