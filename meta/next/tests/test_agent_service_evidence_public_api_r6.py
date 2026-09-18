from __future__ import annotations

import unittest

import agent_service
from agent_service.evidence import AgentServiceR6, RuntimeArtifactReader, VerificationRecord
from agent_service.runtime_mcp import RuntimeMcpArtifactReader
from agent_service.task_runtime import RuntimeArtifactDescriptor


class AgentServiceEvidencePublicApiR6Tests(unittest.TestCase):
    def test_package_exports_r6_evidence_surface(self) -> None:
        self.assertIs(agent_service.AgentServiceR6, AgentServiceR6)
        self.assertIs(agent_service.RuntimeArtifactReader, RuntimeArtifactReader)
        self.assertIs(agent_service.RuntimeMcpArtifactReader, RuntimeMcpArtifactReader)
        self.assertIs(agent_service.VerificationRecord, VerificationRecord)
        self.assertIs(agent_service.RuntimeArtifactDescriptor, RuntimeArtifactDescriptor)


if __name__ == "__main__":
    unittest.main()
