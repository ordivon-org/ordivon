from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIT = ROOT / "packaging" / "systemd" / "ordivon-runtime.service"


def test_runtime_is_enabled_style_persistent_infrastructure() -> None:
    text = UNIT.read_text(encoding="utf-8")
    assert "WantedBy=multi-user.target" in text
    assert "Restart=always" in text
    assert "RestartSec=3" in text
    assert "PartOf=ordivon-gateway.service" not in text
    assert "BindsTo=ordivon-gateway.service" not in text
