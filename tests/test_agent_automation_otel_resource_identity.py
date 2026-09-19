from __future__ import annotations

import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OTEL_SERVICE_INSTANCE_NAMESPACE = uuid.UUID("4d63009a-8d0f-11ee-aad7-4c796ed8e320")


class AgentAutomationOtelResourceIdentityTests(unittest.TestCase):
    def _assert_unit_identity(self, unit_name: str, service_name: str) -> None:
        text = (ROOT / "systemd" / unit_name).read_text()
        instance_id = uuid.uuid5(
            OTEL_SERVICE_INSTANCE_NAMESPACE,
            f"systemd:{unit_name}",
        )
        self.assertIn(f"Environment=OTEL_SERVICE_NAME={service_name}", text)
        self.assertIn(
            "Environment=OTEL_RESOURCE_ATTRIBUTES="
            f"service.namespace=ordivon,service.instance.id={instance_id},"
            "deployment.environment.name=production",
            text,
        )

    def test_mcp_uses_otel_service_resource_identity(self) -> None:
        self._assert_unit_identity(
            "ordivon-agent-automation-mcp.service",
            "ordivon-agent-automation-mcp",
        )

    def test_temporal_worker_uses_otel_service_resource_identity(self) -> None:
        self._assert_unit_identity(
            "ordivon-agent-temporal-worker.service",
            "ordivon-agent-temporal-worker",
        )


if __name__ == "__main__":
    unittest.main()
