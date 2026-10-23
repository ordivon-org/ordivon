"""Exact public Gateway Epoch 5 release must never regress during Python migration."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LIVE_TOOLS = [
    "actor.declare",
    "artifact.read",
    "attention.ack",
    "attention.delta",
    "attention.get",
    "attention.reentry",
    "capability.describe",
    "capability.resolve",
    "capability.search",
    "execution.cancel",
    "execution.get",
    "execution.resolve",
    "execution.submit",
    "host.status",
    "message.post",
    "message.relation.add",
    "message.relation.list",
    "message.search",
    "space.create",
    "space.get",
    "space.list",
    "space.participation.list",
    "space.participation.set",
    "space.subject.list",
    "subscription.follow",
    "subscription.list",
    "subscription.unfollow",
    "system.describe",
    "topic.create",
    "topic.cursor.ack",
    "topic.cursor.get",
    "topic.list",
    "topic.resume",
    "work.create",
    "work.get",
    "work.list",
    "work.snapshot.commit",
]


def test_epoch5_is_forward_compatible_with_installed_live_gateway():
    manifest = json.loads((ROOT / "mcp-surface.json").read_text())
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert manifest["surfaceEpoch"] == 5
    assert manifest["packageVersion"] == project["version"] == "0.8.1"
    assert manifest["tools"] == LIVE_TOOLS
    root_python = tomllib.loads((ROOT.parents[1] / "mise.toml").read_text())["tools"]["python"]
    owner_python = (ROOT / ".python-version").read_text().strip()
    assert owner_python == root_python
    assert project["requires-python"] == f"=={owner_python}"


def test_capability_resolve_implementation_comes_from_real_gateway():
    from ordivon_gateway.routes import default_routes
    from ordivon_gateway.service import GatewayService

    assert callable(getattr(GatewayService, "capability_resolve", None))
    routes = default_routes()
    assert "research.publication.closure" in routes
    assert routes["research.publication.closure"].category == "research"
