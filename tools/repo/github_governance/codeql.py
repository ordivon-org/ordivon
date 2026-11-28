from __future__ import annotations

import re

import yaml


def validate_monorepo_codeql(source: str) -> None:
    """Ensure all three source languages get a real root-loaded CodeQL workflow."""
    workflow = yaml.safe_load(source)
    if not isinstance(workflow, dict):
        raise AssertionError("CodeQL workflow is not a YAML mapping")  # noqa: TRY004 - governance contract
    triggers = workflow.get("on", workflow.get(True))
    if not isinstance(triggers, dict):
        raise AssertionError("CodeQL is missing event triggers")  # noqa: TRY004 - governance contract
    for event in ("pull_request", "merge_group", "push", "workflow_dispatch", "schedule"):
        if event not in triggers:
            raise AssertionError(f"CodeQL missing active {event} event")
    for event in ("pull_request", "merge_group", "push", "workflow_dispatch"):
        config = triggers[event]
        if config is not None and not isinstance(config, dict):
            raise AssertionError(f"CodeQL {event} event has invalid configuration")
    schedule = triggers["schedule"]
    if (
        not isinstance(schedule, list)
        or not schedule
        or any(
            not isinstance(item, dict)
            or not isinstance(item.get("cron"), str)
            or not item["cron"].strip()
            for item in schedule
        )
    ):
        raise AssertionError("CodeQL schedule event has no active cron")
    if workflow.get("permissions", {}).get("security-events") != "write":
        raise AssertionError("CodeQL cannot upload security results")
    jobs = workflow.get("jobs", {})
    if not isinstance(jobs, dict) or set(jobs) != {"analyze"}:
        raise AssertionError("CodeQL requires exactly one bounded analysis job")
    job = jobs["analyze"]
    matrix = job.get("strategy", {}).get("matrix", {})
    languages = matrix.get("language")
    if not isinstance(languages, list) or set(languages) != {
        "python", "javascript-typescript", "rust"
    } or len(languages) != 3:
        raise AssertionError("CodeQL matrix lost a supported Monorepo language")
    steps = job.get("steps")
    if not isinstance(steps, list) or any(not isinstance(step, dict) for step in steps):
        raise AssertionError("CodeQL missing valid steps")
    # Pin the release family, not a historical release. Init writes state
    # consumed by analyze, so both must use the same immutable commit.
    codeql_steps = [
        step for step in steps
        if str(step.get("uses", "")).startswith("github/codeql-action/")
    ]
    matches = [
        re.fullmatch(r"github/codeql-action/(init|analyze)@([0-9a-f]{40})", step["uses"])
        for step in codeql_steps
    ]
    if (
        len(matches) != 2
        or any(match is None for match in matches)
        or [match.group(1) for match in matches] != ["init", "analyze"]
        or matches[0].group(2) != matches[1].group(2)
    ):
        raise AssertionError("CodeQL init/analyze SHA actions missing or drifting")
    init, analyze = codeql_steps
    matrix_value = "$" + "{{ matrix.language }}"
    if init.get("with", {}).get("languages") != matrix_value:
        raise AssertionError("CodeQL does not bind each matrix language")
    if init.get("with", {}).get("build-mode") != "none":
        raise AssertionError("CodeQL Rust extraction cannot be qualified as no-build")
    if analyze.get("with", {}).get("category") != "/language:" + matrix_value:
        raise AssertionError("CodeQL language and result category are not bound")
