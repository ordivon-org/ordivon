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


def test_protected_parallel_host_matches_installed_read_only_identity_boundary() -> None:
    protected = ROOT / "packaging" / "systemd" / "ordivon-host-v2-protected.service"
    text = protected.read_text(encoding="utf-8")
    legacy = UNIT.read_text(encoding="utf-8")
    assert "User=ordivon-host-v2-protected" in text
    assert "DynamicUser=yes" in text
    assert "LoadCredentialEncrypted=host-owner-token:/etc/ordivon/host-v2-protected-owner.cred" in text
    assert "ORDIVON_HOST_V2_OWNER_BEARER_TOKEN_FILE=/run/credentials/ordivon-host-v2-protected.service/host-owner-token" in text
    assert "EnvironmentFile=/etc/ordivon/host-v2.env" in text
    assert "PGOPTIONS=-c default_transaction_read_only=on -c statement_timeout=10000" in text
    assert "ORDIVON_HOST_V2_PG_POOL_MAX_SIZE=2" in text
    assert "ORDIVON_HOST_V2_PORT=19008" in text
    assert "ORDIVON_HOST_V2_HOST=127.0.0.1" in text
    assert "/usr/bin/env -u ORDIVON_HOST_V2_PUBLIC_ORIGIN" in text
    assert "Restart=on-failure" in text
    assert "WantedBy=multi-user.target" in text
    assert "PartOf=ordivon-host-v2.service" not in text
    assert "BindsTo=ordivon-host-v2.service" not in text
    assert "Requires=ordivon-host-v2.service" not in text
    assert "ORDIVON_HOST_V2_PORT=19008" not in legacy
