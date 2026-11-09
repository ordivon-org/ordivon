"""Source-bound Ansible write-frame contract for the Linux Workstation host.

This proves a bounded *source task* property, NOT a physical-effect, credential,
active-WSL-generation or installed-code theorem. An unknown module or task
composition is outside the analyzed frame and requires a new owner contract.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = ROOT / "ansible" / "host-substrate.yml"
_LINUX_SYSTEMD_ROOT = "/etc/systemd/"
_LINUX_DISTRO_WSL = "/etc/wsl.conf"
_ACTIONS = {
    "ansible.builtin.file",
    "ansible.builtin.copy",
    "ansible.builtin.systemd_service",
    "community.general.ini_file",
    "ansible.builtin.debug",
}
_TASK_METADATA = {"name", "loop"}
_SECTIONS = {"boot", "user", "network", "interop"}


def _closed_linux_write_frame(plays: object) -> None:
    """Require every observed task to fit supported Linux-only native effects."""
    assert isinstance(plays, list) and len(plays) == 1
    play = plays[0]
    assert isinstance(play, dict)
    assert play["hosts"] == "operations_local"
    assert play["become"] is True
    assert play["gather_facts"] is False
    variables = play["vars"]
    assert isinstance(variables, dict)
    assert set(variables) == {
        "workstation_wsl_distro_settings",
        "workstation_disabled_system_units",
    }
    distro = variables["workstation_wsl_distro_settings"]
    assert isinstance(distro, list) and distro
    for value in distro:
        assert isinstance(value, dict) and set(value) == {"section", "option", "value"}
        assert value["section"] in _SECTIONS
        assert isinstance(value["option"], str) and value["option"].isidentifier()
        assert isinstance(value["value"], (str, bool))
    assert variables["workstation_disabled_system_units"] == [
        "systemd-homed.service",
        "systemd-homed-activate.service",
    ]

    tasks = play["tasks"]
    assert isinstance(tasks, list) and tasks
    observed: set[str] = set()
    for task in tasks:
        assert isinstance(task, dict)
        assert set(task) <= _ACTIONS | _TASK_METADATA, (
            "unexamined Ansible action or task composition",
            task.get("name"),
            set(task) - (_ACTIONS | _TASK_METADATA),
        )
        actions = set(task) & _ACTIONS
        assert len(actions) == 1, ("missing or multiple action modules", task.get("name"))
        action = actions.pop()
        parameters = task[action]
        assert isinstance(parameters, dict)
        observed.add(action)

        if action in {"ansible.builtin.file", "ansible.builtin.copy"}:
            target = parameters.get("path") if action.endswith(".file") else parameters.get("dest")
            assert isinstance(target, str) and target.startswith(_LINUX_SYSTEMD_ROOT), (
                "unowned filesystem target",
                target,
            )
            assert "{{" not in target and "}}" not in target
        elif action == "ansible.builtin.systemd_service":
            assert task.get("loop") == "{{ workstation_disabled_system_units }}"
            assert parameters["name"] == "{{ item }}"
            assert parameters["state"] == "stopped"
            assert parameters["enabled"] is False
        elif action == "community.general.ini_file":
            assert parameters["path"] == _LINUX_DISTRO_WSL
            assert task.get("loop") == "{{ workstation_wsl_distro_settings }}"
            assert parameters["section"] == "{{ item.section }}"
            assert parameters["option"] == "{{ item.option }}"
            assert parameters["value"] == "{{ item.value }}"
            assert parameters["create"] is False
        elif action == "ansible.builtin.debug":
            assert set(parameters) == {"msg"}
            assert isinstance(parameters["msg"], str)

    assert observed == _ACTIONS, ("existing Linux consumers must remain", _ACTIONS - observed)


def _source() -> list[dict]:
    return yaml.safe_load(PLAYBOOK.read_text(encoding="utf-8"))


def test_linux_host_playbook_has_closed_linux_effect_frame() -> None:
    """Prohibit Windows user-global writes and preserve the actual Linux seam."""
    _closed_linux_write_frame(_source())


@pytest.mark.parametrize(
    "mutation",
    ["windows_ini", "dynamic_copy", "unknown_shell", "import_tasks", "remove_linux_distro"],
)
def test_write_frame_rejects_out_of_scope_effect_or_missing_consumer(mutation: str) -> None:
    """Independent negative controls: the source check must reject bad actions."""
    plays = deepcopy(_source())
    tasks = plays[0]["tasks"]

    if mutation == "windows_ini":
        ini = next(t for t in tasks if "community.general.ini_file" in t)
        ini["community.general.ini_file"]["path"] = "/mnt/c/Users/other/.wslconfig"
    elif mutation == "dynamic_copy":
        copy = next(t for t in tasks if "ansible.builtin.copy" in t)
        copy["ansible.builtin.copy"]["dest"] = "{{ windows_global_path }}"
    elif mutation == "unknown_shell":
        tasks.append({"name": "unknown writer", "ansible.builtin.shell": "echo foo > /mnt/c/x"})
    elif mutation == "import_tasks":
        tasks.append({"name": "hidden indirect effects", "ansible.builtin.import_tasks": "other.yml"})
    elif mutation == "remove_linux_distro":
        tasks[:] = [t for t in tasks if "community.general.ini_file" not in t]

    with pytest.raises((AssertionError, KeyError, TypeError)):
        _closed_linux_write_frame(plays)
