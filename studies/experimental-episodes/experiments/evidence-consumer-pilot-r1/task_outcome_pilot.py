"""Bounded real Codex task-outcome test with vs without verified Episode summary.

A factual historical corpus summary is NOT a task-level experience memory.
This test measures only its utility for one qualified independent Harness task.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EVAL = ROOT / "services/harness/evals/harness-repository-repair-001"
FIXTURE = ROOT / "services/harness/fixtures/harness-replacement-repository-repair-v1"
TASK = EVAL / "task.json"
HIDDEN = EVAL / "verifier/test_outcome.py"

spec = importlib.util.spec_from_file_location(
    "owner_research_delivery", HERE / "deliver_research.py"
)
assert spec and spec.loader
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


def hash_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root: Path) -> dict[str, str]:
    return {
        f.relative_to(root).as_posix(): hash_file(f)
        for f in sorted(root.rglob("*"))
        if f.is_file()
    }


def qualification() -> dict[str, Any]:
    original = json.loads(TASK.read_bytes())
    assert original["taskId"] == "HARNESS-REPO-REPAIR-001"
    assert HIDDEN.is_file() and HIDDEN.resolve() != (FIXTURE / HIDDEN.name).resolve()
    # The existing authoritative Harness QA, not our experimental grader,
    # checks hidden verifier integrity, oracle behavior and invalid candidates.
    completed = subprocess.run(
        [sys.executable, str(EVAL / "qa.py")],
        capture_output=True,
        text=True,
        check=False,
        timeout=40,
    )
    if completed.returncode:
        raise RuntimeError("native Harness task QA failed")
    reported = json.loads(completed.stdout)
    if (
        not reported["passed"]
        or reported["taskDefinitionDigest"] != original["integrity"]["payloadDigest"]
    ):
        raise ValueError("Harness Task did not qualify")
    return {
        "taskId": original["taskId"],
        "taskDefinitionDigest": original["integrity"]["payloadDigest"],
        "sourceEnvironmentDigest": original["initialState"]["environmentDigest"],
        "hiddenVerifierDigest": hash_file(HIDDEN),
        "nativeHarnessTaskQualification": "PASS",
    }


def prompt(arm: str, evidence: dict[str, Any]) -> str:
    block = "NO ADDITIONAL HISTORICAL DATA PROVIDED."
    if arm == "evidence":
        block = (
            "QUALIFIED HISTORICAL EPISODE RESEARCH INFORMATION (NOT A REPAIR EXAMPLE): "
            + json.dumps(
                {
                    "manifestSha256": evidence["deliveredInformation"][
                        "manifestSha256"
                    ],
                    "counts": evidence["observedBusinessFacts"],
                    "researchDecision": evidence["decision"],
                },
                sort_keys=True,
            )
        )
    return (
        "Complete a software repair inside the current working directory. "
        "Read SPEC.md, allocation.py and test_allocation.py. "
        "Edit only allocation.py and files inside artifacts/. "
        "Implement the SPEC correctly, run the visible unittest, and write "
        "artifacts/completion.json as a JSON object with taskId="
        "HARNESS-REPO-REPAIR-001 and status=completed. "
        "Do not search outside this directory or access the internet. "
        "Do not modify SPEC.md or tests. Hidden evaluation outside this "
        "directory independently checks correctness; do not try to access it. "
        "Return a short completion summary. \n\n" + block
    )


def score(workspace: Path, before: dict[str, str]) -> dict[str, Any]:
    after = inventory(workspace)
    changes = sorted(
        name for name in set(before) | set(after) if before.get(name) != after.get(name)
    )
    forbidden = [
        f for f in changes if f != "allocation.py" and not f.startswith("artifacts/")
    ]
    env = {
        **os.environ,
        "ORDIVON_EVAL_WORKSPACE": str(workspace),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    visible = subprocess.run(
        [sys.executable, "-m", "unittest", "-q", "test_allocation.py"],
        cwd=workspace,
        env=env,
        text=True,
        capture_output=True,
        timeout=35,
        check=False,
    )
    hidden = subprocess.run(
        [sys.executable, str(HIDDEN)],
        cwd=workspace,
        env=env,
        text=True,
        capture_output=True,
        timeout=35,
        check=False,
    )
    artifact_path = workspace / "artifacts/completion.json"
    artifact_ok = False
    if artifact_path.is_file():
        try:
            value = json.loads(artifact_path.read_text())
            artifact_ok = (
                isinstance(value, dict)
                and value.get("taskId") == "HARNESS-REPO-REPAIR-001"
                and value.get("status") == "completed"
            )
        except (ValueError, UnicodeError):
            pass
    return {
        "visiblePassed": visible.returncode == 0,
        "hiddenPassed": hidden.returncode == 0,
        "completionArtifactPresentAndParsable": artifact_ok,
        "protectedSourceUnchanged": not forbidden,
        "changedPaths": changes,
        "modifiedSourceSha256": hash_file(workspace / "allocation.py"),
        "taskSucceeded": (
            visible.returncode == 0
            and hidden.returncode == 0
            and artifact_ok
            and not forbidden
            and "allocation.py" in changes
        ),
    }


def run_agent(arm: str, evidence: dict[str, Any], timeout: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ordivon-data-outcome-codex-") as directory:
        temp = Path(directory)
        workspace = temp / "workspace"
        shutil.copytree(FIXTURE, workspace)
        before = inventory(workspace)
        terminal = temp / "last.txt"
        started = time.monotonic()
        try:
            process = subprocess.run(
                [
                    "codex",
                    "exec",
                    "--skip-git-repo-check",
                    "--ephemeral",
                    "--ignore-user-config",
                    "--ignore-rules",
                    "--sandbox",
                    "workspace-write",
                    "-C",
                    str(workspace),
                    "-o",
                    str(terminal),
                    prompt(arm, evidence),
                ],
                cwd=temp,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "ERROR_TIMEOUT_NO_MODEL_SCORE",
                "elapsedSeconds": round(time.monotonic() - started, 3),
            }
        elapsed = round(time.monotonic() - started, 3)
        if process.returncode:
            return {
                "status": "ERROR_PROVIDER_NO_MODEL_SCORE",
                "elapsedSeconds": elapsed,
                "returnCode": process.returncode,
                "stderrTail": process.stderr[-450:],
            }
        evaluated = score(workspace, before)
        return {
            "status": "MODEL_EXECUTED",
            "elapsedSeconds": elapsed,
            "modelVersionHint": next(
                (
                    line.partition(":")[2].strip()
                    for line in process.stderr.splitlines()
                    if line.startswith("model:")
                ),
                "UNKNOWN",
            ),
            "result": evaluated,
            "agentFinalSha256": hash_file(terminal)
            if terminal.is_file()
            else "NOT_RETAINED",
        }


def build_contract() -> tuple[dict[str, Any], dict[str, Any]]:
    qualification_result = qualification()
    evidence = delivery.deliver()
    assert evidence["status"] == "ACCEPTED"
    contract = {
        "kind": "ordivon.research.data-to-harness-real-task-ab-r1",
        "consumer": "HARNESS-REPO-REPAIR-001",
        "question": "Does a verified historical Episode aggregate improve exact task success on this one qualified coding task?",
        "assignment": ["control", "evidence", "evidence", "control"],
        "task": qualification_result,
        "informationSourceSha256": evidence["deliveredInformation"]["manifestSha256"],
        "studyReceiptSha256": evidence["deliveredInformation"]["systemAnalysisSha256"],
        "budget": {
            "perRunTimeoutSeconds": 110,
            "codexSandbox": "workspace-write",
            "sameTask": True,
        },
        "nonClaims": [
            "Episode aggregates are not actionable individual repair experiences",
            "Single task repeated four times is not independent held-out generalization",
            "Provider model usage/costs unavailable from this record",
            "The task-level outcome oracle remains external and inaccessible to the model",
        ],
    }
    return contract, evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute-model", action="store_true")
    args = parser.parse_args()
    contract, evidence = build_contract()
    record: dict[str, Any] = {"contract": contract, "runs": []}
    if args.execute_model:
        for i, arm in enumerate(contract["assignment"], 1):
            result = run_agent(arm, evidence, 110)
            record["runs"].append({"run": i, "arm": arm, **result})
            print(
                json.dumps(
                    {
                        "run": i,
                        "arm": arm,
                        "status": result["status"],
                        "taskSucceeded": result.get("result", {}).get("taskSucceeded"),
                    }
                ),
                flush=True,
            )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )
    print("RESEARCH_TASK_RECEIPT", args.output, flush=True)


if __name__ == "__main__":
    main()
