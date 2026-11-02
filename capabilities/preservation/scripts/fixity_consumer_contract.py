"""Pure source-level binding check for the external Artefactual Fixity service.

This module parses supplied systemd Unit/Timer text. It does not read host files,
invoke systemctl, query an external provider, or claim an installed service.
"""

from __future__ import annotations

import configparser
import shlex
from pathlib import Path


def _require(valid: bool, message: str) -> None:
    if not valid:
        raise ValueError(message)


def verify_fixity_consumer_binding(service_source: str, timer_source: str) -> None:
    """Qualify exact Git source Service/Timer seam, not installed systemd state.

    systemd owns scheduling and Artefactual owns scanning. This consumer contract
    only ensures the declared local Fixity profile still routes the timer to
    the intended one-shot provider client with its named environment file.
    Actual STORAGE_SERVICE_URL bytes, deployed units and reachability stay UNKNOWN.
    """

    def unit(source: str, sections: tuple[str, ...]) -> configparser.ConfigParser:
        result = configparser.ConfigParser(interpolation=None, strict=True)
        result.optionxform = str
        try:
            result.read_string(source)
        except configparser.Error as exc:
            raise ValueError(f"invalid Fixity systemd source unit: {exc}") from exc
        for section in sections:
            _require(
                result.has_section(section), f"missing Fixity unit section {section}"
            )
        return result

    service = unit(service_source, ("Unit", "Service", "Install"))
    timer = unit(timer_source, ("Unit", "Timer", "Install"))
    service_cfg = service["Service"]
    timer_cfg = timer["Timer"]
    credential = "/etc/ordivon/fixity-r7.env"
    _require(
        service["Unit"].get("ConditionPathExists") == credential
        and service_cfg.get("EnvironmentFile") == credential,
        "Fixity source consumer must conditionally read the same credential EnvironmentFile",
    )
    _require(
        service_cfg.get("Type") == "oneshot",
        "Fixity scanner must remain a one-shot consumer",
    )
    _require(
        timer_cfg.get("Unit") == "ordivon-preservation-fixity-r7.service",
        "Fixity Timer must schedule its actual named Service, not an unrelated unit",
    )
    _require(
        bool(timer_cfg.get("OnCalendar", "").strip()),
        "Fixity Timer requires a schedule",
    )
    working_dir = service_cfg.get("WorkingDirectory", "")
    try:
        argv = shlex.split(service_cfg.get("ExecStart", ""))
    except ValueError as exc:
        raise ValueError("invalid Fixity scanner ExecStart") from exc
    expected_cli = str(Path(working_dir) / ".venv" / "bin" / "fixity")
    _require(
        working_dir.startswith("/opt/ordivon/external/fixity/")
        and len(argv) >= 3
        and argv[:3] == [expected_cli, "scanall", "--force-local"],
        "Fixity Service must invoke its pinned local provider scanner from WorkingDirectory",
    )
