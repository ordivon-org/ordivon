from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT / "src", ROOT / "scripts"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

try:
    import httpx
except ImportError as exc:  # pragma: no cover
    raise unittest.SkipTest(f"Skills MCP runtime dependencies unavailable: {exc}")

from skills_mcp import CatalogProvider, McpSettings, build_app  # noqa: E402

from ordivon_skills.sep2640 import (  # noqa: E402
    AgentSkillsConformanceError,
    parse_skill_uri,
    parse_standard_frontmatter,
    skill_entry,
)


def write_skill(root: Path, name: str, description: str, *, extra: str = "") -> Path:
    package = root / name
    package.mkdir(parents=True, exist_ok=True)
    skill = package / "SKILL.md"
    skill.write_text(
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        f"{extra}"
        "---\n\n"
        f"# {name}\n",
        encoding="utf-8",
    )
    return package


class Sep2640SkillsTests(unittest.TestCase):
    def make_fixture(self):
        td = tempfile.TemporaryDirectory()
        base = Path(td.name)
        user = base / "user"
        alpha = write_skill(user, "alpha", "Use for alpha workflows")
        (alpha / "references").mkdir()
        (alpha / "references" / "guide.md").write_text("guide-v1\n", encoding="utf-8")
        write_skill(
            user,
            "dialect",
            "Dialect-specific metadata must stay off the standard wire",
            extra="homepage: https://example.invalid\n",
        )
        write_skill(
            user,
            "nested-meta",
            "Nested metadata is not the Agent Skills string map",
            extra='metadata:\n  openclaw:\n    requires:\n      bins: ["demo"]\n',
        )
        system = user / ".system"
        write_skill(system, "installer", "Explicit-only installer")
        config = {
            "schemaVersion": 2,
            "ttlMs": 30000,
            "workspaces": {},
            "standardDiscovery": {"user": False, "projects": False},
            "additionalSources": [],
            "compatibilitySources": [
                {
                    "sourceId": "user",
                    "root": str(user),
                    "scope": "user",
                    "trust": "APPROVED",
                    "implicitDenyPrefixes": [".system"],
                }
            ],
        }
        config_file = base / "skills.json"
        config_file.write_text(json.dumps(config), encoding="utf-8")
        token_file = base / "token"
        token_file.write_text("x" * 64, encoding="utf-8")
        token_file.chmod(0o600)
        return td, base, CatalogProvider(config_file), token_file

    def test_agent_skills_standard_gate_is_strict_only_on_standard_surface(self) -> None:
        td, base, provider, _token = self.make_fixture()
        self.addCleanup(td.cleanup)
        catalog = provider.get(force_refresh=True)
        alpha = catalog.by_skill_id("user/alpha", invocation_mode="explicit")
        entry = skill_entry(alpha)
        self.assertEqual(entry.frontmatter["name"], "alpha")
        self.assertEqual(parse_skill_uri(entry.uri), ("user", "alpha", "SKILL.md"))
        self.assertTrue(any(item.uri.endswith("/references/guide.md") for item in entry.resources))

        dialect = catalog.by_skill_id("user/dialect", invocation_mode="explicit")
        with self.assertRaises(AgentSkillsConformanceError):
            skill_entry(dialect)
        nested = catalog.by_skill_id("user/nested-meta", invocation_mode="explicit")
        with self.assertRaises(AgentSkillsConformanceError):
            skill_entry(nested)

        mismatch = base / "mismatch-folder"
        mismatch.mkdir()
        (mismatch / "SKILL.md").write_text(
            "---\nname: another-name\ndescription: mismatch\n---\n# x\n",
            encoding="utf-8",
        )
        with self.assertRaises(AgentSkillsConformanceError):
            parse_standard_frontmatter(mismatch)

    def test_unicode_name_round_trip_and_exact_parent_match_follow_agent_skills_spec(self) -> None:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        base = Path(td.name)
        user = base / "user"
        write_skill(user, "技能-2", "Unicode portable skill")
        config = {
            "schemaVersion": 2,
            "ttlMs": 30000,
            "workspaces": {},
            "standardDiscovery": {"user": False, "projects": False},
            "additionalSources": [],
            "compatibilitySources": [
                {
                    "sourceId": "user",
                    "root": str(user),
                    "scope": "user",
                    "trust": "APPROVED",
                }
            ],
        }
        config_file = base / "skills.json"
        config_file.write_text(json.dumps(config), encoding="utf-8")
        catalog = CatalogProvider(config_file).get(force_refresh=True)
        record = catalog.by_skill_id("user/技能-2", invocation_mode="explicit")
        entry = skill_entry(record)
        self.assertEqual(entry.frontmatter["name"], "技能-2")
        self.assertEqual(
            entry.uri,
            "skill://ordivon/user/%E6%8A%80%E8%83%BD-2/SKILL.md",
        )
        self.assertEqual(parse_skill_uri(entry.uri), ("user", "技能-2", "SKILL.md"))

        decomposed = base / "cafe\u0301"
        decomposed.mkdir()
        (decomposed / "SKILL.md").write_text(
            "---\nname: café\ndescription: Canonically equivalent but not exact\n---\n# Cafe\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(AgentSkillsConformanceError, "parent directory"):
            parse_standard_frontmatter(decomposed)

    def test_standard_frontmatter_preserves_published_optional_fields(self) -> None:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root = Path(td.name) / "rich"
        root.mkdir(parents=True)
        (root / "SKILL.md").write_text(
            "---\n"
            "name: rich\n"
            "description: Rich portable metadata\n"
            "license: Apache-2.0\n"
            "compatibility: Requires git\n"
            "metadata:\n  author: example-org\n  version: '1.0'\n"
            "allowed-tools: Read Bash(git:*)\n"
            "---\n# Rich\n",
            encoding="utf-8",
        )
        parsed = parse_standard_frontmatter(root)
        self.assertEqual(parsed["license"], "Apache-2.0")
        self.assertEqual(parsed["metadata"], {"author": "example-org", "version": "1.0"})
        self.assertEqual(parsed["allowed-tools"], "Read Bash(git:*)")

    def test_http_sep2640_list_get_and_resources_read_are_digest_consistent(self) -> None:
        td, base, provider, token_file = self.make_fixture()
        self.addCleanup(td.cleanup)
        settings = McpSettings(base / "skills.json", token_file=token_file)
        app = build_app(settings, provider, "x" * 64)
        meta = {
            "io.modelcontextprotocol/protocolVersion": "2026-07-28",
            "io.modelcontextprotocol/clientCapabilities": {},
        }

        async def call(client, method: str, params: dict, request_id: int):
            payload = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": {**params, "_meta": meta},
            }
            response = await client.post(
                "/mcp",
                headers={
                    "Authorization": "Bearer " + "x" * 64,
                    "MCP-Protocol-Version": "2026-07-28",
                    "Mcp-Method": method,
                    **({"Mcp-Name": params["uri"]} if method == "resources/read" else {}),
                    "Accept": "application/json",
                },
                json=payload,
            )
            self.assertEqual(response.status_code, 200, response.text)
            row = response.json()
            self.assertNotIn("error", row, row)
            return row["result"]

        async def exercise():
            async with app.app.router.lifespan_context(app.app):
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://127.0.0.1:8895"
                ) as client:
                    listed = await call(client, "skills/list", {}, 1)
                    alpha = next(skill for skill in listed["skills"] if skill["frontmatter"]["name"] == "alpha")
                    got = await call(client, "skills/get", {"uri": alpha["uri"]}, 2)
                    read = await call(client, "resources/read", {"uri": alpha["uri"]}, 3)
                    explicit = await call(
                        client,
                        "skills/get",
                        {"uri": "skill://ordivon/user/installer/SKILL.md"},
                        4,
                    )
                    return listed, alpha, got, read, explicit

        listed, alpha, got, read, explicit = asyncio.run(exercise())
        names = {skill["frontmatter"]["name"] for skill in listed["skills"]}
        self.assertIn("alpha", names)
        self.assertNotIn("dialect", names)
        self.assertNotIn("nested-meta", names)
        self.assertNotIn("installer", names)  # explicit-only, not implicit discovery
        self.assertEqual(listed["resultType"], "complete")
        self.assertEqual(listed["cacheScope"], "private")
        self.assertEqual(got["skill"], alpha)
        self.assertEqual(explicit["skill"]["frontmatter"]["name"], "installer")

        manifest = {item["uri"]: item for item in alpha["resources"]}
        skill_bytes = (base / "user" / "alpha" / "SKILL.md").read_bytes()
        self.assertEqual(
            manifest[alpha["uri"]]["digest"],
            "sha256:" + hashlib.sha256(skill_bytes).hexdigest(),
        )
        self.assertEqual(manifest[alpha["uri"]]["size"], len(skill_bytes))
        [content] = read["contents"]
        self.assertEqual(content["uri"], alpha["uri"])
        self.assertEqual(content["text"].encode("utf-8"), skill_bytes)

    def test_resources_read_rejects_bytes_changed_after_manifest_check(self) -> None:
        from unittest import mock

        import skills_mcp as skills_mcp_module

        td, base, provider, token_file = self.make_fixture()
        self.addCleanup(td.cleanup)
        settings = McpSettings(base / "skills.json", token_file=token_file)
        app = build_app(settings, provider, "x" * 64)
        target = base / "user" / "alpha" / "SKILL.md"
        uri = "skill://ordivon/user/alpha/SKILL.md"
        meta = {
            "io.modelcontextprotocol/protocolVersion": "2026-07-28",
            "io.modelcontextprotocol/clientCapabilities": {},
        }
        original_manifest_contains = skills_mcp_module.manifest_contains
        mutated = False

        def contains_then_mutate(entry, requested_uri: str) -> bool:
            nonlocal mutated
            result = original_manifest_contains(entry, requested_uri)
            if result and not mutated:
                target.write_text(
                    "---\nname: alpha\ndescription: changed after manifest\n---\n\n# alpha\n",
                    encoding="utf-8",
                )
                mutated = True
            return result

        async def exercise():
            async with app.app.router.lifespan_context(app.app):
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://127.0.0.1:8895"
                ) as client:
                    payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "resources/read",
                        "params": {"uri": uri, "_meta": meta},
                    }
                    return await client.post(
                        "/mcp",
                        headers={
                            "Authorization": "Bearer " + "x" * 64,
                            "MCP-Protocol-Version": "2026-07-28",
                            "Mcp-Method": "resources/read",
                            "Mcp-Name": uri,
                            "Accept": "application/json",
                        },
                        json=payload,
                    )

        with mock.patch.object(
            skills_mcp_module,
            "manifest_contains",
            side_effect=contains_then_mutate,
        ):
            response = asyncio.run(exercise())
        self.assertEqual(response.status_code, 200, response.text)
        row = response.json()
        self.assertIn("error", row, row)
        self.assertEqual(row["error"]["code"], -32603)
        self.assertNotIn("changed after manifest", json.dumps(row, sort_keys=True))

    def test_same_name_skills_remain_distinct_standard_uris(self) -> None:
        td, base, _provider, token_file = self.make_fixture()
        self.addCleanup(td.cleanup)
        vendor = base / "vendor"
        write_skill(vendor, "alpha", "Vendor alpha with the same friendly name")
        config_path = base / "skills.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["compatibilitySources"].append(
            {
                "sourceId": "vendor",
                "root": str(vendor),
                "scope": "vendor",
                "trust": "APPROVED",
            }
        )
        config_path.write_text(json.dumps(config), encoding="utf-8")
        provider = CatalogProvider(config_path)
        settings = McpSettings(config_path, token_file=token_file)
        app = build_app(settings, provider, "x" * 64)
        meta = {
            "io.modelcontextprotocol/protocolVersion": "2026-07-28",
            "io.modelcontextprotocol/clientCapabilities": {},
        }
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "skills/list",
            "params": {"_meta": meta},
        }

        async def exercise():
            async with app.app.router.lifespan_context(app.app):
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://127.0.0.1:8895"
                ) as client:
                    return await client.post(
                        "/mcp",
                        headers={
                            "Authorization": "Bearer " + "x" * 64,
                            "MCP-Protocol-Version": "2026-07-28",
                            "Mcp-Method": "skills/list",
                            "Accept": "application/json",
                        },
                        json=body,
                    )

        response = asyncio.run(exercise())
        self.assertEqual(response.status_code, 200, response.text)
        skills = response.json()["result"]["skills"]
        alpha_uris = sorted(
            row["uri"] for row in skills if row["frontmatter"]["name"] == "alpha"
        )
        self.assertEqual(
            alpha_uris,
            [
                "skill://ordivon/user/alpha/SKILL.md",
                "skill://ordivon/vendor/alpha/SKILL.md",
            ],
        )

    def test_server_discover_advertises_standard_skills_extension(self) -> None:
        td, base, provider, token_file = self.make_fixture()
        self.addCleanup(td.cleanup)
        settings = McpSettings(base / "skills.json", token_file=token_file)
        app = build_app(settings, provider, "x" * 64)
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "server/discover",
            "params": {
                "_meta": {
                    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                    "io.modelcontextprotocol/clientInfo": {
                        "name": "sep2640-test",
                        "version": "1",
                    },
                    "io.modelcontextprotocol/clientCapabilities": {},
                },
            },
        }

        async def exercise():
            async with app.app.router.lifespan_context(app.app):
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://127.0.0.1:8895"
                ) as client:
                    return await client.post(
                        "/mcp",
                        headers={
                            "Authorization": "Bearer " + "x" * 64,
                            "MCP-Protocol-Version": "2026-07-28",
                            "Mcp-Method": "server/discover",
                            "Accept": "application/json",
                        },
                        json=body,
                    )

        response = asyncio.run(exercise())
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()["result"]
        self.assertIn("io.modelcontextprotocol/skills", result["capabilities"]["extensions"])
        self.assertEqual(result["capabilities"]["extensions"]["io.modelcontextprotocol/skills"], {})


if __name__ == "__main__":
    unittest.main()
