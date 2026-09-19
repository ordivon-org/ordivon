from __future__ import annotations

import unittest

from mcp_types.version import MODERN_PROTOCOL_VERSIONS

from agent_service.delivery import _route_profiles_from_revision_spec


class McpVersionAuthorityTests(unittest.TestCase):
    def test_every_official_modern_version_is_accepted(self) -> None:
        for version in MODERN_PROTOCOL_VERSIONS:
            with self.subTest(version=version):
                [profile] = _route_profiles_from_revision_spec(
                    "arev:test",
                    {
                        "routes": [
                            {
                                "transport": "mcp",
                                "protocolVersion": version,
                                "url": "https://example.test/mcp",
                            }
                        ]
                    },
                )
                self.assertEqual(profile["protocolVersion"], version)

    def test_syntactically_valid_but_unsupported_date_version_is_rejected(self) -> None:
        self.assertNotIn("2099-12-31", MODERN_PROTOCOL_VERSIONS)
        with self.assertRaisesRegex(
            ValueError, "supported modern MCP protocol version"
        ):
            _route_profiles_from_revision_spec(
                "arev:test",
                {
                    "routes": [
                        {
                            "transport": "mcp",
                            "protocolVersion": "2099-12-31",
                            "url": "https://example.test/mcp",
                        }
                    ]
                },
            )


if __name__ == "__main__":
    unittest.main()
