#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from artifact_temporal_workflow import run_worker


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--address", default="127.0.0.1:17233")
    p.add_argument("--namespace", default="default")
    p.add_argument("--task-queue", default="ordivon-artifact")
    p.add_argument("--state-root", type=Path, required=True)
    p.add_argument("--deployment-name")
    p.add_argument("--build-id")
    a = p.parse_args()
    if (a.deployment_name is None) != (a.build_id is None) or a.deployment_name == "" or a.build_id == "":
        p.error("--deployment-name and --build-id must be supplied together and nonempty")
    asyncio.run(run_worker(
        temporal_address=a.address, namespace=a.namespace, task_queue=a.task_queue,
        state_root=a.state_root, deployment_name=a.deployment_name, build_id=a.build_id,
    ))


if __name__ == "__main__":
    main()
