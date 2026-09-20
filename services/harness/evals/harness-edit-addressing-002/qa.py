#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

REPO = Path(__file__).resolve().parents[2]
ROOT = Path(__file__).resolve().parent
TASK_PATH = ROOT / "task.json"
FIXTURE = REPO / "fixtures/harness-edit-addressing-repeated-v1"
ORACLE = ROOT / "oracle/feature_flags.py"
KNOWN_INVALID = ROOT / "known-invalid/both-enabled.py"
HIDDEN_VERIFIER = ROOT / "verifier/test_outcome.py"
VISIBLE_FILES = ("SPEC.md", "feature_flags.py", "test_feature_flags.py")
PROTECTED_FILES = ("SPEC.md", "test_feature_flags.py")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def file_digest(path: Path) -> str:
    return _sha256(path.read_bytes())


def payload_digest(document: dict[str, Any]) -> str:
    payload = dict(document)
    payload.pop("integrity", None)
    return _sha256(_canonical(payload))


def environment_digest() -> str:
    return _sha256(
        _canonical(
            [{"path": name, "digest": file_digest(FIXTURE / name)} for name in VISIBLE_FILES]
        )
    )


def write_task_digests() -> None:
    task = json.loads(TASK_PATH.read_text())
    task["initialState"]["environmentDigest"] = environment_digest()
    task["oracle"]["digest"] = file_digest(ORACLE)
    task["integrity"] = {
        "algorithm": "sha256",
        "canonicalization": "ordivon-canonical-json-v1",
        "payloadDigest": payload_digest(task),
    }
    TASK_PATH.write_text(json.dumps(task, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def validate_task() -> dict[str, Any]:
    task = json.loads(TASK_PATH.read_text())
    if task.get("schemaVersion") != 1 or task.get("kind") != "ordivon.evaluation-task":
        raise ValueError("Task identity differs")
    if task.get("taskId") != "HARNESS-EDIT-ADDRESSING-002" or task.get("taskVersion") != 1:
        raise ValueError("Task version differs")
    if task["initialState"]["fixturePath"] != "fixtures/harness-edit-addressing-repeated-v1":
        raise ValueError("fixture path differs")
    if task["initialState"]["environmentDigest"] != environment_digest():
        raise ValueError("environment digest differs")
    if task["oracle"]["digest"] != file_digest(ORACLE):
        raise ValueError("oracle digest differs")
    if task["integrity"]["payloadDigest"] != payload_digest(task):
        raise ValueError("task payload digest differs")
    if HIDDEN_VERIFIER.is_relative_to(FIXTURE) or ORACLE.is_relative_to(FIXTURE):
        raise ValueError("hidden material entered model-visible fixture")
    return task


def _tree_manifest(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): file_digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> bool:
    return (
        subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        ).returncode
        == 0
    )


def run_candidate(label: str, source: Path | None) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory) / "workspace"
        shutil.copytree(FIXTURE, workspace)
        before = _tree_manifest(workspace)
        protected = {name: file_digest(workspace / name) for name in PROTECTED_FILES}
        if source is not None:
            shutil.copyfile(source, workspace / "feature_flags.py")
        env = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "ORDIVON_EVAL_WORKSPACE": str(workspace),
        }
        visible = _run(
            ["/usr/bin/python3", "-m", "unittest", "-q", "test_feature_flags.py"],
            cwd=workspace,
            env=env,
        )
        hidden = _run(["/usr/bin/python3", str(HIDDEN_VERIFIER)], cwd=workspace, env=env)
        after = _tree_manifest(workspace)
        changed = sorted(
            path for path in set(before) | set(after) if before.get(path) != after.get(path)
        )
        unexpected = [
            path
            for path in changed
            if path != "feature_flags.py" and not path.startswith("artifacts/")
        ]
        if unexpected:
            raise AssertionError(f"{label}: unexpected changed paths: {unexpected}")
        for name, digest in protected.items():
            if file_digest(workspace / name) != digest:
                raise AssertionError(f"{label}: protected file changed: {name}")
        return {
            "label": label,
            "visiblePassed": visible,
            "hiddenPassed": hidden,
            "changedPaths": changed,
        }


def run_qa() -> dict[str, Any]:
    task = validate_task()
    rounds = []
    for index in range(1, task["reproducibility"]["cleanRebuildTrials"] + 1):
        cases = {
            "baseline": run_candidate("baseline", None),
            "oracle": run_candidate("oracle", ORACLE),
            "both-enabled": run_candidate("both-enabled", KNOWN_INVALID),
        }
        expected = {
            "baseline": (False, False),
            "oracle": (True, True),
            "both-enabled": (True, False),
        }
        for label, expectation in expected.items():
            observed = (cases[label]["visiblePassed"], cases[label]["hiddenPassed"])
            if observed != expectation:
                raise AssertionError(
                    f"round {index} {label}: expected {expectation}, observed {observed}"
                )
        rounds.append({"round": index, "cases": cases})
    signatures = [
        {label: (case["visiblePassed"], case["hiddenPassed"]) for label, case in r["cases"].items()}
        for r in rounds
    ]
    if any(signature != signatures[0] for signature in signatures[1:]):
        raise AssertionError("clean rebuild outcomes disagree")
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.evaluation-task-qa-result",
        "taskId": task["taskId"],
        "taskVersion": task["taskVersion"],
        "taskDefinitionDigest": task["integrity"]["payloadDigest"],
        "environmentDigest": task["initialState"]["environmentDigest"],
        "oracleDigest": task["oracle"]["digest"],
        "hiddenVerifierDigest": file_digest(HIDDEN_VERIFIER),
        "cleanRebuildTrials": task["reproducibility"]["cleanRebuildTrials"],
        "requiredAgreement": task["reproducibility"]["requiredAgreement"],
        "agreement": len(signatures),
        "outcomes": signatures[0],
        "hiddenVerifierOutsideWorkspace": not HIDDEN_VERIFIER.is_relative_to(FIXTURE),
        "oracleOutsideWorkspace": not ORACLE.is_relative_to(FIXTURE),
        "passed": True,
    }
    result["integrity"] = {
        "algorithm": "sha256",
        "canonicalization": "ordivon-canonical-json-v1",
        "payloadDigest": payload_digest(result),
    }
    return result


if __name__ == "__main__":
    if "--write-digests" in os.sys.argv:
        write_task_digests()
    result = run_qa()
    rendered = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    (ROOT / "evidence/r2-task-qa.json").write_text(rendered)
    print(rendered, end="")
