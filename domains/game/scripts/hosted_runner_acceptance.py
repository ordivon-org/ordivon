"""Consume both original Game previews from one successful main workflow run."""
import argparse
import json
import os
from pathlib import Path
import re
import resource
import subprocess

from hosted_product_acceptance import MAX_ARCHIVE, consume, digest, require

WORKFLOW_PATH = ".github/workflows/game-factory.yml"
PRODUCTS = {"room": "room-encounter", "beacon": "beacon-relay"}
MAX_METADATA = 1024 * 1024


def positive_id(value):
    return type(value) is int and value > 0


def select_artifacts(run, collection, repository, run_id):
    require(isinstance(run, dict) and isinstance(collection, dict), "invalid API metadata")
    require(positive_id(run_id) and positive_id(run.get("id")) and run["id"] == run_id,
            "source run identity differs")
    repo = run.get("repository")
    head = run.get("head_repository")
    require(isinstance(repo, dict) and isinstance(head, dict), "missing repository metadata")
    repo_id = repo.get("id")
    require(positive_id(repo_id) and repo.get("full_name") == repository and
            positive_id(head.get("id")) and head["id"] == repo_id and head.get("full_name") == repository,
            "source repository differs")
    require(run.get("path") == WORKFLOW_PATH and run.get("head_branch") == "main" and
            run.get("event") == "push" and run.get("status") == "completed" and
            run.get("conclusion") == "success", "source workflow not qualified")
    source = run.get("head_sha")
    require(isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source), "invalid source SHA")
    entries = collection.get("artifacts")
    require(isinstance(entries, list) and type(collection.get("total_count")) is int and collection["total_count"] == len(PRODUCTS) and
            len(entries) == len(PRODUCTS), "source artifact inventory differs")
    expected = {f"ordivon-game-{short}-preview-{source}": product
                for short, product in PRODUCTS.items()}
    selected = {}
    ids = set()
    for item in entries:
        require(isinstance(item, dict) and item.get("name") in expected, "unexpected artifact name")
        product = expected[item["name"]]
        require(product not in selected and positive_id(item.get("id")) and item["id"] not in ids,
                "duplicate or invalid artifact identity")
        ids.add(item["id"])
        require(item.get("expired") is False and positive_id(item.get("size_in_bytes")) and
                item["size_in_bytes"] <= MAX_ARCHIVE, "artifact expired or size outside budget")
        sha = item.get("digest")
        require(isinstance(sha, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", sha),
                "missing artifact digest")
        bound = item.get("workflow_run")
        require(isinstance(bound, dict) and all(positive_id(bound.get(k)) for k in
                ("id", "repository_id", "head_repository_id")) and
                bound["id"] == run_id and bound["repository_id"] == repo_id and
                bound["head_repository_id"] == repo_id and bound.get("head_branch") == "main" and
                bound.get("head_sha") == source, "artifact run/source identity differs")
        selected[product] = {"id": item["id"], "sha256": sha.removeprefix("sha256:"),
                             "size": item["size_in_bytes"]}
    require(set(selected) == set(PRODUCTS.values()), "product obligations differ")
    return {"source_run_id": run_id, "source_commit": source, "artifacts": selected}


def read_json(path):
    require(path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= MAX_METADATA,
            "metadata file invalid")
    return json.loads(path.read_text())


def api_json(path):
    p = subprocess.run(["gh", "api", path], capture_output=True, timeout=30, check=True)
    require(len(p.stdout) <= MAX_METADATA, "API metadata exceeds budget")
    return json.loads(p.stdout)


def limit_download():
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_ARCHIVE, MAX_ARCHIVE))


def fetch(stage, repository, run_id):
    stage.mkdir(mode=0o700, exist_ok=False)
    base = f"repos/{repository}/actions"
    run = api_json(f"{base}/runs/{run_id}")
    collection = api_json(f"{base}/runs/{run_id}/artifacts?per_page=100")
    plan = select_artifacts(run, collection, repository, run_id)
    for name, data in (("run.json", run), ("artifacts.json", collection)):
        (stage / name).write_text(json.dumps(data, sort_keys=True))
    for product, item in sorted(plan["artifacts"].items()):
        path = stage / f"{product}.zip"
        with path.open("xb") as out:
            subprocess.run(["gh", "api", f"{base}/artifacts/{item['id']}/zip"],
                           stdout=out, timeout=180, check=True, preexec_fn=limit_download)
        require(path.stat().st_size <= MAX_ARCHIVE and digest(path) == item["sha256"],
                "downloaded artifact digest differs")
    return plan


def qualify(stage, repository, run_id):
    require(not os.environ.get("GH_TOKEN") and not os.environ.get("GITHUB_TOKEN"),
            "API token present in native consumer step")
    require(stage.is_dir() and not stage.is_symlink(), "invalid qualification stage")
    plan = select_artifacts(read_json(stage / "run.json"), read_json(stage / "artifacts.json"),
                            repository, run_id)
    results = {}
    for product, item in sorted(plan["artifacts"].items()):
        result = consume(stage / f"{product}.zip", item["sha256"], plan["source_commit"], product)
        require(result["status"] == "PASS" and result["product"] == product and
                result["outer_sha256"] == item["sha256"] and
                result["source_commit"] == plan["source_commit"], "child receipt differs")
        results[product] = result
    require(set(results) == set(PRODUCTS.values()), "missing product consumer")
    return {"status": "PASS", "scope": "selected_hosted_linux_technical_preview_consumption",
            **plan, "consumer_commit": os.environ.get("GITHUB_SHA", "LOCAL"),
            "consumer_run_id": os.environ.get("GITHUB_RUN_ID", "LOCAL"),
            "consumer_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "LOCAL"),
            "runner_os": os.environ.get("RUNNER_OS", "LOCAL"),
            "runner_image": os.environ.get("ImageVersion", "UNKNOWN"),
            "consumers": results}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("fetch", "qualify"))
    p.add_argument("--repository", required=True)
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--stage", type=Path, required=True)
    args = p.parse_args()
    try:
        require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository),
                "invalid repository")
        require(positive_id(args.run_id) and args.stage.is_absolute() and
                not args.stage.is_symlink(), "invalid run/stage")
        if args.action == "fetch":
            result = fetch(args.stage, args.repository, args.run_id)
        else:
            result = qualify(args.stage, args.repository, args.run_id)
    except (ValueError, AssertionError, OSError, subprocess.SubprocessError) as exc:
        p.exit(1, f"hosted runner qualification rejected: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
