#!/usr/bin/env python3
from __future__ import annotations
import argparse
import asyncio
from pathlib import Path
from temporal_agent_automation import run_worker

p = argparse.ArgumentParser()
p.add_argument("--config", type=Path, required=True)
p.add_argument("--address", default="127.0.0.1:17233")
p.add_argument("--namespace", default="default")
p.add_argument("--task-queue", default="ordivon-agent-automation")
a = p.parse_args()
asyncio.run(
    run_worker(
        temporal_address=a.address,
        namespace=a.namespace,
        task_queue=a.task_queue,
        config_path=a.config,
    )
)
