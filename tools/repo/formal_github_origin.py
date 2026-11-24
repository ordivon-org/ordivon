"""Bounded original GitHub event witness for an already validated Formal receipt.

No raw webhook, credentials, new verification, or proof applicability is stored.
The witness is a producer assertion within the native artifact trust boundary.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

KIND = "ordivon.github-formal-execution-origin-v1"
REPOSITORY = "ordivon-org/ordivon"
WORKFLOW = ".github/workflows/ci.yml"
PRODUCER = "tools/repo/formal_github_origin.py"
MAX_BYTES = 1048576
MAX_EVENT_BYTES = 25 * MAX_BYTES
ARTIFACT_PREFIX = "ordivon-core-formal-"
ORIGIN_QUALIFICATION = "NATIVE_ATTEMPT_PRODUCER_EVENT_AND_GIT"


def oid(value):
    if (not isinstance(value, str)
            or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value) is None
            or not value.strip("0")):
        raise ValueError("origin requires exact nonzero Git object identity")
    return value


def positive(value):
    if type(value) is int and value > 0:
        return value
    if isinstance(value, str) and re.fullmatch(r"[1-9][0-9]*", value):
        return int(value)
    raise ValueError("origin requires positive native identity")


def artifact_identity(name):
    """Return (exact execution cut, attempt or None for legacy name)."""
    if not isinstance(name, str):
        return None
    match = re.fullmatch(
        ARTIFACT_PREFIX + r"([0-9a-f]{40}|[0-9a-f]{64})(?:-attempt-([1-9][0-9]*))?",
        name,
    )
    if match is None:
        return None
    return oid(match.group(1)), int(match.group(2)) if match.group(2) else None


def native_git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_GRAFT_FILE"] = os.devnull
    return subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(repo), *args],
        env=env, text=True, stderr=subprocess.PIPE, timeout=20,
    ).strip()


def native_parents(repo, cut):
    cut = oid(cut)
    if native_git(repo, "rev-parse", "--verify", cut + "^{commit}") != cut:
        raise ValueError("origin execution cut is not exact Git commit")
    # Read the immutable commit header, not shallow traversal or graft overlays.
    headers = native_git(repo, "cat-file", "-p", cut).split("\n\n", 1)[0]
    return [oid(line[7:]) for line in headers.splitlines() if line.startswith("parent ")]


def regular_git_blob(repo, cut, path):
    if native_git(repo, "rev-parse", "--verify", cut + "^{commit}") != cut:
        raise ValueError("origin workflow cut is not exact Git commit")
    entry = native_git(repo, "ls-tree", cut, "--", path)
    match = re.fullmatch(r"100(?:644|755) blob ([0-9a-f]{40}|[0-9a-f]{64})\t" + re.escape(path), entry)
    if match is None:
        raise ValueError("origin source witness is not a native regular Git blob")
    return oid(match.group(1))


def git_witness(repo, cut, workflow_sha):
    cut, workflow_sha = oid(cut), oid(workflow_sha)
    return {
        "sourceParents": native_parents(repo, cut),
        "producerBlob": regular_git_blob(repo, cut, PRODUCER),
        "workflowBlob": regular_git_blob(repo, workflow_sha, WORKFLOW),
    }


def event_coordinates(event_name, event, cut):
    if not isinstance(event, dict):
        raise ValueError("original event must be an object")  # noqa: TRY004
    repository = event.get("repository")
    if repository is not None and (
        not isinstance(repository, dict) or repository.get("full_name") != REPOSITORY
    ):
        raise ValueError("original event repository mismatch")
    if event_name == "pull_request":
        pr = event["pull_request"]
        number = positive(event["number"])
        if "number" in pr and positive(pr["number"]) != number:
            raise ValueError("original PR number mismatch")
        return oid(pr["head"]["sha"]), oid(pr["base"]["sha"]), number
    if event_name == "merge_group":
        if event.get("action") != "checks_requested":
            raise ValueError("unexpected merge group event action")
        group = event["merge_group"]
        return oid(group["head_sha"]), oid(group["base_sha"]), None
    if event_name == "push":
        before = event["before"]
        if isinstance(before, str) and len(before) in (40, 64) and not before.strip("0"):
            before = None
        else:
            before = oid(before)
        return oid(event["after"]), before, None
    if event_name in ("schedule", "workflow_dispatch"):
        return cut, None, None
    raise ValueError("unsupported native Formal event")


def qualify_origin(
    origin, *, source_cut, provider_head, run_id, attempt, event_name, git_inputs,
):
    """Pure finite identity/relationship check; no signature or proof claim."""
    if not isinstance(origin, dict):
        raise ValueError("missing original execution origin")  # noqa: TRY004
    required = {
        "kind", "repository", "workflowRef", "workflowSha", "workflowBlob",
        "producerBlob", "job", "event", "runId", "runAttempt", "sourceCut",
        "sourceParents", "eventHead", "eventBase", "pullRequestNumber", "ref",
    }
    if set(origin) != required:
        raise ValueError("origin field inventory mismatch")
    prefix = REPOSITORY + "/" + WORKFLOW + "@"
    if (
        origin["kind"] != KIND or origin["repository"] != REPOSITORY
        or origin["job"] != "root-preflight" or origin["event"] != event_name
        or type(origin["runId"]) is not int or origin["runId"] != positive(run_id)
        or type(origin["runAttempt"]) is not int or origin["runAttempt"] != positive(attempt)
        or origin["sourceCut"] != oid(source_cut) or origin["eventHead"] != oid(provider_head)
        or not isinstance(origin["workflowRef"], str)
        or not origin["workflowRef"].startswith(prefix)
        or not origin["workflowRef"][len(prefix):]
        or not isinstance(origin["ref"], str) or not origin["ref"].startswith("refs/")
        or any(origin[key] != git_inputs[key] for key in (
            "sourceParents", "producerBlob", "workflowBlob",
        ))
    ):
        raise ValueError("original execution identity mismatch")
    oid(origin["workflowSha"])
    oid(origin["producerBlob"])
    oid(origin["workflowBlob"])
    parents = origin["sourceParents"]
    if not isinstance(parents, list) or any(oid(parent) != parent for parent in parents):
        raise ValueError("original Git parent inventory mismatch")
    base = origin["eventBase"]
    number = origin["pullRequestNumber"]
    if event_name == "pull_request":
        if (type(number) is not int or number <= 0
                or origin["ref"] != f"refs/pull/{number}/merge"
                or parents != [oid(base), provider_head]
                or source_cut == provider_head):
            raise ValueError("original PR event and native Git parents disagree")
    elif event_name in ("merge_group", "push", "schedule", "workflow_dispatch"):
        if number is not None or source_cut != provider_head:
            raise ValueError("original direct event execution cut mismatch")
        if event_name == "merge_group":
            oid(base)
        elif event_name == "push":
            if base is not None:
                oid(base)
        elif base is not None:
            raise ValueError("manual/scheduled event cannot assert a base")
    else:
        raise ValueError("unsupported native Formal event")
    return origin


def capture_origin(repo, env, event):
    cut = oid(env["GITHUB_SHA"])
    if native_git(repo, "rev-parse", "HEAD") != cut:
        raise ValueError("origin checkout differs from GitHub event")
    event_name = env["GITHUB_EVENT_NAME"]
    head, base, number = event_coordinates(event_name, event, cut)
    git_inputs = git_witness(repo, cut, env["GITHUB_WORKFLOW_SHA"])
    origin = {
        "kind": KIND, "repository": env["GITHUB_REPOSITORY"],
        "workflowRef": env["GITHUB_WORKFLOW_REF"],
        "workflowSha": oid(env["GITHUB_WORKFLOW_SHA"]),
        "job": env["GITHUB_JOB"], "event": event_name,
        "runId": positive(env["GITHUB_RUN_ID"]),
        "runAttempt": positive(env["GITHUB_RUN_ATTEMPT"]),
        "sourceCut": cut, "eventHead": head, "eventBase": base,
        "pullRequestNumber": number, "ref": env["GITHUB_REF"], **git_inputs,
    }
    return qualify_origin(
        origin, source_cut=cut, provider_head=head, run_id=origin["runId"],
        attempt=origin["runAttempt"], event_name=event_name, git_inputs=git_inputs,
    )


def read_json(path, limit=MAX_BYTES):
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= limit:
        raise ValueError("origin input must be a bounded regular JSON file")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate origin JSON key")
            result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=unique)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = read_json(args.report)
    if (
        not isinstance(report, dict)
        or report.get("kind") != "source-scoped-native-formal-toolchain-check"
        or report.get("status") != "PASS" or report.get("proofReuseAdmissible") is not False
        or report.get("sourceCut") != os.environ.get("GITHUB_SHA")
        or "githubExecutionOrigin" in report
    ):
        raise ValueError("origin requires existing scoped PASS receipt, never overrides it")
    event = read_json(Path(os.environ["GITHUB_EVENT_PATH"]), MAX_EVENT_BYTES)
    report["githubExecutionOrigin"] = capture_origin(Path.cwd(), os.environ, event)
    data = (json.dumps(report, sort_keys=True, allow_nan=False) + "\n").encode()
    if len(data) > MAX_BYTES:
        raise ValueError("origin receipt exceeds archive content bound")
    # Atomic replacement of our temporary receipt; no second artifact or DB.
    with tempfile.NamedTemporaryFile(dir=args.report.parent, delete=False) as f:
        temporary = Path(f.name)
        try:
            f.write(data)
            f.flush()
            temporary.replace(args.report)
        finally:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
