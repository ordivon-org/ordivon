"""Native systemd reverse lifecycle contract for active Network consumers.

Use systemd Upholds rather than a custom polling/restart controller.
Physical stop/restart/standalone-start behavior is separately qualified by
a real systemd transient-unit red/green acceptance run on the Linux host.
"""

from configparser import ConfigParser
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("consumer", ("model-provider", "supply-chain", "x-reality"))
def test_active_egress_continuously_upholds_native_enabled_target(consumer: str) -> None:
    units = ROOT / "consumers" / consumer / "systemd"
    service = units / f"network-v2-{consumer}-egress.service"
    target = units / f"network-v2-{consumer}.target"

    def parse(path: Path) -> ConfigParser:
        conf = ConfigParser(interpolation=None)
        conf.read(path)
        return conf

    service_unit = parse(service)
    target_unit = parse(target)
    t = f"network-v2-{consumer}.target"
    s = f"network-v2-{consumer}-egress.service"

    assert service_unit.get("Unit", "PartOf") == t
    assert service_unit.get("Unit", "Upholds") == t
    assert service_unit.get("Service", "Restart") == "on-failure"
    assert target_unit.get("Unit", "Requires") == s
    assert target_unit.get("Unit", "After") == s
    assert target_unit.get("Install", "WantedBy") == "multi-user.target"

    # No independent parallel provider/VPN is permitted by this lifecycle fix.
    assert "ExecStart" not in dict(target_unit["Unit"])
    assert service_unit.get("Service", "ExecStart").startswith("/usr/bin/sing-box run ")
