from __future__ import annotations

import unittest

import agent_service
from agent_service.evidence import VerificationRecord
from agent_service.runtime_mcp import RuntimeMcpArtifactReader
from agent_service.task_runtime import RuntimeArtifactDescriptor


class AgentServiceEvidencePublicApiTests(unittest.TestCase):
    def test_package_exports_r6_evidence_surface(self) -> None:
        self.assertFalse(hasattr(agent_service, "AgentServiceR6"))
        self.assertFalse(hasattr(agent_service, "RuntimeArtifactReader"))
        self.assertIs(agent_service.RuntimeMcpArtifactReader, RuntimeMcpArtifactReader)
        self.assertIs(agent_service.VerificationRecord, VerificationRecord)
        self.assertIs(agent_service.RuntimeArtifactDescriptor, RuntimeArtifactDescriptor)


if __name__ == "__main__":
    unittest.main()
