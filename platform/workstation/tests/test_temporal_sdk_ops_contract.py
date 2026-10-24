"""Workstation Temporal SDK owner CDC: locked bytes load real smoke consumers.

No server connection, network action, or extra compatibility adapter is required.
"""
from __future__ import annotations

import inspect
import runpy
import tomllib
from importlib.metadata import version
from pathlib import Path

OWNER = Path(__file__).resolve().parents[1]


def test_current_temporal_sdk_imports_every_production_smoke_consumer() -> None:
    lock = tomllib.loads((OWNER / "uv.lock").read_text(encoding="utf-8"))
    pinned = [entry["version"] for entry in lock["package"] if entry["name"] == "temporalio"]
    assert len(pinned) == 1
    assert version("temporalio") == pinned[0]

    consumers = (
        ("temporal_green_smoke.py", "GreenSmokeWorkflow", "run"),
        ("temporal_nexus_smoke.py", "SmokeCallerWorkflow", "run"),
        ("temporal_nexus_smoke.py", "SmokeServiceHandler", "echo"),
        ("temporal-n8n-integration-smoke.py", "N8nIntegrationSmokeWorkflow", "run"),
    )
    loaded: dict[str, dict] = {}
    for source, cls, method in consumers:
        if source not in loaded:
            loaded[source] = runpy.run_path(str(OWNER / "scripts" / source))
        assert inspect.iscoroutinefunction(getattr(loaded[source][cls], method))
