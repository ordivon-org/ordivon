"""Development-only real Activity/Workflow/OCI integration, not a release test."""

import asyncio
import concurrent.futures
import hashlib
import json
import os
import shutil
from datetime import timedelta
from pathlib import Path

import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.integration
@pytest.mark.parametrize("versioned", [False, True])
def test_complete_local_development_workflow_and_receipt_replay(tmp_path, monkeypatch, versioned):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    from artifact_temporal_support import ReceiptFencedArtifactExecutor
    from artifact_temporal_workflow import (
        ArtifactActivities,
        ArtifactWorkflow,
        worker_deployment_config,
    )

    cli = os.environ.get("ARTIFACT_TEMPORAL_CLI") or shutil.which("temporal")
    assert cli and Path(cli).is_file(), "qualify a local Temporal CLI; do not implicitly download"
    request = ROOT / "artifact-delivery/examples/presentation-local-development-request-r1.json"
    state_root = tmp_path / "state"
    workflow_id = "artifact-native-local-development"
    task_queue = "artifact-native-local-only"
    activity_input = {
        "request": {
            "path": str(request),
            "sha256": hashlib.sha256(request.read_bytes()).hexdigest(),
        },
        "allowLocalUnsignedDevelopment": True,
    }

    async def run():
        async with await WorkflowEnvironment.start_local(
            dev_server_existing_path=cli,
            dev_server_startup_timeout=timedelta(seconds=30),
            ui=False,
        ) as environment:
            activities = ArtifactActivities(state_root=state_root)
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                async with Worker(
                    environment.client,
                    task_queue=task_queue,
                    workflows=[ArtifactWorkflow],
                    activities=[
                        activities.prepare,
                        activities.build,
                        activities.verify,
                        activities.verify_trust,
                        activities.package,
                    ],
                    activity_executor=pool,
                    deployment_config=worker_deployment_config("artifact-native-test", "candidate") if versioned else None,
                ):
                    if versioned:
                        address = environment.client.service_client.config.target_host
                        assert address.startswith("127.0.0.1:") and not address.endswith(":17233")
                        for _ in range(20):
                            proc = await asyncio.create_subprocess_exec(
                                cli, "--address", address, "worker", "deployment",
                                "set-current-version", "--deployment-name", "artifact-native-test",
                                "--build-id", "candidate", "--yes",
                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                            )
                            try:
                                out, err = await asyncio.wait_for(proc.communicate(), timeout=12)
                            except TimeoutError:
                                proc.kill()
                                await proc.wait()
                                raise
                            if proc.returncode == 0:
                                print("ACTUAL ARTIFACT CURRENT", out.decode().strip())
                                break
                            await asyncio.sleep(0.4)
                        else:
                            raise RuntimeError(err.decode())
                    handle = await environment.client.start_workflow(
                        ArtifactWorkflow.run,
                        activity_input,
                        id=workflow_id,
                        task_queue=task_queue,
                    )
                    result = await asyncio.wait_for(handle.result(), timeout=110)
                    history = await handle.fetch_history()
            assert result["status"] == "PASS"
            assert result["releaseReady"] is False
            assert result["trustStanding"] == "LOCAL_UNSIGNED_DEVELOPMENT"
            assert result["trust"] is None
            roles = 0
            for phase in ("prepare", "build", "verify", "package"):
                for fact in result[phase]["roles"].values():
                    path = Path(fact["path"])
                    assert path.is_file()
                    data = path.read_bytes()
                    assert len(data) == fact["size"]
                    assert hashlib.sha256(data).hexdigest() == fact["sha256"]
                    roles += 1
            verified = json.loads(
                Path(result["verify"]["roles"]["verifyReport"]["path"]).read_bytes()
            )
            assert verified["profileVerificationComplete"] is True
            assert verified["standingCoverage"]["verificationStatus"] == "PASS"
            again = ReceiptFencedArtifactExecutor(state_root).package(
                {
                    "operationId": workflow_id + "/package",
                    "profile": result["prepare"]["metadata"]["profile"],
                    "artifact": result["build"]["roles"]["artifact"],
                    "verifyReport": result["verify"]["roles"]["verifyReport"],
                    "allowLocalUnsignedDevelopment": True,
                }
            )
            assert again["replayed"] is True
            assert again["roles"] == result["package"]["roles"]
            await Replayer(workflows=[ArtifactWorkflow]).replay_workflow(history)
            print(
                "REAL_WORKFLOW_COMPLETE",
                len(history.events),
                roles,
                result["package"]["metadata"]["referrerCount"],
                "REPLAY_PASS",
            )

    asyncio.run(run())


def test_worker_deployment_config_explicit_opt_in(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    from artifact_temporal_workflow import worker_deployment_config
    from temporalio.common import VersioningBehavior

    assert worker_deployment_config(None, None) is None
    config = worker_deployment_config("artifact-test", "exact-build")
    assert config.use_worker_versioning
    assert config.version.deployment_name == "artifact-test"
    assert config.version.build_id == "exact-build"
    assert config.default_versioning_behavior == VersioningBehavior.PINNED
    for name, build in ((None, "id"), ("name", None), ("", "id"), ("name", "")):
        with pytest.raises(ValueError):
            worker_deployment_config(name, build)
