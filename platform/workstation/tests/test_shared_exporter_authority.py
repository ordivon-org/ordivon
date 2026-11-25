"""Source-bound shared physical exporter ownership contract."""
from __future__ import annotations

import itertools
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
NETWORK = ROOT.parent / "network"
UNIT = "prometheus-node-exporter.service"
ENVFILE = "/etc/conf.d/prometheus-node-exporter"
PLAYBOOKS = ("workstation-service-profiles.yml", "observability-metrics.yml")


def workstation_effects():
    """Project actual declared writes, not service names in comments."""
    effects = []
    for name in PLAYBOOKS:
        for play in yaml.safe_load((ROOT / "ansible" / name).read_text()):
            for task in [*play["tasks"], *play.get("handlers", [])]:
                args = task.get("ansible.builtin.systemd_service", {})
                targets = args.get("name")
                if targets == "{{ item }}":
                    loop = task.get("loop", [])
                    if isinstance(loop, str):
                        variable = loop.removeprefix("{{ ").removesuffix(" }}")
                        loop = play["vars"][variable]
                    targets = loop
                if targets == UNIT or isinstance(targets, list) and UNIT in targets:
                    effects.append((name, "lifecycle", args.get("state"), args.get("enabled")))
                copy = task.get("ansible.builtin.copy", {})
                if copy.get("dest") == ENVFILE:
                    effects.append((name, "configuration"))
                command = task.get("ansible.builtin.command", {})
                if UNIT in command.get("argv", []):
                    effects.append((name, "command", tuple(command["argv"])))
    return effects


def test_workstation_has_no_write_authority_over_network_exporter():
    assert workstation_effects() == []


def test_network_preserves_native_authority_and_exact_metric_scope():
    tasks = yaml.safe_load((NETWORK / "observability/Taskfile.yml").read_text())["tasks"]
    source = "\n".join(tasks["observability:systemd:converge"]["cmds"])
    assert "systemctl enable --now " + UNIT in source
    assert "envfile=" + ENVFILE in source
    config = (NETWORK / "config/prometheus/node-exporter.env").read_text()
    assert "--collector.disable-defaults --collector.systemd" in config
    assert "127.0.0.1:29100" in config


def test_no_mislabeled_generic_node_scrape():
    config = yaml.safe_load((ROOT / "observability/prometheus.yml").read_text())
    assert all("127.0.0.1:29100" not in target["targets"]
               for job in config["scrape_configs"] for target in job["static_configs"])


@pytest.mark.parametrize("order", list(itertools.permutations(("workstation", "network"))))
@pytest.mark.parametrize("initial", [(False, False, "legacy"), (True, True, "network")])
def test_source_projected_shared_lifecycle_orders(order, initial):
    # Independent finite projection, not an execution of production playbooks.
    # Network's known-preimage guard is modeled explicitly: active legacy
    # config is outside these two qualified initial states.
    state = initial
    for owner in order:
        if owner == "network":
            state = (True, True, "network")
        else:
            for effect in workstation_effects():
                if effect[1] == "lifecycle":
                    active, enabled, config = state
                    state = (False if effect[2] == "stopped" else active,
                             effect[3] if effect[3] is not None else enabled, config)
                elif effect[1] == "configuration":
                    state = (*state[:2], "legacy")
                # A restart cannot restore the lost configuration or authority.
    assert state == (True, True, "network")
