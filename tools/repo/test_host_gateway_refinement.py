"""SDK Host→Gateway contract refinement has a falsifiable input boundary."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tools.repo.check_host_gateway_refinement as checker


class HostGatewayRefinementTests(unittest.TestCase):
    def compare_synthetic(
        self, source: dict, gateway: dict,
    ) -> dict:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            host_root = root / "host"
            gateway_root = root / "gateway"
            host_root.mkdir()
            gateway_root.mkdir()
            (host_root / "mcp-surface.json").write_text(
                json.dumps({"tools": sorted(source)}), encoding="utf-8",
            )
            (gateway_root / "mcp-surface.json").write_text(
                json.dumps({"tools": sorted(gateway)}), encoding="utf-8",
            )
            with (
                patch.object(checker, "HOST", host_root),
                patch.object(checker, "GATEWAY", gateway_root),
                patch.object(checker, "HOST_OMISSIONS", frozenset()),
            ):
                return checker.compare_source_to_gateway(source, gateway)

    def test_modified_default_is_detected_even_with_generic_output(self) -> None:
        source = {"host.status": {
            "name": "host.status",
            "inputSchema": {
                "type": "object",
                "properties": {"detail": {"type": "string", "default": "summary"}},
            },
            "outputSchema": {"type": "object", "properties": {"healthy": {"type": "boolean"}}},
        }}
        gateway = {"host.status": {
            "name": "host.status",
            "inputSchema": {
                "type": "object",
                "properties": {"detail": {"type": "string", "default": "history"}},
            },
            "outputSchema": {"type": "object", "additionalProperties": True},
        }}
        report = self.compare_synthetic(source, gateway)
        self.assertIn("defaults", report["inputDifferences"]["host.status"])
        self.assertEqual(report["outputSchemaNotPreserved"], ["host.status"])

    def test_missing_required_field_is_not_accepted_as_refinement(self) -> None:
        source = {"work.get": {
            "name": "work.get",
            "inputSchema": {
                "type": "object",
                "properties": {"workRef": {"type": "string"}},
                "required": ["workRef"],
            },
            "outputSchema": {"type": "object", "properties": {"revision": {"type": "integer"}}},
        }}
        gateway = {"work.get": {
            "name": "work.get",
            "inputSchema": {
                "type": "object",
                "properties": {"workRef": {"type": "string"}},
            },
            "outputSchema": source["work.get"]["outputSchema"],
        }}
        report = self.compare_synthetic(source, gateway)
        self.assertIn("required", report["inputDifferences"]["work.get"])
        self.assertEqual(report["outputSchemaNotPreserved"], [])

    def test_new_gateway_host_namespace_without_authoritative_contract_fails(self) -> None:
        source = {"host.status": {"name": "host.status", "inputSchema": {}}}
        gateway = {
            **source,
            "work.unsafe": {"name": "work.unsafe", "inputSchema": {}},
        }
        with self.assertRaisesRegex(
            RuntimeError, "Gateway exposed Host-namespaced tools",
        ):
            self.compare_synthetic(source, gateway)

    def test_extra_or_missing_host_tool_requires_explicit_review(self) -> None:
        source = {"host.status": {"name": "host.status", "inputSchema": {}}}
        with self.assertRaisesRegex(RuntimeError, "Unexpected northbound Gateway Host omissions"):
            self.compare_synthetic(source, {})


if __name__ == "__main__":
    unittest.main()
