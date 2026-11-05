from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "providers" / "gluetun" / "systemd"


def test_recovery_requires_selected_mode_and_operator_enabled_target():
    service = (ROOT / "network-v2-gluetun-owned-reconcile.service").read_text()
    assert "ConditionPathExists=/etc/network-v2/gluetun/m4-owned-mode.selected" in service
    assert "ExecCondition=/usr/bin/systemctl is-enabled --quiet network-v2-gluetun-owned.target" in service
    assert "ExecStartPre=/usr/local/libexec/network-v2/provider-identity-exclusive gluetun" in service
    assert "ExecStart=/usr/bin/systemctl start network-v2-gluetun-owned.target" in service
    assert "Restart=always" not in service
    assert "network-v2-browserless-wireguard.service" not in service


def test_timer_is_bounded_periodic_not_a_busy_loop():
    timer = (ROOT / "network-v2-gluetun-owned-reconcile.timer").read_text()
    assert "OnBootSec=1min" in timer
    assert "OnCalendar=*-*-* *:0/2:00" in timer
    assert "RandomizedDelaySec=10s" in timer
    assert "Unit=network-v2-gluetun-owned-reconcile.service" in timer
    assert "WantedBy=timers.target" in timer
