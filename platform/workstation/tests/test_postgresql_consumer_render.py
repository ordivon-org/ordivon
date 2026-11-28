"""Render the original deployment template tasks without touching live services."""

from __future__ import annotations

import configparser
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ANSIBLE = ROOT / "ansible"
PLAYBOOK = shutil.which("ansible-playbook")
CASES = {
    "postgresql-backup.yml": {
        "/etc/pgbackrest/pgbackrest.conf": "backup",
        "/etc/systemd/system/postgresql.service.d/20-ordivon-pgdata.conf": "pgdata",
    },
    "n8n.yml": {"{{ n8n_container_env_file }}": "n8n"},
    "temporal-production.yml": {"/etc/temporal/production.yaml": "temporal"},
}


def render(tmp_path: Path, overrides: dict[str, object]) -> dict[str, str]:
    # Reuse the exact module arguments from the real deployment tasks. Replace
    # only delivery destinations and ownership; never run service/DB tasks.
    tasks = []
    expected = set()
    for playbook, destinations in CASES.items():
        play = yaml.safe_load((ANSIBLE / playbook).read_text())[0]
        expected.update(destinations.values())
        for task in play["tasks"]:
            module = task.get("ansible.builtin.template", {})
            name = destinations.get(module.get("dest"))
            if name is None:
                continue
            args = dict(module)
            args["src"] = str((ANSIBLE / args["src"]).resolve())
            args["dest"] = str(tmp_path / name)
            args.pop("owner", None)
            args.pop("group", None)
            tasks.append({"name": name, "ansible.builtin.template": args})
    assert {task["name"] for task in tasks} == expected
    play = tmp_path / "render.json"
    play.write_text(json.dumps([{
        "hosts": "operations_local", "gather_facts": False, "tasks": tasks
    }]))
    result = subprocess.run(
        [PLAYBOOK, "-i", str(ANSIBLE / "inventory.ini"), str(play),
         "--extra-vars", json.dumps(overrides)],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return {name: (tmp_path / name).read_text() for name in expected}


def assert_endpoint(outputs: dict[str, str], port: int, data: str, socket: str) -> None:
    backup = configparser.ConfigParser()
    backup.read_string(outputs["backup"])
    assert backup.getint("ordivon", "pg1-port") == port
    assert backup["ordivon"]["pg1-path"] == data
    assert backup["ordivon"]["pg1-socket-path"] == socket
    assert f"PIDFile={data}/postmaster.pid" in outputs["pgdata"]
    assert f"ExecStart=/usr/bin/postgres -D {data}" in outputs["pgdata"]
    assert f"DB_POSTGRESDB_PORT={port}" in outputs["n8n"].splitlines()
    # Preserve Temporal's separate Go template pass and never materialize a secret.
    assert outputs["temporal"].startswith("# enable-template\n")
    assert outputs["temporal"].count(f'connectAddr: "127.0.0.1:{port}"') == 2
    assert outputs["temporal"].count(
        'password: {{ env "TEMPORAL_POSTGRES_PASSWORD" | quote }}'
    ) == 2


@pytest.mark.skipif(PLAYBOOK is None, reason="native Ansible is not installed")
def test_deployment_consumers_share_inventory_endpoint(tmp_path: Path) -> None:
    inventory = yaml.safe_load(
        (ANSIBLE / "group_vars" / "operations_local.yml").read_text()
    )
    default = tmp_path / "default"
    default.mkdir()
    outputs = render(default, {})
    data = inventory["operations_postgres_data_dir"]
    assert_endpoint(outputs, inventory["operations_postgres_port"], data, data)
    changed = tmp_path / "changed"
    changed.mkdir()
    outputs = render(changed, {
        "operations_postgres_port": 15999,
        "operations_postgres_data_dir": "/var/tmp/qualification-data",
        "operations_postgres_socket": "/var/tmp/qualification-socket",
    })
    assert_endpoint(outputs, 15999, "/var/tmp/qualification-data",
                    "/var/tmp/qualification-socket")
