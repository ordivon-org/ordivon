import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ServiceProfileTests(unittest.TestCase):
    def test_heavy_observability_profile_is_opt_in_and_groups_expensive_services(self) -> None:
        target = (ROOT / "systemd/ordivon-observability-heavy.target").read_text()
        self.assertIn("Wants=netdata.service loki.service vector.service ordivon-grafana.service", target)
        self.assertNotIn("WantedBy=multi-user.target", target)

        for service in ("netdata", "loki", "vector"):
            dropin = (
                ROOT
                / f"systemd/service-profiles/{service}.service.d/20-ordivon-observability-heavy.conf"
            ).read_text()
            self.assertIn("PartOf=ordivon-observability-heavy.target", dropin)

    def test_grafana_is_profile_owned_not_boot_owned(self) -> None:
        quadlet = (ROOT / "grafana/ordivon-grafana.container").read_text()
        self.assertIn("PartOf=ordivon-observability-heavy.target", quadlet)
        self.assertNotIn("WantedBy=multi-user.target", quadlet)

    def test_profile_desired_state_keeps_heavy_services_cold_and_docker_socket_ready(self) -> None:
        playbook = (ROOT / "ansible/workstation-service-profiles.yml").read_text()
        self.assertIn("ordivon-observability-heavy.target", playbook)
        self.assertIn("docker.socket", playbook)
        self.assertIn("docker.service", playbook)
        self.assertIn("enabled: true", playbook)
        self.assertIn("enabled: false", playbook)
        self.assertIn("state: stopped", playbook)
        self.assertGreaterEqual(playbook.count("not ansible_check_mode"), 7)
        for service in (
            "netdata.service",
            "loki.service",
            "vector.service",
            "ordivon-grafana.service",
            "prometheus.service",
            "prometheus-node-exporter.service",
            "ordivon-gatus.service",
        ):
            self.assertIn(service, playbook)

    def test_slice_playbooks_do_not_reintroduce_boot_autostart(self) -> None:
        metrics = (ROOT / "ansible/observability-metrics.yml").read_text()
        logs = (ROOT / "ansible/observability-logs.yml").read_text()
        grafana = (ROOT / "ansible/observability-grafana.yml").read_text()

        self.assertIn("Keep Netdata cold by default", metrics)
        self.assertIn("Keep node exporter cold by default", metrics)
        self.assertIn("Keep Operations Prometheus cold by default", metrics)
        self.assertNotIn("Enable and start Netdata", metrics)
        self.assertNotIn("Enable and start node exporter", metrics)
        self.assertNotIn("Enable and start Operations Prometheus", metrics)
        self.assertIn("try-restart, prometheus-node-exporter.service", metrics)
        self.assertIn("try-restart, prometheus.service", metrics)
        self.assertIn("Keep Loki cold by default", logs)
        self.assertIn("Keep Vector cold by default", logs)
        self.assertNotIn("Enable and start Loki", logs)
        self.assertNotIn("Enable and start Vector", logs)
        self.assertIn("Keep Grafana cold by default", grafana)
        self.assertNotIn("Ensure Grafana OCI service remains started", grafana)


if __name__ == "__main__":
    unittest.main()
