from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIT = ROOT / "packaging" / "systemd" / "ordivon-host-v2.service"


def test_host_is_persistent_and_db_stop_does_not_propagate() -> None:
    text = UNIT.read_text(encoding="utf-8")
    assert "WantedBy=multi-user.target" in text
    assert "Wants=network-online.target postgresql.service" in text
    assert "After=network-online.target postgresql.service" in text
    assert "Requires=postgresql.service" not in text
    assert "PartOf=postgresql.service" not in text
    assert "BindsTo=postgresql.service" not in text
    assert "Restart=always" in text
    assert "RestartSec=3" in text
