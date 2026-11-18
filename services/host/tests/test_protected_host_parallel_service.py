"""The protected Host source must match the proven independent native systemd contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIT = ROOT / "packaging" / "systemd" / "ordivon-host-v2-protected.service"
LEGACY_UNIT = ROOT / "packaging" / "systemd" / "ordivon-host-v2.service"


def test_protected_service_is_exactly_qualified_parallel_loopback_workload() -> None:
    source = UNIT.read_text(encoding="utf-8")
    assert "User=ordivon-host-v2-protected" in source
    assert "DynamicUser=yes" in source
    assert "ORDIVON_HOST_V2_HOST=127.0.0.1" in source
    assert "ORDIVON_HOST_V2_PORT=19008" in source
    assert "ORDIVON_HOST_V2_TRANSPORT=streamable-http" in source
    assert "ORDIVON_HOST_V2_PG_POOL_MAX_SIZE=2" in source
    assert "PGOPTIONS=-c default_transaction_read_only=on -c statement_timeout=10000" in source
    assert "Restart=on-failure" in source
    assert "WantedBy=multi-user.target" in source
    assert "0.0.0.0:19008" not in source
    assert "8898" not in source and "19005" not in source
    assert "ORDIVON_HOST_V2_LEGACY_DIRECT_HTTP=true" not in source


def test_m2m_secret_is_systemd_encrypted_and_absent_from_source() -> None:
    source = UNIT.read_text(encoding="utf-8")
    cred = "host-owner-token"
    assert (
        "LoadCredentialEncrypted="
        + cred
        + ":/etc/ordivon/host-v2-protected-owner.cred"
    ) in source
    assert (
        "ORDIVON_HOST_V2_OWNER_BEARER_TOKEN_FILE="
        "/run/credentials/ordivon-host-v2-protected.service/host-owner-token"
    ) in source
    assert "LoadCredential=" not in source
    assert "Authorization: Bearer " not in source
    assert "NoNewPrivileges=true" in source
    assert "ProtectSystem=strict" in source
    assert "CapabilityBoundingSet=" in source


def test_legacy_service_stays_independent_and_unchanged() -> None:
    original = LEGACY_UNIT.read_text(encoding="utf-8")
    parallel = UNIT.read_text(encoding="utf-8")
    assert "User=ordivon-host-v2" in original
    assert "User=ordivon-host-v2-protected" in parallel
    assert "/opt/ordivon/host-v2/current" in original
    assert "/opt/ordivon/host-v2/current" in parallel
    assert "Requires=ordivon-host-v2.service" not in parallel
    assert "PartOf=ordivon-host-v2.service" not in parallel
    assert "BindsTo=ordivon-host-v2.service" not in parallel
    assert "-u ORDIVON_HOST_V2_PUBLIC_ORIGIN" in parallel
