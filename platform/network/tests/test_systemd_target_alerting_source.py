"""Native node_exporter + Prometheus monitor for Target/service split."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nonprivileged_native_collector_is_scoped_to_six_units() -> None:
    env = (ROOT / "config/prometheus/node-exporter.env").read_text()
    assert "--web.listen-address=127.0.0.1:29100" in env
    assert "--collector.disable-defaults --collector.systemd" in env
    assert "network-v2-(model-provider|supply-chain|x-reality)(-egress)?[.](target|service)" in env
    assert "--collector.textfile" not in env


def test_prometheus_uses_exact_local_exporter_without_external_relay() -> None:
    frag = (ROOT / "config/prometheus/consumers/systemd-targets.yml").read_text()
    assert "job_name: network-node-systemd" in frag
    assert "127.0.0.1:29100" in frag
    assert "scrape_timeout: 5s" in frag


def test_correlated_alert_has_negative_unknown_monitor_control() -> None:
    rules = (ROOT / "config/prometheus/consumer.rules.yml").read_text()
    assert "NetworkConsumerTargetDesynchronized" in rules
    assert "unless on(consumer)" in rules
    assert "NetworkSystemdCollectorUnavailable" in rules
    assert 'absent(up{job="network-node-systemd"})' in rules


def test_native_promtool_alarm_mutants() -> None:
    import shutil
    import subprocess

    promtool = shutil.which("promtool")
    if promtool is None:
        # Generic GitHub Network runners only install the declared mise CI
        # toolchain. The official Prometheus rule engine is a production-native
        # requirement enforced by core:validate and the observer admit gate.
        import pytest

        pytest.skip("promtool unavailable in generic runner; native release gate requires it")

    result = subprocess.run(
        [promtool, "test", "rules", "tests/fixtures/systemd-target-alert.test.yml"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=35,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_source_task_uses_existing_package_and_prometheus_reload() -> None:
    root_task = (ROOT / "Taskfile.yml").read_text()
    assert "promtool test rules tests/fixtures/systemd-target-alert.test.yml" in root_task
    taskfile = (ROOT / "observability/Taskfile.yml").read_text()
    assert "systemctl enable --now prometheus-node-exporter.service" in taskfile
    assert "systemctl kill --kill-who=main --signal=HUP network-v2-prometheus.service" in taskfile
    assert "network-v2-gluetun-owned.service" not in taskfile
    assert "systemctl restart" not in taskfile
