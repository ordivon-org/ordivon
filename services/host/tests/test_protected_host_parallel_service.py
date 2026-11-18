"""Protected parallel Host is a separate native service, not a second PG authority."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIT = ROOT / "packaging" / "systemd" / "ordivon-host-v2-protected.service"
LEGACY_UNIT = ROOT / "packaging" / "systemd" / "ordivon-host-v2.service"


def test_protected_service_is_stable_only_at_preflight_qualified_native_identity() -> None:
    source = UNIT.read_text(encoding="utf-8")
    assert "User=ordivon-host-v2-protected" in source
    assert "DynamicUser=yes" in source
    assert "ORDIVON_HOST_V2_PORT=19008" in source
    assert "ORDIVON_HOST_V2_HOST=127.0.0.1" in source
    assert "ORDIVON_HOST_V2_TRANSPORT=streamable-http" in source
    assert "ORDIVON_HOST_V2_OWNER_BEARER_TOKEN_FILE=%d/owner-bearer" in source
    assert "LoadCredential=owner-bearer:/etc/ordivon/host-v2-protected/owner-bearer" in source
    assert "PGOPTIONS=-c default_transaction_read_only=on" in source
    assert "ExecStart=/usr/bin/env -u ORDIVON_HOST_V2_LEGACY_DIRECT_HTTP " in source
    assert "Restart=on-failure" in source
    assert "WantedBy=multi-user.target" in source
    assert "ORDIVON_HOST_V2_LEGACY_DIRECT_HTTP=true" not in source
    assert "0.0.0.0" not in source
    assert "8898" not in source
    assert "19005" not in source
    assert "AuthZEN" not in source  # No invented PDP or Principal-to-Actor authority.


def test_legacy_ingress_remains_independently_serviceable() -> None:
    original = LEGACY_UNIT.read_text(encoding="utf-8")
    parallel = UNIT.read_text(encoding="utf-8")
    assert "/opt/ordivon/host-v2/current" in original
    assert "/opt/ordivon/host-v2/current" in parallel
    assert "postgresql.service" in parallel
    assert "Requires=ordivon-host-v2.service" not in parallel
    assert "PartOf=ordivon-host-v2.service" not in parallel
    assert "BindsTo=ordivon-host-v2.service" not in parallel
