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

def test_protected_parallel_host_has_independent_identity_native_credential_and_rollback() -> None:
    protected = ROOT / "packaging" / "systemd" / "ordivon-host-v2-protected.service"
    text = protected.read_text(encoding="utf-8")
    legacy = UNIT.read_text(encoding="utf-8")
    assert "User=ordivon-host-v2-protected" in text
    assert "DynamicUser=true" in text
    assert "LoadCredentialEncrypted=host-mcp-bearer:" in text
    assert "ordivon-host-v2-protected-mcp.cred" in text
    assert "ORDIVON_HOST_V2_PORT=19008" in text
    assert "ORDIVON_HOST_V2_HOST=127.0.0.1" in text
    assert "ORDIVON_HOST_V2_OWNER_BEARER_TOKEN_FILE=/run/credentials/" in text
    assert "ORDIVON_HOST_V2_LEGACY_DIRECT_HTTP=" in text
    assert "Restart=on-failure" in text
    assert "WantedBy=multi-user.target" in text
    assert "PartOf=ordivon-host-v2.service" not in text
    assert "BindsTo=ordivon-host-v2.service" not in text
    assert "Requires=ordivon-host-v2.service" not in text
    assert "ORDIVON_HOST_V2_PORT=19008" not in legacy
