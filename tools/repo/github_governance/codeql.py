from __future__ import annotations

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
    action_sha = "1c5b675653bb5c22dbe9b12b556ec555138e09fd"
    expected = {
        f"github/codeql-action/init@{action_sha}",
        f"github/codeql-action/analyze@{action_sha}",
    }
    actual = {
        step.get("uses")
        for step in steps
        if str(step.get("uses", "")).startswith("github/codeql-action/")
    }
    if actual != expected:
        raise AssertionError("CodeQL init/analyze SHA actions missing or drifting")
    init = next(step for step in steps if step.get("uses", "").endswith("/init@" + action_sha))
    analyze = next(step for step in steps if step.get("uses", "").endswith("/analyze@" + action_sha))
    matrix_value = "$" + "{{ matrix.language }}"
    if init.get("with", {}).get("languages") != matrix_value:
        raise AssertionError("CodeQL does not bind each matrix language")
    if init.get("with", {}).get("build-mode") != "none":
        raise AssertionError("CodeQL Rust extraction cannot be qualified as no-build")
    if analyze.get("with", {}).get("category") != "/language:" + matrix_value:
        raise AssertionError("CodeQL language and result category are not bound")
