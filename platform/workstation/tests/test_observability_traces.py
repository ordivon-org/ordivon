from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_tempo_is_digest_pinned_private_and_profile_owned() -> None:
    quadlet = (ROOT / "tempo/ordivon-tempo.container").read_text(encoding="utf-8")
    assert (
        "Image=docker.io/grafana/tempo@sha256:"
        "0296560ac66f8a3600d7fb3014a52c189d4d9c3549ad6ff441bf2409855d68d5"
        in quadlet
    )
    assert "Network=host" in quadlet
    assert "User=10001" in quadlet
    assert "Group=10001" in quadlet
    assert "PartOf=ordivon-observability-heavy.target" in quadlet
    assert "Pull=never" in quadlet
    assert "NoNewPrivileges=true" in quadlet
    assert "DropCapability=all" in quadlet
    assert "StopTimeout=60" in quadlet
    assert "TimeoutStopSec=75" in quadlet


def test_tempo_config_is_monolithic_loopback_local_storage() -> None:
    text = (ROOT / "observability/tempo.yaml").read_text(encoding="utf-8")
    assert "http_listen_address: 127.0.0.1" in text
    assert "http_listen_port: 3200" in text
    assert 'endpoint: "127.0.0.1:14317"' in text
    assert 'endpoint: "127.0.0.1:14318"' in text
    assert "backend: local" in text
    assert "path: /var/tempo/wal" in text
    assert "path: /var/tempo/blocks" in text
    assert "reporting_enabled: false" in text
    assert "kafka" not in text.lower()


def test_vector_forwards_otlp_traces_to_tempo_instead_of_blackhole() -> None:
    text = (ROOT / "observability/vector.yaml").read_text(encoding="utf-8")
    assert "traces: true" in text
    assert "otel_traces_tempo:" in text
    assert "inputs: [otel.traces]" in text
    assert "uri: http://127.0.0.1:14318/v1/traces" in text
    assert "codec: otlp" in text
    assert "otel_traces_deferred" not in text
    assert "type: blackhole" not in text


def test_grafana_has_immutable_tempo_datasource() -> None:
    text = (ROOT / "observability/grafana-datasources.yaml").read_text(encoding="utf-8")
    assert "name: Tempo" in text
    assert "uid: operations-tempo" in text
    assert "type: tempo" in text
    assert "url: http://127.0.0.1:3200" in text
    assert "editable: false" in text


def test_trace_playbook_keeps_tempo_cold_by_default_and_has_explicit_acceptance() -> None:
    text = (ROOT / "ansible/observability-traces.yml").read_text(encoding="utf-8")
    assert "tempo_image:" in text
    assert "podman, image, exists" in text
    assert "Keep Tempo cold by default" in text
    assert "Start Tempo for explicit trace acceptance" in text
    assert "http://127.0.0.1:3200/ready" in text
    assert "ordivon_trace_observability_acceptance" in text


def test_heavy_profile_includes_tempo_without_boot_enablement() -> None:
    target = (ROOT / "systemd/ordivon-observability-heavy.target").read_text(encoding="utf-8")
    assert "ordivon-tempo.service" in target
    assert "WantedBy=multi-user.target" not in target
