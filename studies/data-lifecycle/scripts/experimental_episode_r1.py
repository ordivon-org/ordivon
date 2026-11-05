#!/usr/bin/env python3
"""Experimental Episode Binding R1.

Task-local research adapter: project exact owner-native identities and bounded
observations into a deterministic analytical binding without mutating owner state.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TextIO

from ordivon_composition import canonical_digest

# Same semantic projection is imported when run as a package or as a direct CLI.
if __package__:
    from .experimental_episode_projection_r1 import (
        EpisodeProjectionError,
        project_r5c_record,
        validate_episode,
    )
else:
    from experimental_episode_projection_r1 import (
        EpisodeProjectionError,
        project_r5c_record,
        validate_episode,
    )


def backfill(
    records: Iterable[dict[str, Any]], output: TextIO | None = None
) -> dict[str, Any]:
    source_run_ids: list[str] = []
    episode_ids: list[str] = []
    projection_digests: list[str] = []
    source_record_digests: list[str] = []
    states: Counter[str] = Counter()
    resolutions: Counter[str] = Counter()
    total_events = 0
    total_artifacts = 0
    total_artifact_bytes = 0

    for record in records:
        episode = project_r5c_record(record)
        source_run_ids.append(episode["anchor"]["objectId"])
        episode_ids.append(episode["episodeId"])
        projection_digests.append(episode["projectionDigest"])
        source_record_digests.append(episode["anchor"]["sourceRecordDigest"])
        observation = episode["executionObservation"]
        states[observation["executionState"]] += 1
        resolutions[
            "<null>" if observation["resolution"] is None else observation["resolution"]
        ] += 1
        total_events += episode["evidenceSets"]["events"]["count"]
        total_artifacts += episode["evidenceSets"]["artifacts"]["count"]
        total_artifact_bytes += episode["evidenceSets"]["artifacts"]["totalBytes"]
        if output is not None:
            output.write(
                json.dumps(
                    episode,
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )

    identity_collisions = len(episode_ids) - len(set(episode_ids))
    summary: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-episode-r5c-backfill-summary",
        "sourceRuns": len(source_run_ids),
        "projectedEpisodes": len(episode_ids),
        "episodeIdentityCollisions": identity_collisions,
        "eventRowsBound": total_events,
        "artifactRowsBound": total_artifacts,
        "artifactBytesObserved": total_artifact_bytes,
        "executionStateDistribution": dict(sorted(states.items())),
        "resolutionDistribution": dict(sorted(resolutions.items())),
        "sourceRunIdSetDigest": canonical_digest(sorted(source_run_ids)),
        "episodeIdSetDigest": canonical_digest(sorted(episode_ids)),
        "sourceRecordDigestSetDigest": canonical_digest(sorted(source_record_digests)),
        "projectionDigestSetDigest": canonical_digest(sorted(projection_digests)),
        "standing": (
            "PASS_EXACT_ONE_EPISODE_PER_SOURCE_RUN"
            if identity_collisions == 0 and len(source_run_ids) == len(episode_ids)
            else "FAIL_IDENTITY_OR_CARDINALITY"
        ),
        "claimBoundary": (
            "This summary proves deterministic mechanical projection/cardinality only. "
            "It does not establish domain success, live Runtime equivalence, or a current PostgreSQL data-plane design."
        ),
    }
    summary["summaryDigest"] = canonical_digest(summary)
    return summary


def _records(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise EpisodeProjectionError(
                    f"{path}:{line_number}: source record must be an object"
                )
            yield value


def _cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    project = sub.add_parser("project-r5c")
    project.add_argument("input", type=Path)
    project.add_argument("output", type=Path)
    project.add_argument("summary", type=Path)
    validate = sub.add_parser("validate")
    validate.add_argument("episode", type=Path)
    return parser


def main() -> int:
    args = _cli().parse_args()
    if args.command == "validate":
        value = json.loads(args.episode.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise SystemExit("episode root must be an object")
        validate_episode(value)
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output:
        summary = backfill(_records(args.input), output)
    args.summary.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if summary["standing"] != "PASS_EXACT_ONE_EPISODE_PER_SOURCE_RUN":
        raise SystemExit(summary["standing"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
